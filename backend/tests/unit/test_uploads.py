"""
R-7 unit tests — upload validation helper.

AC-7.1: Photo 5MB+1 → 413
AC-7.2: Photo with Content-Type: text/plain → 415
AC-7.3: Valid photo (jpeg, ≤5MB) → returns bytes
AC-7.4: CSV 200KB+1 → 413
AC-7.5: Content-Type: application/pdf → 415
AC-7.6: Valid CSV (text/csv, ≤200KB) → returns bytes
AC-7.7: Content-Type: application/vnd.ms-excel → NOT 415 (allowed for CSV)
"""
import io

import pytest
from fastapi import HTTPException, UploadFile

from app.utils.uploads import (
    ALLOWED_CSV_MIMES,
    ALLOWED_PHOTO_MIMES,
    MAX_CSV_BYTES,
    MAX_PHOTO_BYTES,
    validate_upload,
)


def _make_upload(content: bytes, content_type: str) -> UploadFile:
    """Create a minimal UploadFile from bytes for testing."""
    return UploadFile(
        filename="test",
        file=io.BytesIO(content),
        headers={"content-type": content_type},
    )


# ── Photo validation ───────────────────────────────────────────────────────────

def test_photo_over_size_limit_raises_413():
    """AC-7.1: 5MB+1 byte → 413."""
    oversized = b"x" * (MAX_PHOTO_BYTES + 1)
    f = _make_upload(oversized, "image/jpeg")
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(f, max_bytes=MAX_PHOTO_BYTES, allowed_mimes=ALLOWED_PHOTO_MIMES)
    assert exc_info.value.status_code == 413


def test_photo_wrong_content_type_raises_415():
    """AC-7.2: Content-Type: text/plain → 415."""
    f = _make_upload(b"fake image data", "text/plain")
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(f, max_bytes=MAX_PHOTO_BYTES, allowed_mimes=ALLOWED_PHOTO_MIMES)
    assert exc_info.value.status_code == 415


def test_valid_jpeg_photo_returns_bytes():
    """AC-7.3: Valid jpeg ≤5MB → returns bytes."""
    content = b"fake jpeg content"
    f = _make_upload(content, "image/jpeg")
    result = validate_upload(f, max_bytes=MAX_PHOTO_BYTES, allowed_mimes=ALLOWED_PHOTO_MIMES)
    assert result == content


def test_valid_png_photo_returns_bytes():
    """AC-7.3: Valid png → returns bytes."""
    content = b"fake png content"
    f = _make_upload(content, "image/png")
    result = validate_upload(f, max_bytes=MAX_PHOTO_BYTES, allowed_mimes=ALLOWED_PHOTO_MIMES)
    assert result == content


def test_valid_webp_photo_returns_bytes():
    """AC-7.3: Valid webp → returns bytes."""
    content = b"fake webp content"
    f = _make_upload(content, "image/webp")
    result = validate_upload(f, max_bytes=MAX_PHOTO_BYTES, allowed_mimes=ALLOWED_PHOTO_MIMES)
    assert result == content


# ── CSV validation ────────────────────────────────────────────────────────────

def test_csv_over_size_limit_raises_413():
    """AC-7.4: 200KB+1 byte → 413."""
    oversized = b"x" * (MAX_CSV_BYTES + 1)
    f = _make_upload(oversized, "text/csv")
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(f, max_bytes=MAX_CSV_BYTES, allowed_mimes=ALLOWED_CSV_MIMES)
    assert exc_info.value.status_code == 413


def test_csv_wrong_content_type_raises_415():
    """AC-7.5: Content-Type: application/pdf → 415."""
    f = _make_upload(b"fake pdf", "application/pdf")
    with pytest.raises(HTTPException) as exc_info:
        validate_upload(f, max_bytes=MAX_CSV_BYTES, allowed_mimes=ALLOWED_CSV_MIMES)
    assert exc_info.value.status_code == 415


def test_valid_csv_returns_bytes():
    """AC-7.6: Valid CSV (text/csv) → returns bytes."""
    content = b"nombre;jornada\nAna;1\n"
    f = _make_upload(content, "text/csv")
    result = validate_upload(f, max_bytes=MAX_CSV_BYTES, allowed_mimes=ALLOWED_CSV_MIMES)
    assert result == content


def test_vnd_ms_excel_content_type_allowed_for_csv():
    """AC-7.7: application/vnd.ms-excel is allowlisted for CSV."""
    content = b"nombre;jornada\nAna;1\n"
    f = _make_upload(content, "application/vnd.ms-excel")
    result = validate_upload(f, max_bytes=MAX_CSV_BYTES, allowed_mimes=ALLOWED_CSV_MIMES)
    assert result == content
