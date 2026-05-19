"""
R-10 unit tests — Cloudinary config moved to lifespan startup.

AC-10.1: cloudinary.config() is NOT called inside jugadores.py at module level
         or inside any request handler.
AC-10.2: When Cloudinary env vars are set, cloudinary.config is called during
         app startup (lifespan).
AC-10.3: Given Cloudinary is configured at startup, the upload handler uses the
         already-configured SDK (no per-request reconfiguration).
"""
import ast
import os
import pathlib
import unittest.mock

import pytest


def test_cloudinary_config_not_in_jugadores_handler():
    """AC-10.1: cloudinary.config() must NOT appear in jugadores.py."""
    jugadores_path = (
        pathlib.Path(__file__).parent.parent.parent / "app" / "routers" / "jugadores.py"
    )
    source = jugadores_path.read_text(encoding="utf-8")

    # Parse the AST and check for cloudinary.config() calls
    tree = ast.parse(source)
    config_calls = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "config"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "cloudinary"
        ):
            config_calls.append(node)

    assert len(config_calls) == 0, (
        f"cloudinary.config() found {len(config_calls)} time(s) in jugadores.py — "
        "it must be moved to the lifespan startup in main.py (R-10 / AD-10). "
        f"Lines: {[call.lineno for call in config_calls]}"
    )


def test_cloudinary_config_in_main_lifespan():
    """AC-10.2: cloudinary.config() IS present in main.py lifespan function."""
    main_path = (
        pathlib.Path(__file__).parent.parent.parent / "app" / "main.py"
    )
    source = main_path.read_text(encoding="utf-8")

    # Check that cloudinary.config appears in the source
    assert "cloudinary.config(" in source, (
        "cloudinary.config() must be called in main.py lifespan (R-10 / AD-10). "
        "It should configure the Cloudinary SDK once at app startup."
    )


def test_cloudinary_config_called_at_startup_when_vars_set(monkeypatch):
    """AC-10.2: lifespan calls cloudinary.config when all three vars are set."""
    import asyncio
    import cloudinary
    from app.main import lifespan, app

    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "test-key")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "test-secret")

    with unittest.mock.patch.object(cloudinary, "config") as mock_config:
        async def run_lifespan():
            async with lifespan(app):
                pass  # startup and shutdown

        asyncio.run(run_lifespan())
        mock_config.assert_called_once()


def test_cloudinary_config_skipped_when_vars_absent(monkeypatch):
    """AC-10.2 (negative): lifespan does NOT call cloudinary.config when vars are missing."""
    import asyncio
    import cloudinary
    from app.main import lifespan, app

    monkeypatch.delenv("CLOUDINARY_CLOUD_NAME", raising=False)
    monkeypatch.delenv("CLOUDINARY_API_KEY", raising=False)
    monkeypatch.delenv("CLOUDINARY_API_SECRET", raising=False)

    with unittest.mock.patch.object(cloudinary, "config") as mock_config:
        async def run_lifespan():
            async with lifespan(app):
                pass

        asyncio.run(run_lifespan())
        mock_config.assert_not_called()
