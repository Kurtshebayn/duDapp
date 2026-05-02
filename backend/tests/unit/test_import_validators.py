"""Tests for validator helpers in import_temporada service.

Tests T-IMP-32 through T-IMP-40.
Run: pytest backend/tests/unit/test_import_validators.py
"""
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.services.import_temporada import (
    ParsedCsv,
    _validar_campeon,
    _validar_headers,
    _validar_puntajes,
    _validar_reuniones_no_vacias,
)


# ---------------------------------------------------------------------------
# Helper: build ParsedCsv quickly
# ---------------------------------------------------------------------------

def make_parsed(headers: list[str], filas: list[list[str]]) -> ParsedCsv:
    return ParsedCsv(headers=headers, filas=filas)


# ---------------------------------------------------------------------------
# _validar_headers
# ---------------------------------------------------------------------------

class TestValidarHeaders:
    """T-IMP-32 & T-IMP-33."""

    def test_validar_headers_duplicados_levanta_422(self):
        """T-IMP-32 — case-insensitive duplicate detection."""
        with pytest.raises(HTTPException) as exc_info:
            _validar_headers(["Ana", "ana"])
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_header_duplicate"

    def test_validar_headers_validos_no_levanta(self):
        """T-IMP-33 — no duplicates, no exception."""
        # Should not raise
        _validar_headers(["Ana", "Beto", "Carla"])

    def test_validar_headers_duplicados_con_espacios(self):
        """Additional: whitespace variants are also duplicates."""
        with pytest.raises(HTTPException) as exc_info:
            _validar_headers(["Ana ", " Ana"])
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_header_duplicate"


# ---------------------------------------------------------------------------
# _validar_puntajes
# ---------------------------------------------------------------------------

class TestValidarPuntajes:
    """T-IMP-34, T-IMP-35, T-IMP-36."""

    def test_validar_puntajes_celdas_invalidas_reporta_todas(self):
        """T-IMP-34 — two invalid cells across two rows, both reported."""
        parsed = make_parsed(
            headers=["Ana", "Beto"],
            filas=[["?", "14"], ["15", "-3"]],
        )
        with pytest.raises(HTTPException) as exc_info:
            _validar_puntajes(parsed)
        exc = exc_info.value
        assert exc.status_code == 422
        assert exc.detail["code"] == "puntaje_invalido"
        errores = exc.detail["errores"]
        assert len(errores) == 2
        # First error: row 1, column Ana, value "?"
        assert errores[0]["fila"] == 1
        assert errores[0]["columna"] == "Ana"
        assert errores[0]["valor"] == "?"
        # Second error: row 2, column Beto, value "-3"
        assert errores[1]["fila"] == 2
        assert errores[1]["columna"] == "Beto"
        assert errores[1]["valor"] == "-3"

    def test_validar_puntajes_todos_validos_retorna_matriz(self):
        """T-IMP-35 — all valid scores; returns int matrix."""
        parsed = make_parsed(
            headers=["Ana", "Beto", "Carla"],
            filas=[["15", "14", "13"], ["10", "9", "8"]],
        )
        result = _validar_puntajes(parsed)
        assert result == [[15, 14, 13], [10, 9, 8]]

    def test_validar_puntajes_rango_extremo_15_y_0_validos(self):
        """T-IMP-36 — scores 0 and 15 are within [0, 15], must NOT raise."""
        parsed = make_parsed(
            headers=["Ana", "Beto"],
            filas=[["0", "15"]],
        )
        result = _validar_puntajes(parsed)
        assert result == [[0, 15]]

    def test_validar_puntajes_score_16_invalido(self):
        """Score > 15 must be included in errors."""
        parsed = make_parsed(
            headers=["Ana"],
            filas=[["16"]],
        )
        with pytest.raises(HTTPException) as exc_info:
            _validar_puntajes(parsed)
        assert exc_info.value.detail["code"] == "puntaje_invalido"
        assert exc_info.value.detail["errores"][0]["valor"] == "16"

    def test_validar_puntajes_score_negativo_invalido(self):
        """Negative integers are invalid."""
        parsed = make_parsed(
            headers=["Ana"],
            filas=[["-1"]],
        )
        with pytest.raises(HTTPException) as exc_info:
            _validar_puntajes(parsed)
        assert exc_info.value.detail["code"] == "puntaje_invalido"

    def test_validar_puntajes_celda_vacia_invalida(self):
        """Empty string cell is invalid."""
        parsed = make_parsed(
            headers=["Ana"],
            filas=[[""]],
        )
        with pytest.raises(HTTPException) as exc_info:
            _validar_puntajes(parsed)
        assert exc_info.value.detail["code"] == "puntaje_invalido"


