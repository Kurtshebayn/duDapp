"""
Security audit logger — R-9 / AD-8.

Emits structured log lines to stdout via stdlib logging.
The "AUDIT" prefix makes Render log filtering trivial.

All helpers must NEVER log passwords or secrets.
"""
import logging
import sys

_logger = logging.getLogger("dudapp.audit")


def _configure() -> None:
    """Configure basicConfig idempotently (no duplicate handlers under pytest)."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            stream=sys.stdout,
        )


_configure()


def log_failed_login(identificador: str, ip: str) -> None:
    """Emit a WARNING for a failed login attempt.

    Args:
        identificador: The email or username submitted by the user (NOT the password).
        ip: The request IP address.
    """
    _logger.warning("AUDIT failed_login id=%s ip=%s", identificador, ip)


def log_successful_login(user_id: int, ip: str) -> None:
    """Emit an INFO for a successful login."""
    _logger.info("AUDIT successful_login user_id=%d ip=%s", user_id, ip)


def log_temporada_cerrada(user_id: int, temporada_id: int) -> None:
    """Emit an INFO when an admin closes a season."""
    _logger.info("AUDIT temporada_cerrada user_id=%d temporada_id=%d", user_id, temporada_id)


def log_import_temporada(user_id: int, nombre: str, status: str) -> None:
    """Emit an INFO for a bulk CSV import.

    Args:
        status: "success" or "failed".
    """
    _logger.info("AUDIT import_temporada user_id=%d nombre=%s status=%s", user_id, nombre, status)
