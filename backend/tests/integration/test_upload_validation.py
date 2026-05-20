"""
R-7 integration tests — upload size and Content-Type validation at endpoint level.

AC-7.1: POST /jugadores/{id}/foto with 5MB+1 photo → 413
AC-7.2: POST /jugadores/{id}/foto with Content-Type: text/plain → 415
AC-7.3: POST /jugadores/{id}/foto with valid jpeg ≤5MB → NOT 413/415 (proceeds)
AC-7.4: POST /temporadas/import with 200KB+1 CSV → 413
AC-7.5: POST /temporadas/import with Content-Type: application/pdf → 415
AC-7.6: POST /temporadas/import with valid text/csv → NOT 413/415
"""
import io
from datetime import date

import bcrypt
import pytest

from app.models.jugador import Jugador
from app.utils.uploads import MAX_CSV_BYTES, MAX_PHOTO_BYTES


@pytest.fixture
def auth_headers(client, admin_user):
    r = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def jugador_en_db(db):
    j = Jugador(nombre="Test Player")
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


# ── Photo upload validation ────────────────────────────────────────────────────

def test_photo_over_5mb_returns_413(client, auth_headers, jugador_en_db):
    """AC-7.1: 5MB+1 byte photo → 413."""
    oversized = b"x" * (MAX_PHOTO_BYTES + 1)
    response = client.post(
        f"/jugadores/{jugador_en_db.id}/foto",
        files={"foto": ("big.jpg", io.BytesIO(oversized), "image/jpeg")},
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_photo_wrong_content_type_returns_415(client, auth_headers, jugador_en_db):
    """AC-7.2: text/plain photo → 415."""
    response = client.post(
        f"/jugadores/{jugador_en_db.id}/foto",
        files={"foto": ("file.txt", io.BytesIO(b"not an image"), "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 415


def test_valid_photo_proceeds_past_validation(client, auth_headers, jugador_en_db, monkeypatch):
    """AC-7.3: Valid jpeg ≤5MB → NOT 413/415 (proceeds to Cloudinary, which we mock)."""
    import cloudinary.uploader

    # Mock the Cloudinary upload to avoid real API calls
    def mock_upload(*args, **kwargs):
        return {"secure_url": "https://res.cloudinary.com/test/image/upload/jugador_1.jpg"}

    monkeypatch.setattr(cloudinary.uploader, "upload", mock_upload)

    content = b"fake jpeg bytes"
    response = client.post(
        f"/jugadores/{jugador_en_db.id}/foto",
        files={"foto": ("photo.jpg", io.BytesIO(content), "image/jpeg")},
        headers=auth_headers,
    )
    # Should NOT be 413 or 415 — may be 503 if Cloudinary env vars not set, but never size/MIME errors
    assert response.status_code not in (413, 415)


# ── CSV import validation ──────────────────────────────────────────────────────

def test_csv_over_200kb_returns_413(client, auth_headers):
    """AC-7.4: 200KB+1 CSV → 413."""
    oversized = b"x" * (MAX_CSV_BYTES + 1)
    response = client.post(
        "/temporadas/import",
        data={"nombre": "Test", "fecha_inicio": "2026-01-01"},
        files={"archivo": ("big.csv", io.BytesIO(oversized), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_csv_wrong_content_type_returns_415(client, auth_headers):
    """AC-7.5: application/pdf → 415."""
    response = client.post(
        "/temporadas/import",
        data={"nombre": "Test", "fecha_inicio": "2026-01-01"},
        files={"archivo": ("file.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 415


def test_valid_csv_proceeds_past_validation(client, auth_headers):
    """AC-7.6: Valid CSV (text/csv) proceeds past validation (may fail parsing — that's OK)."""
    # A minimal valid CSV for the import endpoint
    csv_content = b"nombre;jornada1\nAna;1\nBruno;2\n"
    response = client.post(
        "/temporadas/import",
        data={"nombre": "TestSeason", "fecha_inicio": "2026-01-01"},
        files={"archivo": ("data.csv", io.BytesIO(csv_content), "text/csv")},
        headers=auth_headers,
    )
    # Should NOT be 413 or 415 — the import may fail for other reasons (format issues etc.)
    assert response.status_code not in (413, 415)
