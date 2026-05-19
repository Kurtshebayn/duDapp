"""
Tests for JWT_SECRET fail-fast validation in app.config.
Uses subprocess to avoid module-cache issues from pytest's import machinery.
"""
import os
import subprocess
import sys


def _run_import(env_overrides: dict) -> subprocess.CompletedProcess:
    """Run `import app.config` in a subprocess with given env overrides."""
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, "-c", "import app.config"],
        capture_output=True,
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
        env=env,
    )


def test_jwt_secret_missing_raises():
    """Empty JWT_SECRET must cause non-zero exit and mention JWT_SECRET in stderr."""
    result = _run_import({"JWT_SECRET": ""})
    assert result.returncode != 0
    assert b"JWT_SECRET" in result.stderr


def test_jwt_secret_too_short_raises():
    """JWT_SECRET shorter than 32 chars must cause non-zero exit."""
    result = _run_import({"JWT_SECRET": "short"})
    assert result.returncode != 0


def test_jwt_secret_forbidden_substring_raises():
    """JWT_SECRET containing a forbidden substring must cause non-zero exit."""
    # "dev-secret" is in the forbidden list
    result = _run_import({"JWT_SECRET": "dev-secret-key-that-is-long-enough-abc"})
    assert result.returncode != 0


def test_jwt_secret_valid_does_not_raise():
    """A compliant JWT_SECRET must allow the module to import without error."""
    result = _run_import(
        {
            "JWT_SECRET": "pytest-ci-secret-key-do-not-use-in-prod-32ch!",
            "CORS_ORIGINS": "http://localhost",
        }
    )
    assert result.returncode == 0
