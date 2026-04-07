"""
Funciones puras de ranking y estadísticas — sin dependencias de DB ni HTTP.

Tipos de entrada (dicts simples):
  inscripcion: {"id_jugador": int, "nombre": str}
  posicion:    {"id_jugador": int | None, "es_invitado": bool, "puntos": int}
"""


def calcular_ranking(
    inscripciones: list[dict],
    posiciones: list[dict],
) -> list[dict]:
    """
    Retorna el ranking de jugadores inscritos con al menos 1 asistencia,
    ordenado por puntos totales descendente. Los invitados nunca aparecen.
    """
    totales: dict[int, dict] = {
        i["id_jugador"]: {"nombre": i["nombre"], "puntos": 0, "asistencias": 0}
        for i in inscripciones
    }

    for pos in posiciones:
        if pos["es_invitado"] or pos["id_jugador"] is None:
            continue
        pid = pos["id_jugador"]
        if pid in totales:
            totales[pid]["puntos"] += pos["puntos"]
            totales[pid]["asistencias"] += 1

    resultado = [
        {"id_jugador": pid, **data}
        for pid, data in totales.items()
        if data["asistencias"] > 0
    ]
    resultado.sort(key=lambda x: x["puntos"], reverse=True)
    return resultado


def calcular_estadisticas(
    inscripciones: list[dict],
    posiciones: list[dict],
    total_reuniones: int,
) -> list[dict]:
    """
    Igual que calcular_ranking pero agrega promedio e inasistencias.
    """
    ranking = calcular_ranking(inscripciones, posiciones)
    for entry in ranking:
        asistencias = entry["asistencias"]
        entry["promedio"] = round(entry["puntos"] / asistencias, 2) if asistencias else 0.0
        entry["inasistencias"] = total_reuniones - asistencias
    return ranking
