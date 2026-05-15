"""Unit tests for new closed-season schemas.

Tests verify:
- RankingEntryCerrada has no delta_posicion / lider_desde_jornada fields
- CampeonResponse serializes correctly
- RankingUltimaCerradaResponse handles fecha_cierre=None and campeon=None
"""
import pytest
from datetime import date

# These imports will FAIL until schemas are added (RED phase)
from app.schemas.consultas import (
    CampeonResponse,
    RankingEntryCerrada,
    RankingUltimaCerradaResponse,
)


class TestRankingEntryCerrada:
    def test_does_not_have_delta_posicion_field(self):
        """RankingEntryCerrada schema must NOT include delta_posicion."""
        assert "delta_posicion" not in RankingEntryCerrada.model_fields

    def test_does_not_have_lider_desde_jornada_field(self):
        """RankingEntryCerrada schema must NOT include lider_desde_jornada."""
        assert "lider_desde_jornada" not in RankingEntryCerrada.model_fields

    def test_has_racha_field(self):
        """RankingEntryCerrada schema MUST include racha."""
        assert "racha" in RankingEntryCerrada.model_fields

    def test_valid_instantiation(self):
        entry = RankingEntryCerrada(
            posicion=1,
            id_jugador=42,
            nombre="Ana",
            foto_url=None,
            puntos=75,
            asistencias=5,
            promedio=15.0,
            racha=3,
        )
        assert entry.posicion == 1
        assert entry.racha == 3
        assert entry.foto_url is None

    def test_foto_url_optional(self):
        """foto_url should be optional (defaults to None)."""
        entry = RankingEntryCerrada(
            posicion=2,
            id_jugador=7,
            nombre="Bruno",
            puntos=60,
            asistencias=4,
            promedio=15.0,
            racha=0,
        )
        assert entry.foto_url is None


class TestCampeonResponse:
    def test_valid_with_all_fields(self):
        campeon = CampeonResponse(
            id=1,
            nombre="Ana",
            foto_url="https://example.com/ana.jpg",
            puntos=75,
            asistencias=5,
            promedio=15.0,
        )
        assert campeon.id == 1
        assert campeon.nombre == "Ana"
        assert campeon.promedio == 15.0

    def test_foto_url_optional(self):
        campeon = CampeonResponse(
            id=1,
            nombre="Ana",
            puntos=75,
            asistencias=5,
            promedio=15.0,
        )
        assert campeon.foto_url is None


class TestRankingUltimaCerradaResponse:
    def test_fecha_cierre_none_serializes_to_null(self):
        """fecha_cierre=None must serialize (not be omitted)."""
        resp = RankingUltimaCerradaResponse(
            temporada_id=1,
            temporada_nombre="Liga 2024",
            fecha_cierre=None,
            campeon=None,
            ranking=[],
        )
        data = resp.model_dump()
        assert "fecha_cierre" in data
        assert data["fecha_cierre"] is None

    def test_campeon_none_serializes_to_null(self):
        """campeon=None must serialize (not be omitted)."""
        resp = RankingUltimaCerradaResponse(
            temporada_id=1,
            temporada_nombre="Liga 2024",
            fecha_cierre=None,
            campeon=None,
            ranking=[],
        )
        data = resp.model_dump()
        assert "campeon" in data
        assert data["campeon"] is None

    def test_with_fecha_cierre_present(self):
        resp = RankingUltimaCerradaResponse(
            temporada_id=1,
            temporada_nombre="Liga 2024",
            fecha_cierre=date(2026, 5, 15),
            campeon=None,
            ranking=[],
        )
        assert resp.fecha_cierre == date(2026, 5, 15)

    def test_with_campeon_embedded(self):
        campeon = CampeonResponse(
            id=1, nombre="Ana", puntos=75, asistencias=5, promedio=15.0
        )
        resp = RankingUltimaCerradaResponse(
            temporada_id=1,
            temporada_nombre="Liga 2024",
            fecha_cierre=date(2026, 5, 15),
            campeon=campeon,
            ranking=[],
        )
        assert resp.campeon is not None
        assert resp.campeon.nombre == "Ana"

    def test_ranking_list_populated(self):
        entry = RankingEntryCerrada(
            posicion=1,
            id_jugador=1,
            nombre="Ana",
            puntos=75,
            asistencias=5,
            promedio=15.0,
            racha=2,
        )
        resp = RankingUltimaCerradaResponse(
            temporada_id=1,
            temporada_nombre="Liga 2024",
            fecha_cierre=None,
            campeon=None,
            ranking=[entry],
        )
        assert len(resp.ranking) == 1
        assert resp.ranking[0].nombre == "Ana"
