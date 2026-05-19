"""
Tests for R-5: Login timing flatten.

Verifies that the login endpoint runs bcrypt regardless of whether the user
exists, so that response time for nonexistent-user vs wrong-password is
indistinguishable within a 50ms tolerance (AC-5.1, AC-5.2).
"""
import time

import bcrypt
import pytest
from unittest.mock import patch, MagicMock


def test_dummy_hash_constant_exists():
    """AC-5.1 (structural): _DUMMY_HASH is a module-level bcrypt hash."""
    from app.routers.auth import _DUMMY_HASH

    assert isinstance(_DUMMY_HASH, str), "_DUMMY_HASH must be a str"
    # Verify it's a valid bcrypt hash by checking it with a dummy check
    assert bcrypt.checkpw(b"dummy-password-for-timing-flatten", _DUMMY_HASH.encode()), (
        "_DUMMY_HASH must be the bcrypt hash of b'dummy-password-for-timing-flatten'"
    )


def test_verify_password_is_called_for_nonexistent_user(client):
    """AC-5.1: bcrypt is invoked even when user does not exist in DB.

    We patch verify_password to intercept the call and confirm it was called
    with the _DUMMY_HASH as the hashed argument.
    """
    from app.routers import auth as auth_module

    calls = []
    original = auth_module.verify_password

    def spy(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    with patch.object(auth_module, "verify_password", side_effect=spy):
        resp = client.post(
            "/auth/login",
            json={"identificador": "definitely_not_a_user@test.com", "password": "whatever"},
        )

    assert resp.status_code == 401
    assert len(calls) == 1, "verify_password must be called exactly once even for nonexistent user"
    # The hashed argument must be _DUMMY_HASH (not None or empty)
    hashed_arg = calls[0][1]
    assert hashed_arg == auth_module._DUMMY_HASH, (
        "verify_password must be called with _DUMMY_HASH when user does not exist"
    )


def test_login_timing_parity(admin_user, client):
    """AC-5.2: mean timing difference between nonexistent-user and wrong-password
    login attempts is less than 50ms.

    Uses 5 samples per group. bcrypt dominates latency so the difference
    should be negligible if both paths run bcrypt exactly once.
    """
    SAMPLES = 5
    TOLERANCE_MS = 50  # per spec: < 50ms mean difference

    wrong_pass_times = []
    no_user_times = []

    # Warm up bcrypt (module-level _DUMMY_HASH already computed, but JIT and caches
    # can affect the first call — do one throwaway call)
    client.post("/auth/login", json={"identificador": admin_user.email, "password": "x"})
    client.post("/auth/login", json={"identificador": "warmup_no_user@x.com", "password": "x"})

    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        client.post("/auth/login", json={"identificador": admin_user.email, "password": "wrong"})
        wrong_pass_times.append((time.perf_counter() - t0) * 1000)

    for _ in range(SAMPLES):
        t0 = time.perf_counter()
        client.post("/auth/login", json={"identificador": "nouser_timing@test.com", "password": "wrong"})
        no_user_times.append((time.perf_counter() - t0) * 1000)

    mean_wrong = sum(wrong_pass_times) / SAMPLES
    mean_no_user = sum(no_user_times) / SAMPLES
    diff = abs(mean_wrong - mean_no_user)

    assert diff < TOLERANCE_MS, (
        f"Mean timing difference {diff:.1f}ms exceeds {TOLERANCE_MS}ms tolerance. "
        f"wrong-password mean={mean_wrong:.1f}ms, no-user mean={mean_no_user:.1f}ms. "
        "Ensure bcrypt runs on both code paths."
    )
