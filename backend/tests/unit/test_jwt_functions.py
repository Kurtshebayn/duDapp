"""
Unit tests for create_access_token / decode_token behavior,
library-agnostic (pass regardless of python-jose or PyJWT).
"""
import pytest

from app.auth.jwt import create_access_token, decode_token


def test_encode_returns_nonempty_string():
    """create_access_token must return a non-empty string."""
    token = create_access_token({"sub": "1"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_round_trip():
    """Encoded then decoded token must preserve sub, email, and name keys."""
    payload = {"sub": "42", "email": "test@example.com", "name": "Tester"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "42"
    assert decoded["email"] == "test@example.com"
    assert decoded["name"] == "Tester"
    assert "exp" in decoded


def test_tampered_token_raises():
    """A token with a tampered signature must raise an exception on decode."""
    token = create_access_token({"sub": "1"})
    # JWT structure: header.payload.signature — tamper a char in the middle of the signature
    header, payload_b64, sig = token.split(".")
    mid = len(sig) // 2
    tampered_sig = sig[:mid] + ("A" if sig[mid] != "A" else "B") + sig[mid + 1 :]
    tampered = header + "." + payload_b64 + "." + tampered_sig
    with pytest.raises(Exception):
        decode_token(tampered)
