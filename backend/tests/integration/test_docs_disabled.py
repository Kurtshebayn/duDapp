"""
R-8: /docs, /redoc, and /openapi.json MUST return 404 unconditionally.

AC-8.1: GET /docs → 404
AC-8.2: GET /redoc → 404
AC-8.3: GET /openapi.json → 404
"""


def test_docs_returns_404(client):
    response = client.get("/docs")
    assert response.status_code == 404


def test_redoc_returns_404(client):
    response = client.get("/redoc")
    assert response.status_code == 404


def test_openapi_json_returns_404(client):
    response = client.get("/openapi.json")
    assert response.status_code == 404
