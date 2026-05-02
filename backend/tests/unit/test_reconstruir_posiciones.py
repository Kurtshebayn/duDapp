"""Unit tests for reconstruir_posiciones_de_reunion — pure function, no DB.

Tests T-IMP-09 through T-IMP-20 (12 tests total).
All tests MUST fail before T-IMP-21 implements the function.
"""
import pytest

from app.services.reconstruir_posiciones import (
    PosicionReconstruida,
    reconstruir_posiciones_de_reunion,
)


# T-IMP-09 — Happy path: 3 consecutive scores, no gaps, no absences
def test_sin_invitados_sin_ausentes():
    """3 players with scores 15,14,13 → 3 rows, all es_invitado=False, correct names."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 14, "Carla": 13})
    assert len(result) == 3
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador="Ana", es_invitado=False)
    assert result[1] == PosicionReconstruida(posicion=2, puntos=14, nombre_jugador="Beto", es_invitado=False)
    assert result[2] == PosicionReconstruida(posicion=3, puntos=13, nombre_jugador="Carla", es_invitado=False)


# T-IMP-10 — One intermediate guest (gap at position 2, expected score 14 missing)
def test_un_invitado_intermedio():
    """Ana=15, Beto=13 → 3 rows: Ana, guest@14, Beto."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 13})
    assert len(result) == 3
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador="Ana", es_invitado=False)
    assert result[1] == PosicionReconstruida(posicion=2, puntos=14, nombre_jugador=None, es_invitado=True)
    assert result[2] == PosicionReconstruida(posicion=3, puntos=13, nombre_jugador="Beto", es_invitado=False)


# T-IMP-11 — Three consecutive guests (scores 14,13,12 all missing)
def test_invitados_consecutivos():
    """Ana=15, Beto=11 → 5 rows: Ana, guest@14, guest@13, guest@12, Beto."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 11})
    assert len(result) == 5
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador="Ana", es_invitado=False)
    assert result[1] == PosicionReconstruida(posicion=2, puntos=14, nombre_jugador=None, es_invitado=True)
    assert result[2] == PosicionReconstruida(posicion=3, puntos=13, nombre_jugador=None, es_invitado=True)
    assert result[3] == PosicionReconstruida(posicion=4, puntos=12, nombre_jugador=None, es_invitado=True)
    assert result[4] == PosicionReconstruida(posicion=5, puntos=11, nombre_jugador="Beto", es_invitado=False)


# T-IMP-12 — Absent player (score=0) produces no row; intermediate guest still inferred
def test_ausencias_y_presentes_mezclados():
    """Ana=15, Beto=0 (absent), Carla=13 → 3 rows, no Beto row."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 0, "Carla": 13})
    assert len(result) == 3
    names = [r.nombre_jugador for r in result]
    assert "Beto" not in names
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador="Ana", es_invitado=False)
    assert result[1] == PosicionReconstruida(posicion=2, puntos=14, nombre_jugador=None, es_invitado=True)
    assert result[2] == PosicionReconstruida(posicion=3, puntos=13, nombre_jugador="Carla", es_invitado=False)


# T-IMP-13 — Guest at position 1 (nobody scored 15, highest is 14)
def test_invitado_en_primera_posicion():
    """Ana=14 → guest@15, Ana@14 (2 rows)."""
    result = reconstruir_posiciones_de_reunion({"Ana": 14})
    assert len(result) == 2
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador=None, es_invitado=True)
    assert result[1] == PosicionReconstruida(posicion=2, puntos=14, nombre_jugador="Ana", es_invitado=False)


# T-IMP-14 — All absent → empty list (orchestrator handles semantic error, pure fn just returns [])
def test_todos_ausentes_devuelve_lista_vacia():
    """All scores=0 → empty list."""
    result = reconstruir_posiciones_de_reunion({"Ana": 0, "Beto": 0})
    assert result == []


# T-IMP-15 — Single player at position 1
def test_un_solo_jugador_primer_lugar():
    """Ana=15 → single row, pos=1, es_invitado=False."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15})
    assert len(result) == 1
    assert result[0] == PosicionReconstruida(posicion=1, puntos=15, nombre_jugador="Ana", es_invitado=False)


# T-IMP-16 — Full 15-player game, all positions filled, no guests
def test_quince_jugadores_sin_invitados():
    """15 players at scores 15..1 → 15 rows, all es_invitado=False."""
    scores = {f"Jugador{i}": 16 - i for i in range(1, 16)}
    result = reconstruir_posiciones_de_reunion(scores)
    assert len(result) == 15
    for i, row in enumerate(result, start=1):
        assert row.posicion == i
        assert row.puntos == 16 - i
        assert row.es_invitado is False


# T-IMP-17 — Duplicate non-zero scores → raises ValueError
def test_score_duplicado_levanta_value_error():
    """Ana=15, Beto=15 (both non-zero) → ValueError (puntajes_duplicados)."""
    with pytest.raises(ValueError):
        reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 15})


# T-IMP-18 — Negative score → raises ValueError
def test_score_negativo_levanta_value_error():
    """Ana=-1 → ValueError (invalid input, defence layer)."""
    with pytest.raises(ValueError):
        reconstruir_posiciones_de_reunion({"Ana": -1})


# T-IMP-19 — Score > 15 → raises ValueError
def test_score_mayor_a_15_levanta_value_error():
    """Ana=20 → ValueError (out of range)."""
    with pytest.raises(ValueError):
        reconstruir_posiciones_de_reunion({"Ana": 20})


# T-IMP-20 — Count of inferred guests matches es_invitado rows
def test_conteo_invitados_inferidos_correcto():
    """Use T-IMP-11 scenario: Ana=15, Beto=11 → 3 guests inferred."""
    result = reconstruir_posiciones_de_reunion({"Ana": 15, "Beto": 11})
    invitados = [p for p in result if p.es_invitado]
    assert len(invitados) == 3
    for inv in invitados:
        assert inv.nombre_jugador is None
        assert inv.es_invitado is True
