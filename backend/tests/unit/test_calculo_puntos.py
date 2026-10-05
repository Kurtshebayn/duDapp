import pytest

from app.services.puntos import calcular_puntos


def test_posicion_1_vale_15():
    assert calcular_puntos(1) == 15


def test_posicion_2_vale_14():
    assert calcular_puntos(2) == 14


def test_posicion_n_vale_15_menos_n_menos_1():
    assert calcular_puntos(5) == 11
    assert calcular_puntos(10) == 6
    assert calcular_puntos(15) == 1


def test_invitado_en_pos_1_reduce_puntos_del_siguiente():
    # Invitado en posición 1 → 15 pts. Jugador en posición 2 → 14 pts, no 15.
    # La fórmula es la misma para todos: puntos = 15 - (posicion - 1).
    # El test verifica que la posición numérica es lo que manda, sin importar si es invitado.
    assert calcular_puntos(1) == 15  # invitado en pos 1
    assert calcular_puntos(2) == 14  # jugador en pos 2, recibe 14 (no 15)


# ── Scoring mode per season ──────────────────────────────────────────────────

from app.models.temporada import ModoPuntaje  # noqa: E402


def test_fijo_15_explicito_ignora_total_participantes():
    # fijo_15 keeps the historical rule regardless of how many played.
    assert calcular_puntos(1, ModoPuntaje.fijo_15, 6) == 15
    assert calcular_puntos(6, ModoPuntaje.fijo_15, 6) == 10


def test_por_asistentes_seis_participantes_reparte_6_a_1():
    puntos = [calcular_puntos(p, ModoPuntaje.por_asistentes, 6) for p in range(1, 7)]
    assert puntos == [6, 5, 4, 3, 2, 1]


def test_por_asistentes_primer_lugar_vale_total_participantes():
    assert calcular_puntos(1, ModoPuntaje.por_asistentes, 4) == 4
    assert calcular_puntos(1, ModoPuntaje.por_asistentes, 20) == 20


def test_por_asistentes_sin_total_falla():
    with pytest.raises(ValueError):
        calcular_puntos(1, ModoPuntaje.por_asistentes, None)
