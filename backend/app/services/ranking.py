"""
Funciones puras de ranking — sin dependencias de DB ni HTTP.

Tipos de entrada (dicts simples):
  inscripcion: {"id_jugador": int, "nombre": str}
  posicion:    {"id_jugador": int | None, "es_invitado": bool, "puntos": int}
"""


def assign_competition_ranks(ranking_entries: list[dict]) -> list[dict]:
    """
    Asigna `posicion` (competition rank, estilo olímpico: 1-1-3-4) a cada
    entry del ranking.

    Asume que ranking_entries YA viene ordenado por puntos desc — output
    de calcular_ranking(). NO muta el input; devuelve nueva lista.
    Bit-exact con frontend/src/lib/ranking.js:assignRanks().

    Algoritmo:
      - i == 0 o puntos distintos al anterior → posicion = i + 1
      - Empate con anterior → misma posicion que el anterior
    """
    result: list[dict] = []
    for i, entry in enumerate(ranking_entries):
        if i > 0 and entry["puntos"] == ranking_entries[i - 1]["puntos"]:
            posicion = result[i - 1]["posicion"]
        else:
            posicion = i + 1
        result.append({**entry, "posicion": posicion})
    return result


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
