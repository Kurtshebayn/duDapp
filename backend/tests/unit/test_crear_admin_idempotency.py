"""
Tests for R-4: _setup_admin retirement and crear_admin.py idempotency (AC-4.x).

Uses subprocess-based tests for the script paths (same pattern as
test_config_validation.py) because the script imports app modules and
creates DB sessions that would conflict with the test database.
"""
import os
import subprocess
import sys

import bcrypt
import pytest


# ── AC-4.1: _setup_admin does not exist in main.py ───────────────────────────

def test_setup_admin_not_in_main():
    """AC-4.1: _setup_admin must not exist in app/main.py after retirement."""
    import ast
    import pathlib

    main_path = pathlib.Path(__file__).parent.parent.parent / "app" / "main.py"
    source = main_path.read_text(encoding="utf-8")

    assert "_setup_admin" not in source, (
        "_setup_admin must be removed from app/main.py (R-4 / AD-7). "
        "The function should only exist in scripts/crear_admin.py."
    )


def test_admin_password_env_not_needed_on_import():
    """AC-4.2: app/main.py imports cleanly without ADMIN_PASSWORD env var."""
    env = {
        **os.environ,
        "JWT_SECRET": "pytest-ci-secret-key-do-not-use-in-prod-32ch!",
        "CORS_ORIGINS": "http://localhost:5173",
    }
    env.pop("ADMIN_PASSWORD", None)

    result = subprocess.run(
        [sys.executable, "-c", "from app.main import app; print('OK')"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    )
    assert result.returncode == 0, (
        f"app/main.py must import cleanly without ADMIN_PASSWORD. "
        f"stderr: {result.stderr}"
    )
    assert "OK" in result.stdout


# ── AC-4.3 / AC-4.4: crear_admin.py idempotency via DB fixture ───────────────

def test_crear_admin_exits_1_when_no_password_and_no_admin(db):
    """AC-4.3 (negative path): exit 1 when ADMIN_PASSWORD unset and no admin exists."""
    # DB is empty (no admin) and ADMIN_PASSWORD is not set
    env = {
        **os.environ,
        "JWT_SECRET": "pytest-ci-secret-key-do-not-use-in-prod-32ch!",
        "DATABASE_URL": "sqlite:///./test.db",
    }
    env.pop("ADMIN_PASSWORD", None)

    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "crear_admin.py",
    )
    result = subprocess.run(
        [sys.executable, script_path],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    )
    assert result.returncode == 1, (
        f"crear_admin.py must exit 1 when no ADMIN_PASSWORD and no admin exists. "
        f"Got exit {result.returncode}. stderr: {result.stderr}, stdout: {result.stdout}"
    )


def test_crear_admin_exits_0_when_no_password_but_admin_exists(db):
    """AC-4.4: exit 0 (graceful no-op) when ADMIN_PASSWORD unset but admin already exists."""
    from app.models.usuario import Usuario

    # Seed an admin in the test DB
    admin = Usuario(
        email="admin@dudo.com",
        nombre="Admin",
        password_hash=bcrypt.hashpw(b"original", bcrypt.gensalt()).decode(),
    )
    db.add(admin)
    db.commit()

    env = {
        **os.environ,
        "JWT_SECRET": "pytest-ci-secret-key-do-not-use-in-prod-32ch!",
        "DATABASE_URL": "sqlite:///./test.db",
    }
    env.pop("ADMIN_PASSWORD", None)

    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "crear_admin.py",
    )
    result = subprocess.run(
        [sys.executable, script_path],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    )
    assert result.returncode == 0, (
        f"crear_admin.py must exit 0 when no ADMIN_PASSWORD but admin already exists. "
        f"Got exit {result.returncode}. stderr: {result.stderr}, stdout: {result.stdout}"
    )
    assert "OK" in result.stdout, (
        f"crear_admin.py must print an OK message when skipping (admin exists). stdout: {result.stdout}"
    )
