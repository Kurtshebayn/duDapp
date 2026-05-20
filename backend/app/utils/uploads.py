"""
Upload validation helpers — R-7 / AD-5.

Validates Content-Type and enforces file size caps BEFORE any downstream
processing (Cloudinary upload, CSV parsing).

Design constraints:
- Size cap: read max_bytes + 1 bytes. If len > max_bytes → 413.
- MIME check: validate Content-Type header only (no python-magic, no libmagic).
- Returns bytes on success so both call sites (foto/CSV) receive the data once.
"""
import io

from fastapi import HTTPException, UploadFile

# ── Constants (locked in spec / AC-7) ────────────────────────────────────────

MAX_PHOTO_BYTES: int = 5 * 1024 * 1024       # 5 MB
MAX_CSV_BYTES: int = 200 * 1024               # 200 KB

ALLOWED_PHOTO_MIMES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})

ALLOWED_CSV_MIMES: frozenset[str] = frozenset({
    "text/csv",
    "application/vnd.ms-excel",  # AC-7.7: Excel MIME type for CSV uploads
})


# ── Public helper ─────────────────────────────────────────────────────────────

def validate_upload(
    file: UploadFile,
    *,
    max_bytes: int,
    allowed_mimes: frozenset[str],
) -> bytes:
    """Validate Content-Type and size cap for an uploaded file.

    Reads at most max_bytes + 1 bytes from the file. If the content exceeds
    max_bytes, raises 413. If the Content-Type is not in allowed_mimes, raises
    415. On success, returns the file bytes.

    Args:
        file: The FastAPI UploadFile to validate.
        max_bytes: Maximum allowed file size in bytes.
        allowed_mimes: Set of allowed Content-Type values.

    Returns:
        The file content as bytes.

    Raises:
        HTTPException(415): Content-Type not in allowed_mimes.
        HTTPException(413): File size exceeds max_bytes.
    """
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no permitido: {file.content_type}. "
                   f"Tipos permitidos: {', '.join(sorted(allowed_mimes))}",
        )

    # Read one byte past the cap — if we get max_bytes+1 bytes, it's too large.
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        max_kb = max_bytes // 1024
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande (máx {max_kb}KB)",
        )

    return content
