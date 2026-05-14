from app.services.ranking import calcular_ranking, detect_max_points_holders


# Estructura de datos para estas funciones:
# inscripcion: {"id_jugador": int, "nombre": str}
# posicion:    {"id_jugador": int|None, "es_invitado": bool, "puntos": int}


def test_jugador_con_asistencias_aparece_en_ranking():
    inscritos = [{"id_jugador": 1, "nombre": "Ana"}]
    posiciones = [{"id_jugador": 1, "es_invitado": False, "puntos": 15}]

    ranking = calcular_ranking(inscritos, posiciones)

    assert len(ranking) == 1
    assert ranking[0]["id_jugador"] == 1
    assert ranking[0]["puntos"] == 15


def test_jugador_sin_asistencias_no_aparece_en_ranking():
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
    ]
    posiciones = [{"id_jugador": 1, "es_invitado": False, "puntos": 15}]

    ranking = calcular_ranking(inscritos, posiciones)

    ids = [r["id_jugador"] for r in ranking]
    assert 2 not in ids


def test_invitados_no_aparecen_en_ranking():
    inscritos = [{"id_jugador": 1, "nombre": "Ana"}]
    posiciones = [
        {"id_jugador": None, "es_invitado": True, "puntos": 15},
        {"id_jugador": 1, "es_invitado": False, "puntos": 14},
    ]

    ranking = calcular_ranking(inscritos, posiciones)

    assert len(ranking) == 1
    assert ranking[0]["id_jugador"] == 1


def test_ranking_ordenado_por_puntos_descendente():
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
        {"id_jugador": 3, "nombre": "Carlos"},
    ]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 10},
        {"id_jugador": 2, "es_invitado": False, "puntos": 15},
        {"id_jugador": 3, "es_invitado": False, "puntos": 12},
    ]

    ranking = calcular_ranking(inscritos, posiciones)

    assert ranking[0]["id_jugador"] == 2
    assert ranking[1]["id_jugador"] == 3
    assert ranking[2]["id_jugador"] == 1


def test_ranking_acumula_puntos_de_varias_reuniones():
    inscritos = [{"id_jugador": 1, "nombre": "Ana"}]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 1, "es_invitado": False, "puntos": 14},
    ]

    ranking = calcular_ranking(inscritos, posiciones)

    assert ranking[0]["puntos"] == 29
    assert ranking[0]["asistencias"] == 2


# ── detect_max_points_holders ─────────────────────────────────────────────────


def test_detect_max_points_holders_sin_inscripciones_devuelve_lista_vacia():
    assert detect_max_points_holders([], []) == []


def test_detect_max_points_holders_sin_asistencias_devuelve_lista_vacia():
    inscritos = [{"id_jugador": 1, "nombre": "Ana"}]
    assert detect_max_points_holders(inscritos, []) == []


def test_detect_max_points_holders_un_solo_ganador():
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
    ]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 2, "es_invitado": False, "puntos": 14},
    ]
    result = detect_max_points_holders(inscritos, posiciones)
    assert result == [{"id_jugador": 1, "nombre": "Ana"}]


def test_detect_max_points_holders_empate_2_way():
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
    ]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 2, "es_invitado": False, "puntos": 15},
    ]
    result = detect_max_points_holders(inscritos, posiciones)
    assert len(result) == 2
    ids = {p["id_jugador"] for p in result}
    assert ids == {1, 2}


def test_detect_max_points_holders_empate_3_way():
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
        {"id_jugador": 3, "nombre": "Carlos"},
    ]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 2, "es_invitado": False, "puntos": 15},
        {"id_jugador": 3, "es_invitado": False, "puntos": 15},
    ]
    result = detect_max_points_holders(inscritos, posiciones)
    assert len(result) == 3


def test_detect_max_points_holders_empate_en_2do_pero_1ro_claro():
    # Ana: 15 (clear 1st), Bruno + Carlos: 10 each (tie for 2nd)
    inscritos = [
        {"id_jugador": 1, "nombre": "Ana"},
        {"id_jugador": 2, "nombre": "Bruno"},
        {"id_jugador": 3, "nombre": "Carlos"},
    ]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 2, "es_invitado": False, "puntos": 10},
        {"id_jugador": 3, "es_invitado": False, "puntos": 10},
    ]
    result = detect_max_points_holders(inscritos, posiciones)
    assert result == [{"id_jugador": 1, "nombre": "Ana"}]