# ---------------------------------------------------------------------------
# _validar_reuniones_no_vacias
# ---------------------------------------------------------------------------

class TestValidarReunionesNoVacias:
    """T-IMP-37."""

    def test_validar_reuniones_no_vacias_levanta_si_todos_ausentes(self):
        """T-IMP-37 — all-zero row is an invalid meeting."""
        with pytest.raises(HTTPException) as exc_info:
            _validar_reuniones_no_vacias([[0, 0, 0]])
        exc = exc_info.value
        assert exc.status_code == 422
        assert exc.detail["code"] == "reunion_todos_ausentes"
        assert exc.detail["fila"] == 1

    def test_validar_reuniones_no_vacias_segunda_fila_todos_ausentes(self):
        """All-zero on row 2 (1-based fila=2)."""
        with pytest.raises(HTTPException) as exc_info:
            _validar_reuniones_no_vacias([[15, 14, 0], [0, 0, 0]])
        assert exc_info.value.detail["fila"] == 2

    def test_validar_reuniones_no_vacias_ok_si_al_menos_uno_presente(self):
        """Rows with at least one non-zero score must pass without exception."""
        # Should not raise
        _validar_reuniones_no_vacias([[15, 0, 0], [0, 14, 0]])


# ---------------------------------------------------------------------------
# _validar_campeon
# ---------------------------------------------------------------------------

class TestValidarCampeon:
    """T-IMP-38, T-IMP-39, T-IMP-40."""

    def _jugador(self, nombre: str) -> MagicMock:
        j = MagicMock()
        j.nombre = nombre
        j.id = 1
        return j

    def test_validar_campeon_nombre_no_inscripto_levanta_422(self):
        """T-IMP-38 — campeon name not matching any header."""
        jugadores = {"Ana": self._jugador("Ana"), "Beto": self._jugador("Beto")}
        with pytest.raises(HTTPException) as exc_info:
            _validar_campeon("Carlos", jugadores)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "campeon_no_inscripto"

    def test_validar_campeon_nombre_valido_retorna_jugador(self):
        """T-IMP-39 — case-insensitive match; returns the Jugador object."""
        jugador_ana = self._jugador("Ana")
        jugadores = {"Ana": jugador_ana}
        result = _validar_campeon("ana", jugadores)
        assert result is jugador_ana

    def test_validar_campeon_ninguno_retorna_none(self):
        """T-IMP-40 — campeon_nombre=None returns None immediately."""
        jugadores = {"Ana": self._jugador("Ana")}
        result = _validar_campeon(None, jugadores)
        assert result is None

    def test_validar_campeon_exact_case_match(self):
        """Exact case match also works."""
        jugador_beto = self._jugador("Beto")
        jugadores = {"Ana": self._jugador("Ana"), "Beto": jugador_beto}
        result = _validar_campeon("Beto", jugadores)
        assert result is jugador_beto

    def test_validar_campeon_nombre_con_espacios_match(self):
        """Leading/trailing whitespace in campeon_nombre is trimmed."""
        jugador_ana = self._jugador("Ana")
        jugadores = {"Ana": jugador_ana}
        result = _validar_campeon("  ana  ", jugadores)
        assert result is jugador_ana
