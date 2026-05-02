"""Tests for _parsear_csv helper in import_temporada service.

Tests T-IMP-23 through T-IMP-30.
Run: pytest backend/tests/unit/test_import_csv_parser.py
"""
import pytest
from fastapi import HTTPException

from app.services.import_temporada import ParsedCsv, _parsear_csv


class TestParsearCsvBasicSemicolon:
    """T-IMP-23 — basic CSV with semicolon separator."""

    def test_parsea_csv_basico_separador_punto_y_coma(self):
        data = b"Ana;Beto;Carla\n15;14;13\n"
        parsed = _parsear_csv(data)
        assert parsed.headers == ["Ana", "Beto", "Carla"]
        assert parsed.filas == [["15", "14", "13"]]


class TestParsearCsvCommaFallback:
    """T-IMP-24 — comma separator auto-detected when no semicolons."""

    def test_parsea_csv_separador_coma_si_no_hay_punto_y_coma(self):
        data = b"Ana,Beto\n15,14\n"
        parsed = _parsear_csv(data)
        assert parsed.headers == ["Ana", "Beto"]
        assert parsed.filas == [["15", "14"]]


class TestParsearCsvBom:
    """T-IMP-25 — UTF-8 BOM is silently discarded."""

    def test_descarta_bom_utf8(self):
        # UTF-8 BOM is 0xEF 0xBB 0xBF
        data = b"\xef\xbb\xbfAna;Beto\n15;14\n"
        parsed = _parsear_csv(data)
        assert parsed.headers == ["Ana", "Beto"]
        assert parsed.filas == [["15", "14"]]
        # First header must NOT start with the BOM character
        assert not parsed.headers[0].startswith("﻿")


class TestParsearCsvInvalidEncoding:
    """T-IMP-26 — non-UTF-8 bytes raise 422 csv_encoding_invalid."""

    def test_levanta_csv_encoding_invalid_si_no_es_utf8(self):
        # bytes that are NOT valid UTF-8
        data = b"\xff\xfe Ana;Beto"
        with pytest.raises(HTTPException) as exc_info:
            _parsear_csv(data)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_encoding_invalid"


class TestParsearCsvNoStructure:
    """T-IMP-27 — empty or unstructured file raises 422 csv_invalido."""

    def test_levanta_csv_invalido_si_archivo_vacio(self):
        data = b""
        with pytest.raises(HTTPException) as exc_info:
            _parsear_csv(data)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_invalido"

    def test_levanta_csv_invalido_si_linea_sin_delimitador(self):
        # A single line with no separator produces a single-column header, which
        # means no player names at all (need at least one header name).
        # Design: "at least one player name" → a one-column header is valid for the
        # parser (one player), but an empty header list is not.
        # However, a completely unstructured file (garbage bytes forming one token)
        # should still pass if it decodes — we test truly empty / whitespace-only.
        data = b"   \n  \n"
        with pytest.raises(HTTPException) as exc_info:
            _parsear_csv(data)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_invalido"


class TestParsearCsvNoDataRows:
    """T-IMP-28 — header but no data rows raises 422 csv_sin_reuniones."""

    def test_levanta_csv_sin_reuniones_si_solo_hay_header(self):
        data = b"Ana;Beto\n"
        with pytest.raises(HTTPException) as exc_info:
            _parsear_csv(data)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "csv_sin_reuniones"


class TestParsearCsvBlankLines:
    """T-IMP-29 — blank lines are silently ignored."""

    def test_ignora_filas_en_blanco(self):
        data = b"Ana;Beto\n\n15;14\n\n"
        parsed = _parsear_csv(data)
        assert len(parsed.filas) == 1
        assert parsed.filas[0] == ["15", "14"]


class TestParsearCsvHeaderTrim:
    """T-IMP-30 — header names are trimmed of whitespace."""

    def test_trim_de_headers(self):
        data = b" Ana ; Beto \n15;14\n"
        parsed = _parsear_csv(data)
        assert parsed.headers == ["Ana", "Beto"]
