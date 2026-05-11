"""
Narrative computation — pure functions, no DB dependency.

SEMANTIC delta convention (decisions-supplement engram #98):
  delta_posicion = anterior_posicion - nueva_posicion
  Positive → player rose (improved rank numerically lower → higher in standings).
  Negative → player dropped.
  Zero     → first appearance or unchanged.

These functions take a list of snapshot dicts ordered by numero_jornada (asc).
Each dict must contain at least: {"numero_jornada": int, "posicion": int}.
"""


def compute_delta_posicion(history: list[dict]) -> int:
    """
    Compute the delta between the last two jornadas in the player's snapshot history.

    SEMANTIC convention: delta = anterior_posicion - nueva_posicion.
    - Positive → player rose (e.g., went from rank 3 to rank 1 → delta=+2).
    - Negative → player dropped (e.g., went from rank 1 to rank 3 → delta=-2).
    - Zero     → same rank, or first/only appearance (decision #4).

    Args:
        history: list of snapshot dicts ordered by numero_jornada asc.
                 Each dict must contain {"numero_jornada": int, "posicion": int}.

    Returns:
        int: delta using SEMANTIC convention. 0 if history has 0 or 1 entries.
    """
    if len(history) < 2:
        return 0
    anterior = history[-2]["posicion"]
    nueva = history[-1]["posicion"]
    return anterior - nueva


def compute_racha(history: list[dict]) -> int:
    """
    Count consecutive jornadas from the end where posicion STRICTLY improved
    (numerically decreased) compared to the previous jornada.

    A stay (same posicion) or a drop (higher number = worse rank) breaks the streak.
    Decision #2: strictly improving only.

    Args:
        history: list of snapshot dicts ordered by numero_jornada asc.

    Returns:
        int >= 0. Returns 0 for empty or single-entry history.
    """
    if len(history) < 2:
        return 0

    streak = 0
    # Walk backwards from the last entry
    for i in range(len(history) - 1, 0, -1):
        if history[i]["posicion"] < history[i - 1]["posicion"]:
            streak += 1
        else:
            break
    return streak


def compute_lider_desde_jornada(history: list[dict]) -> int | None:
    """
    Return the numero_jornada of the FIRST snapshot in the current contiguous
    block of posicion=1 at the end of history.

    Decision #3 (last ascent): if the player lost #1 and regained it later,
    the returned jornada is the one where they most recently ascended to #1.

    Args:
        history: list of snapshot dicts ordered by numero_jornada asc.

    Returns:
        int | None. None if the player is not currently at posicion=1.
    """
    if not history:
        return None

    # Player must be currently at posicion=1
    if history[-1]["posicion"] != 1:
        return None

    # Walk backwards to find the start of the current contiguous block of posicion=1
    first_jornada = history[-1]["numero_jornada"]
    for i in range(len(history) - 2, -1, -1):
        if history[i]["posicion"] == 1:
            first_jornada = history[i]["numero_jornada"]
        else:
            break

    return first_jornada
