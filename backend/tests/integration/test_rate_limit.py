"""
Integration test for R-3: rate limiting on /auth/login.
Requires the enable_rate_limit fixture to activate the limiter.
All other tests run with limiter disabled (autouse fixture in conftest.py).
"""
import pytest


def test_sixth_login_request_returns_429(client, enable_rate_limit):
    """AC-3.1: 6th request from same IP in 15-minute window returns 429."""
    payload = {"identificador": "nonexistent@test.com", "password": "wrongpassword"}

    responses = []
    for _ in range(6):
        resp = client.post("/auth/login", json=payload)
        responses.append(resp.status_code)

    # First 5 should not be 429 (they may be 401 for bad credentials)
    for i, code in enumerate(responses[:5]):
        assert code != 429, f"Request {i + 1} should not be 429, got {code}"

    # 6th must be 429
    assert responses[5] == 429, f"6th request should be 429, got {responses[5]}"


def test_rate_limit_key_function_uses_get_ipaddr():
    """AC-3.2: verify the limiter uses get_ipaddr (X-Forwarded-For-aware key).

    NOTE: TestClient normalizes all connections to 'testclient' host, and slowapi
    0.1.9's get_ipaddr reads X_FORWARDED_FOR in ASGI underscore format which
    doesn't match the lowercase headers sent by TestClient. Per-IP isolation
    cannot be end-to-end tested via TestClient. Instead we assert that the
    Limiter is configured with get_ipaddr as the key function.
    """
    from slowapi.util import get_ipaddr
    from app.security.rate_limit import limiter

    assert limiter._key_func is get_ipaddr, (
        "Limiter must use get_ipaddr (X-Forwarded-For-aware) not get_remote_address. "
        "Using get_remote_address under Render's proxy would coalesce all clients into one IP."
    )


def test_limiter_disabled_by_default_allows_many_requests(client):
    """Verify that with limiter disabled (default for all non-rate-limit tests),
    sending more than 5 login attempts does not trigger 429."""
    payload = {"identificador": "nonexistent@test.com", "password": "wrongpassword"}

    for i in range(10):
        resp = client.post("/auth/login", json=payload)
        assert resp.status_code != 429, (
            f"Request {i + 1} should not be 429 when limiter is disabled, got {resp.status_code}"
        )
