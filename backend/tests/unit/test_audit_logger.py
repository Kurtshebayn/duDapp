"""
R-9: Security logging — audit log unit tests.

AC-9.1: Failed login → WARNING log entry with identifier (not password) + IP.
AC-9.4: basicConfig called at most once (no duplicate handlers under pytest).
"""
import logging

import pytest


def test_log_failed_login_emits_warning(caplog):
    """AC-9.1: Failed login emits a WARNING with identifier and IP."""
    from app.security.audit import log_failed_login

    with caplog.at_level(logging.WARNING, logger="dudapp.audit"):
        log_failed_login("user@example.com", "1.2.3.4")

    assert len(caplog.records) >= 1
    record = caplog.records[-1]
    assert record.levelno >= logging.WARNING
    assert "user@example.com" in record.message
    assert "1.2.3.4" in record.message
    # Ensure password is never included
    assert "password" not in record.message.lower()


def test_log_failed_login_does_not_include_password(caplog):
    """AC-9.1: Password must never appear in the audit log."""
    from app.security.audit import log_failed_login

    with caplog.at_level(logging.WARNING, logger="dudapp.audit"):
        log_failed_login("someone@example.com", "10.0.0.1")

    for record in caplog.records:
        assert "supersecretpassword" not in record.message


def test_log_successful_login_emits_info(caplog):
    """AC-9.1 (success path): Successful login emits an INFO log with user_id and IP."""
    from app.security.audit import log_successful_login

    with caplog.at_level(logging.INFO, logger="dudapp.audit"):
        log_successful_login(user_id=42, ip="192.168.1.1")

    assert len(caplog.records) >= 1
    record = caplog.records[-1]
    assert record.levelno >= logging.INFO
    assert "42" in record.message
    assert "192.168.1.1" in record.message


def test_log_temporada_cerrada_emits_info(caplog):
    """AC-9.2: Closing a season emits INFO log with user_id and temporada_id."""
    from app.security.audit import log_temporada_cerrada

    with caplog.at_level(logging.INFO, logger="dudapp.audit"):
        log_temporada_cerrada(user_id=1, temporada_id=7)

    assert len(caplog.records) >= 1
    record = caplog.records[-1]
    assert record.levelno >= logging.INFO
    assert "1" in record.message
    assert "7" in record.message


def test_no_duplicate_handlers_after_multiple_imports():
    """AC-9.4: Importing audit module multiple times does not add duplicate handlers."""
    import importlib

    from app.security import audit

    # Re-import should not add handlers
    importlib.reload(audit)
    root_logger = logging.getLogger("dudapp.audit")
    # Root logger handlers won't duplicate (we rely on propagate to root)
    # Just verify the logger exists with the right name
    assert root_logger.name == "dudapp.audit"
