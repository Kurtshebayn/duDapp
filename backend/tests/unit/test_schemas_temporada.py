"""
Unit tests for TemporadaResponse schema extensions.

Tests the new fields:
  campeon_id: int | None = None
  tie_detected: bool = False
  tied_players: list[TiedPlayerSchema] | None = None

And the new schemas:
  TiedPlayerSchema
  DesignarCampeonRequest
"""
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.temporada import (
    DesignarCampeonRequest,
    TiedPlayerSchema,
    TemporadaResponse,
)


def test_temporada_response_defaults_campeon_id_none_y_tie_detected_false():
    """AC-1: TemporadaResponse defaults to campeon_id=None, tie_detected=False."""
    t = TemporadaResponse(
        id=1,
        nombre="Liga 2024",
        fecha_inicio=date.today(),
        estado="activa",
    )
    assert t.campeon_id is None
    assert t.tie_detected is False
    assert t.tied_players is None


def test_temporada_response_tied_players_excluido_cuando_none():
    """D6: tied_players must NOT appear in model_dump when None (for exclude_none=True on router)."""
    t = TemporadaResponse(
        id=1,
        nombre="Liga 2024",
        fecha_inicio=date.today(),
        estado="activa",
    )
    dumped = t.model_dump(exclude_none=True)
    assert "tied_players" not in dumped


def test_temporada_response_con_empate_serializa_tied_players():
    """AC-3: When tie_detected=True and tied_players set, tied_players appears in dump."""
    t = TemporadaResponse(
        id=1,
        nombre="Liga 2024",
        fecha_inicio=date.today(),
        estado="cerrada",
        tie_detected=True,
        tied_players=[
            TiedPlayerSchema(id_jugador=1, nombre="Ana"),
            TiedPlayerSchema(id_jugador=2, nombre="Bruno"),
        ],
    )
    dumped = t.model_dump(exclude_none=True)
    assert "tied_players" in dumped
    assert len(dumped["tied_players"]) == 2


def test_tied_player_schema_serializa_correctamente():
    """TiedPlayerSchema fields serialize correctly."""
    p = TiedPlayerSchema(id_jugador=2, nombre="Bruno")
    dumped = p.model_dump()
    assert dumped == {"id_jugador": 2, "nombre": "Bruno"}


def test_designar_campeon_request_parsea_id_jugador():
    """DesignarCampeonRequest parses correctly."""
    req = DesignarCampeonRequest(id_jugador=5)
    assert req.id_jugador == 5


def test_designar_campeon_request_rechaza_no_entero():
    """DesignarCampeonRequest raises ValidationError when id_jugador is not int."""
    with pytest.raises(ValidationError):
        DesignarCampeonRequest(id_jugador="abc")
