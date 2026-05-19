"""
R-9 integration tests — audit log wiring.

AC-9.1: Failed login → WARNING log entry in auth endpoint.
AC-9.1: Successful login → INFO log entry in auth endpoint.
AC-9.2: POST /temporadas/{id}/cerrar → INFO log entry with user_id + temporada_id.
"""
import logging
from datetime import date

import pytest


def test_failed_login_emits_audit_warning(client, caplog):
    """AC-9.1: Wrong credentials → audit WARNING with identifier, not password."""
    with caplog.at_level(logging.WARNING, logger="dudapp.audit"):
        response = client.post(
            "/auth/login",
            json={"identificador": "ghost@nowhere.com", "password": "wrongpassword123"},
        )

    assert response.status_code == 401
    audit_records = [r for r in caplog.records if r.name == "dudapp.audit"]
    assert len(audit_records) >= 1, "Expected at least one audit log entry on failed login"
    record = audit_records[-1]
    assert record.levelno >= logging.WARNING
    assert "ghost@nowhere.com" in record.message
    # Password must NOT appear in the log
    assert "wrongpassword123" not in record.message


def test_successful_login_emits_audit_info(client, admin_user, caplog):
    """AC-9.1 (success path): Valid credentials → audit INFO with user_id."""
    with caplog.at_level(logging.INFO, logger="dudapp.audit"):
        response = client.post(
            "/auth/login",
            json={"identificador": "admin@dudo.com", "password": "admin123"},
        )

    assert response.status_code == 200
    audit_records = [r for r in caplog.records if r.name == "dudapp.audit"]
    assert len(audit_records) >= 1, "Expected at least one audit log entry on successful login"
    record = audit_records[-1]
    assert record.levelno >= logging.INFO
    assert str(admin_user.id) in record.message


def test_close_season_emits_audit_info(client, admin_user, caplog):
    """AC-9.2: Closing a season → audit INFO with user_id and temporada_id.

    Uses the API to create and close the season — same pattern as test_temporadas.py.
    """
    # Login first to get auth token
    login_resp = client.post(
        "/auth/login",
        json={"identificador": "admin@dudo.com", "password": "admin123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Create a season via the API (no direct DB access — avoids session state issues)
    create_resp = client.post(
        "/temporadas",
        json={"nombre": "Temporada Audit Test", "fecha_inicio": "2026-01-01", "jugadores": []},
        headers=auth,
    )
    assert create_resp.status_code == 201
    temporada_id = create_resp.json()["id"]

    # Close the season while capturing audit logs
    with caplog.at_level(logging.INFO, logger="dudapp.audit"):
        response = client.post(
            f"/temporadas/{temporada_id}/cerrar",
            headers=auth,
        )

    assert response.status_code == 200
    audit_records = [r for r in caplog.records if r.name == "dudapp.audit"]
    # Find the close_season entry
    close_records = [r for r in audit_records if "temporada_cerrada" in r.message]
    assert len(close_records) >= 1, "Expected audit log for closing season"
    record = close_records[-1]
    assert str(admin_user.id) in record.message
    assert str(temporada_id) in record.message
