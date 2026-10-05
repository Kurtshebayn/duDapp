from app.models.temporada import ModoPuntaje


def calcular_puntos(
    posicion: int,
    modo: ModoPuntaje = ModoPuntaje.fijo_15,
    total_participantes: int | None = None,
) -> int:
    """Points for a finishing position under the season's scoring mode.

    - fijo_15: position 1 = 15 points, position N = 15 - (N-1).
    - por_asistentes: position 1 = total participants in the meeting (guests
      included), position N = total - (N-1). Callers pass the highest
      registered position as the total.
    """
    if modo == ModoPuntaje.por_asistentes:
        if total_participantes is None:
            raise ValueError("por_asistentes requires total_participantes")
        return total_participantes - (posicion - 1)
    return 15 - (posicion - 1)
