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
    """Validate and return JWT_SECRET, raising ValueError on misconfig."""
    value = os.getenv("JWT_SECRET", "").strip()
    if not value:
        raise ValueError(
            "JWT_SECRET env var is required, must be at least 32 chars, "
            "and must not contain insecure substrings. "
            "Generate with: openssl rand -hex 32"
        )
    if len(value) < 32:
        raise ValueError(
            "JWT_SECRET env var is required, must be at least 32 chars, "
            "and must not contain insecure substrings. "
            "Generate with: openssl rand -hex 32"
        )
    for forbidden in _FORBIDDEN_SUBSTRINGS:
        if forbidden in value:
            raise ValueError(
                "JWT_SECRET env var is required, must be at least 32 chars, "
                "and must not contain insecure substrings. "
                "Generate with: openssl rand -hex 32"
            )
    return value


SECRET_KEY: str = _require_jwt_secret()

_TEST_SENTINEL = "pytest-ci-secret-key-do-not-use-in-prod-32ch!"


def _parse_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS env var, stripping whitespace.

    Raises ValueError if the result is empty and we are NOT in a test environment
    (identified by the JWT_SECRET test sentinel). In test env, falls back to
    localhost for convenience.
    """
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        if os.getenv("JWT_SECRET", "") == _TEST_SENTINEL:
            return ["http://localhost:5173"]
        raise ValueError(
            "CORS_ORIGINS env var is required (comma-separated list of allowed origins). "
            "Example: https://yourapp.vercel.app"
        )
    return origins


CORS_ORIGINS: list[str] = _parse_cors_origins()
