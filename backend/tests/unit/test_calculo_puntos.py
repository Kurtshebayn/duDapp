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
