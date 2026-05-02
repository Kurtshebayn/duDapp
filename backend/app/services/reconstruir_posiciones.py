"""Pure position-reconstruction function for CSV imports.

No database access, no I/O, no side effects.
Implements REQ-IMP-17 through REQ-IMP-21 from the bulk-import-temporadas spec.
"""
from dataclasses import dataclass


@dataclass
class PosicionReconstruida:
    posicion: int
    puntos: int
    nombre_jugador: str | None  # None when es_invitado=True
    es_invitado: bool


def reconstruir_posiciones_de_reunion(
    scores: dict[str, int],
) -> list[PosicionReconstruida]:
    """Reconstruct ordered position rows from a {player_name: score} map.

    Algorithm (implements REQ-IMP-17..REQ-IMP-21):
    1. Filter out players with score == 0 (absent — REQ-IMP-18).
    2. Raise ValueError if any score is outside [1, 15].
    3. Raise ValueError if two or more present players share the same non-zero score.
    4. Sort present players by score descending.
    5. Walk from expected_score=15 downward:
       - If expected_score matches next player's score → emit a player row.
       - If expected_score is higher than next player's score → emit a guest row
         for the missing score (REQ-IMP-20) and continue decrementing.
    6. Returns [] when all players are absent (REQ-IMP-18 + NFR-IMP-01 separation
       of concerns; orchestrator handles the semantic 'all absent' error).

    Raises:
        ValueError: on duplicate non-zero scores, negative scores, or scores > 15.
    """
    # Separate absent players (score == 0) from present players
    present = {name: s for name, s in scores.items() if s != 0}

    if not present:
        return []

    # Validate score range for present players
    for name, s in present.items():
        if s < 1 or s > 15:
            raise ValueError(
                f"Score fuera de rango [1, 15] para '{name}': {s}"
            )

    # Validate no duplicate scores among present players
    score_values = list(present.values())
    if len(score_values) != len(set(score_values)):
        # Find the duplicate(s)
        seen = set()
        for s in score_values:
            if s in seen:
                raise ValueError(
                    f"Puntaje duplicado entre jugadores presentes: {s}"
                )
            seen.add(s)

    # Sort present players by descending score
    sorted_players = sorted(present.items(), key=lambda kv: kv[1], reverse=True)

    result: list[PosicionReconstruida] = []
    position_counter = 1
    expected_score = 15

    player_idx = 0
    while player_idx < len(sorted_players):
        name, score = sorted_players[player_idx]

        if expected_score > score:
            # Gap: insert a guest row for the missing expected score
            result.append(
                PosicionReconstruida(
                    posicion=position_counter,
                    puntos=expected_score,
                    nombre_jugador=None,
                    es_invitado=True,
                )
            )
            position_counter += 1
            expected_score -= 1
        else:
            # expected_score == score → emit the player row
            result.append(
                PosicionReconstruida(
                    posicion=position_counter,
                    puntos=score,
                    nombre_jugador=name,
                    es_invitado=False,
                )
            )
            position_counter += 1
            expected_score -= 1
            player_idx += 1

    return result
