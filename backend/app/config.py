import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dudapp.db")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día

_FORBIDDEN_SUBSTRINGS = [
    "dev-secret",
    "changeme",
    "change-in-production",
    "example",
    "placeholder",
]


def _require_jwt_secret() -> str:
    """Validate and return JWT_SECRET, raising RuntimeError on misconfig."""
    value = os.getenv("JWT_SECRET", "").strip()
    if not value:
        raise RuntimeError(
            "JWT_SECRET env var is required, must be at least 32 chars, "
            "and must not contain insecure substrings. "
            "Generate with: openssl rand -hex 32"
        )
    if len(value) < 32:
        raise RuntimeError(
            "JWT_SECRET env var is required, must be at least 32 chars, "
            "and must not contain insecure substrings. "
            "Generate with: openssl rand -hex 32"
        )
    for forbidden in _FORBIDDEN_SUBSTRINGS:
        if forbidden in value:
            raise RuntimeError(
                "JWT_SECRET env var is required, must be at least 32 chars, "
                "and must not contain insecure substrings. "
                "Generate with: openssl rand -hex 32"
            )
    return value


SECRET_KEY: str = _require_jwt_secret()

CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
