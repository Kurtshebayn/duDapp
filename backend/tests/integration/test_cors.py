"""
R-6: CORS hardening tests.

AC-6.1: CORS_ORIGINS with spaces after commas → origins stripped correctly.
AC-6.2: CORS_ORIGINS="" → ValueError at app startup (tested via config unit test).
AC-6.3: OPTIONS preflight from valid origin → Access-Control-Allow-Methods does NOT
        contain "*" and does NOT contain "PATCH" or "HEAD".
AC-6.4: OPTIONS preflight from valid origin → Access-Control-Allow-Headers does NOT
        contain "*".
"""
import pytest


def test_options_preflight_allow_methods_is_scoped(client):
    """AC-6.3: allow_methods must not be wildcard and must not include PATCH or HEAD."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    # CORS preflight returns 200 for valid origins
    assert response.status_code == 200
    methods_header = response.headers.get("access-control-allow-methods", "")
    assert "*" not in methods_header, "allow_methods must not be wildcard"
    assert "PATCH" not in methods_header.upper(), "PATCH must not be in allow_methods"
    assert "HEAD" not in methods_header.upper(), "HEAD must not be in allow_methods"


def test_options_preflight_allow_headers_is_scoped(client):
    """AC-6.4: allow_headers must not be wildcard."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    headers_header = response.headers.get("access-control-allow-headers", "")
    assert "*" not in headers_header, "allow_headers must not be wildcard"
