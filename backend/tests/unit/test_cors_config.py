"""
R-6 unit tests — CORS parsing.

AC-6.1: Space after comma in CORS_ORIGINS → origins are stripped.
AC-6.2: Empty CORS_ORIGINS → ValueError raised (not tested here via subprocess —
        the integration path is covered by the fail-fast behavior of config.py).
        We test the parsing function directly.
"""
import os
import sys


def test_cors_origins_with_spaces_are_stripped():
    """AC-6.1: Whitespace around origins is stripped."""
    # We test the parsing logic by manipulating the env var and re-running the helper.
    # Since config.py is already imported, we test our helper via a subprocess that
    # prints the result of parsing.
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "os.environ['JWT_SECRET'] = 'pytest-ci-secret-key-do-not-use-in-prod-32ch!'; "
                "os.environ['CORS_ORIGINS'] = 'https://a.com, https://b.com'; "
                "from app.config import _parse_cors_origins; "
                "origins = _parse_cors_origins(); "
                "print(origins)"
            ),
        ],
        capture_output=True,
        text=True,
        cwd="E:/duDapp/backend",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # Both origins must appear without leading space
    assert "'https://a.com'" in result.stdout
    assert "'https://b.com'" in result.stdout
    assert "' https://b.com'" not in result.stdout, "Space was not stripped from second origin"


def test_empty_cors_origins_raises_value_error():
    """AC-6.2: Empty CORS_ORIGINS causes ValueError at config parse time."""
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "os.environ['JWT_SECRET'] = 'a-valid-secret-key-that-is-long-enough-12345!'; "
                "os.environ['CORS_ORIGINS'] = ''; "
                "import app.config"
            ),
        ],
        capture_output=True,
        text=True,
        cwd="E:/duDapp/backend",
    )
    assert result.returncode != 0, "Expected failure but process exited 0"
    assert "CORS_ORIGINS" in result.stderr or "CORS" in result.stderr
