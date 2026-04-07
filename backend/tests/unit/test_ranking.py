from app.services.ranking import calcular_ranking, calcular_estadisticas


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


def test_estadisticas_asistencias_y_promedio():
    inscritos = [{"id_jugador": 1, "nombre": "Ana"}]
    posiciones = [
        {"id_jugador": 1, "es_invitado": False, "puntos": 15},
        {"id_jugador": 1, "es_invitado": False, "puntos": 13},
    ]
    total_reuniones = 3

    stats = calcular_estadisticas(inscritos, posiciones, total_reuniones)

    jugador = stats[0]
    assert jugador["asistencias"] == 2
    assert jugador["promedio"] == 14.0
    assert jugador["inasistencias"] == 1
