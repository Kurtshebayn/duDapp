"""
Funciones puras de cálculo histórico cross-temporadas + orquestadores de DB.

Todos los inputs de las funciones puras son listas de dicts planos
(sin instancias SQLAlchemy).
jugadores_map: dict[int, {"nombre": str, "foto_url": str | None}]

Convención de salida:
  - Cada función retorna una lista de dicts con claves que coinciden
    exactamente con los campos de los schemas Pydantic correspondientes.
  - Orden por defecto: métrica DESC, nombre ASC (tie-breaker C6).
  - Jugadores con métrica == 0 NO aparecen en el resultado.

Orquestadores (requieren DB session):
  - get_historico_resumen(db) → dict (shape HistoricoResumenResponse)
  - get_head_to_head(db, jugador_id) → dict (shape HeadToHeadResponse)
"""

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada


# ---------------------------------------------------------------------------
# M1 — Puntos totales
# ---------------------------------------------------------------------------


def compute_puntos_totales(
    posiciones: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Suma de puntos por jugador. Orden: puntos DESC, nombre ASC."""
    totales: dict[int, int] = defaultdict(int)

    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        totales[pid] += pos["puntos"]

    resultado = []
    for pid, puntos in totales.items():
        if puntos == 0:
            continue
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "puntos": puntos,
            }
        )

    resultado.sort(key=lambda x: (-x["puntos"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# M2 — Victorias (posicion == 1)
# ---------------------------------------------------------------------------


def compute_victorias(
    posiciones: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Conteo de posicion==1 por jugador. Filtra >0. Orden: victorias DESC, nombre ASC."""
    victorias: dict[int, int] = defaultdict(int)

    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        if pos["posicion"] == 1:
            victorias[pid] += 1

    resultado = []
    for pid, count in victorias.items():
        if count == 0:
            continue
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "victorias": count,
            }
        )

    resultado.sort(key=lambda x: (-x["victorias"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# M3 — Campeones de temporada
# ---------------------------------------------------------------------------


def compute_campeones(
    temporadas_data: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Conteo de campeonatos por jugador. Ignora temporadas con campeon_id=None (C5).
    Orden: campeonatos DESC, nombre ASC."""
    campeonatos: dict[int, int] = defaultdict(int)

    for t in temporadas_data:
        cid = t.get("campeon_id")
        if cid is None:
            continue
        campeonatos[cid] += 1

    resultado = []
    for pid, count in campeonatos.items():
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "campeonatos": count,
            }
        )

    resultado.sort(key=lambda x: (-x["campeonatos"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# M4 — Asistencias
# ---------------------------------------------------------------------------


def compute_asistencias(
    posiciones: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Conteo de filas de Posicion por jugador. Filtra >0.
    Orden: asistencias DESC, nombre ASC."""
    conteo: dict[int, int] = defaultdict(int)

    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        conteo[pid] += 1

    resultado = []
    for pid, count in conteo.items():
        if count == 0:
            continue
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "asistencias": count,
            }
        )

    resultado.sort(key=lambda x: (-x["asistencias"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# Shared streak helper
# ---------------------------------------------------------------------------


def _compute_streak(
    posiciones: list[dict],
    reuniones: list[dict],
    temporadas: list[dict],
    jugadores_map: dict,
    win_condition,  # callable(pos_dict) -> bool
) -> list[dict]:
    """
    Generic streak computation for both M5 (victories) and M6 (attendance).

    Algorithm:
      1. Build temporada_map: {id -> dict with nombre, fecha_inicio}.
      2. Build reunion_meta: {reunion_id -> {id_temporada, numero_jornada}}.
      3. Build per-player win-set: set of reunion_ids where win_condition holds.
      4. For each player, iterate the global ordered timeline (reuniones list):
         - if reunion in player's win-set: increment current streak, track start.
         - else: reset current streak.
         - On update: if current_len > best_len, OR current_len == best_len (tie → most recent):
           update best.
      5. Build result dicts using reunion_meta + temporada_map for metadata.
      6. Return players with best_len > 0, sorted by (longitud DESC, nombre ASC).

    C7 implemented: on tie, the most recently-ending streak wins (later position in
    the ordered timeline overwrites the previous best because we check >= not just >).
    """
    # Build temporada lookup
    temporada_map = {t["id"]: t for t in temporadas}

    # Build reunion metadata lookup
    reunion_meta: dict[int, dict] = {}
    for r in reuniones:
        reunion_meta[r["id"]] = {
            "id_temporada": r["id_temporada"],
            "numero_jornada": r["numero_jornada"],
        }

    # Build per-player win set
    win_sets: dict[int, set] = defaultdict(set)
    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        if win_condition(pos):
            win_sets[pid].add(pos["id_reunion"])

    # All unique players across posiciones (to handle those with 0 wins)
    all_players: set[int] = set()
    for pos in posiciones:
        if pos["id_jugador"] is not None:
            all_players.add(pos["id_jugador"])

    # Ordered list of reunion ids (already ordered by caller)
    ordered_reunion_ids = [r["id"] for r in reuniones]

    resultado = []
    for pid in sorted(all_players):
        player_wins = win_sets[pid]

        best_len = 0
        best_start_idx = -1
        best_end_idx = -1

        current_len = 0
        current_start_idx = -1

        for idx, rid in enumerate(ordered_reunion_ids):
            if rid in player_wins:
                if current_len == 0:
                    current_start_idx = idx
                current_len += 1
                current_end_idx = idx

                # C7: update best if strictly better OR equal (keeps most recent)
                if current_len >= best_len:
                    best_len = current_len
                    best_start_idx = current_start_idx
                    best_end_idx = current_end_idx
            else:
                current_len = 0
                current_start_idx = -1

        if best_len == 0:
            continue

        start_rid = ordered_reunion_ids[best_start_idx]
        end_rid = ordered_reunion_ids[best_end_idx]

        start_meta = reunion_meta[start_rid]
        end_meta = reunion_meta[end_rid]

        t_inicio = temporada_map[start_meta["id_temporada"]]
        t_fin = temporada_map[end_meta["id_temporada"]]

        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "longitud": best_len,
                "temporada_inicio": {
                    "id": t_inicio["id"],
                    "nombre": t_inicio["nombre"],
                    "fecha_inicio": t_inicio["fecha_inicio"],
                },
                "jornada_inicio": start_meta["numero_jornada"],
                "temporada_fin": {
                    "id": t_fin["id"],
                    "nombre": t_fin["nombre"],
                    "fecha_inicio": t_fin["fecha_inicio"],
                },
                "jornada_fin": end_meta["numero_jornada"],
            }
        )

    resultado.sort(key=lambda x: (-x["longitud"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# M5 — Racha de victorias consecutivas
# ---------------------------------------------------------------------------


def compute_racha_victorias(
    posiciones: list[dict],
    reuniones: list[dict],
    temporadas: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Racha máxima de posicion==1 consecutivas por jugador (cruza temporadas).
    C7: en empate de longitud, devuelve la más reciente.
    Filtra streaks con longitud < 2 (Change B).
    Orden: longitud DESC, nombre ASC."""
    result = _compute_streak(
        posiciones,
        reuniones,
        temporadas,
        jugadores_map,
        win_condition=lambda pos: pos["posicion"] == 1,
    )
    return [r for r in result if r["longitud"] >= 2]


# ---------------------------------------------------------------------------
# M6 — Racha de asistencia perfecta
# ---------------------------------------------------------------------------


def compute_racha_asistencia(
    posiciones: list[dict],
    reuniones: list[dict],
    temporadas: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Racha máxima de asistencia perfecta por jugador (cruza temporadas).
    Cualquier reunión sin fila de Posicion para el jugador rompe la racha (C10).
    C7: en empate de longitud, devuelve la más reciente.
    Filtra streaks con longitud < 2 (Change C). Retorna top 5.
    Orden: longitud DESC, nombre ASC."""
    result = _compute_streak(
        posiciones,
        reuniones,
        temporadas,
        jugadores_map,
        win_condition=lambda pos: True,  # Any Posicion row counts as attended
    )
    return [r for r in result if r["longitud"] >= 2][:5]


# ---------------------------------------------------------------------------
# M10 — Racha de inasistencias consecutivas
# ---------------------------------------------------------------------------


def compute_racha_inasistencia(
    posiciones: list[dict],
    reuniones: list[dict],
    temporadas: list[dict],
    inscripciones: "set[tuple[int, int]]",
    jugadores_map: dict,
) -> list[dict]:
    """Racha máxima de inasistencias consecutivas por jugador.

    Eligibility (prerequisite for M10):
      A player is eligible only if they have >= 1 asistencia in EACH closed temporada.
      If a player is enrolled (inscripcion exists) in a temporada and attended 0 reuniones,
      they are INELIGIBLE. If a player is NOT enrolled in some temporada, they are also
      ineligible for M10 (we require participation in every closed temporada).

    Streak computation:
      Iterates reuniones chronologically. For each eligible player, for each reunión:
        - If the player IS enrolled in the reunión's temporada AND has NO posicion row
          → inasistencia: streak counter increments.
        - If the player HAS a posicion row for the reunión → streak resets to 0.
        - If the player is NOT enrolled in the reunión's temporada → skipped entirely
          (does not count as inasistencia, does not reset the streak). This case is rare
          for eligible players (eligibility requires >=1 asistencia in every temporada,
          so enrollment in every temporada is implicitly required).

    C7 (tie-break): when two streaks of equal length exist for the same player,
      the most recent one is returned (>= update rule).

    Filters and limits:
      - Drop players with longitud < 2.
      - Sort by (longitud desc, nombre asc).
      - Slice top 5.

    Args:
      posiciones: list of dicts {id_jugador, id_reunion, posicion, puntos}
      reuniones: list of dicts {id, id_temporada, numero_jornada} — already ordered chronologically
      temporadas: list of dicts {id, nombre, fecha_inicio, campeon_id} — closed temporadas only
      inscripciones: set of (id_jugador, id_temporada) tuples — closed temporadas only
      jugadores_map: {id_jugador: {nombre, foto_url}}

    Returns:
      list of dicts matching RachaItem schema shape.
    """
    if not temporadas or not reuniones:
        return []

    temporada_ids = {t["id"] for t in temporadas}
    temporada_map = {t["id"]: t for t in temporadas}

    # Build reunion metadata lookup
    reunion_meta: dict[int, dict] = {}
    for r in reuniones:
        reunion_meta[r["id"]] = {
            "id_temporada": r["id_temporada"],
            "numero_jornada": r["numero_jornada"],
        }

    # Build attended set: {(id_jugador, id_reunion)} for quick lookup
    attended: set[tuple[int, int]] = set()
    all_jugadores: set[int] = set()
    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        attended.add((pid, pos["id_reunion"]))
        all_jugadores.add(pid)

    # Build asistencias per jugador per temporada: {(id_jugador, id_temporada): count}
    asistencias_por_temporada: dict[tuple[int, int], int] = defaultdict(int)
    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        rid = pos["id_reunion"]
        t_id = reunion_meta.get(rid, {}).get("id_temporada")
        if t_id is not None:
            asistencias_por_temporada[(pid, t_id)] += 1

    # Eligibility filter: player must have >=1 asistencia in EACH closed temporada
    eligible_players: set[int] = set()
    for pid in all_jugadores:
        eligible = True
        for t_id in temporada_ids:
            if asistencias_por_temporada[(pid, t_id)] == 0:
                eligible = False
                break
        if eligible:
            eligible_players.add(pid)

    if not eligible_players:
        return []

    # Ordered list of reunion ids (already ordered by caller)
    ordered_reunion_ids = [r["id"] for r in reuniones]

    resultado = []
    for pid in sorted(eligible_players):
        best_len = 0
        best_start_idx = -1
        best_end_idx = -1

        current_len = 0
        current_start_idx = -1

        for idx, rid in enumerate(ordered_reunion_ids):
            t_id = reunion_meta[rid]["id_temporada"]

            # Check if player is enrolled in this temporada
            if (pid, t_id) not in inscripciones:
                # Not enrolled → skip (neither count nor reset)
                continue

            # Player is enrolled in this temporada
            if (pid, rid) not in attended:
                # Inasistencia: streak increments
                if current_len == 0:
                    current_start_idx = idx
                current_len += 1
                current_end_idx = idx

                # C7: update best if strictly better OR equal (keeps most recent)
                if current_len >= best_len:
                    best_len = current_len
                    best_start_idx = current_start_idx
                    best_end_idx = current_end_idx
            else:
                # Attended → streak resets
                current_len = 0
                current_start_idx = -1

        if best_len < 2:
            continue

        start_rid = ordered_reunion_ids[best_start_idx]
        end_rid = ordered_reunion_ids[best_end_idx]

        start_meta = reunion_meta[start_rid]
        end_meta = reunion_meta[end_rid]

        t_inicio = temporada_map[start_meta["id_temporada"]]
        t_fin = temporada_map[end_meta["id_temporada"]]

        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "longitud": best_len,
                "temporada_inicio": {
                    "id": t_inicio["id"],
                    "nombre": t_inicio["nombre"],
                    "fecha_inicio": t_inicio["fecha_inicio"],
                },
                "jornada_inicio": start_meta["numero_jornada"],
                "temporada_fin": {
                    "id": t_fin["id"],
                    "nombre": t_fin["nombre"],
                    "fecha_inicio": t_fin["fecha_inicio"],
                },
                "jornada_fin": end_meta["numero_jornada"],
            }
        )

    resultado.sort(key=lambda x: (-x["longitud"], x["nombre"]))
    return resultado[:5]


# ---------------------------------------------------------------------------
# M7 — Promedios
# ---------------------------------------------------------------------------


def compute_promedios(
    posiciones: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """promedio = puntos_totales / asistencias. Redondea a 2 decimales.
    Filtra jugadores con asistencias == 0. Orden: promedio DESC, nombre ASC."""
    totales: dict[int, list] = defaultdict(lambda: [0, 0])  # [puntos, asistencias]

    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        totales[pid][0] += pos["puntos"]
        totales[pid][1] += 1

    resultado = []
    for pid, (puntos, asistencias) in totales.items():
        if asistencias <= 8:
            continue
        promedio = round(puntos / asistencias, 2)
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "puntos": puntos,
                "asistencias": asistencias,
                "promedio": promedio,
            }
        )

    resultado.sort(key=lambda x: (-x["promedio"], x["nombre"]))
    return resultado


# ---------------------------------------------------------------------------
# M9 — Podios
# ---------------------------------------------------------------------------


def compute_podios(
    posiciones: list[dict],
    jugadores_map: dict,
) -> list[dict]:
    """Por jugador: oro (pos==1), plata (pos==2), bronce (pos==3), total = sum.
    Filtra total>0. Orden: total DESC, oro DESC, plata DESC, nombre ASC."""
    podios: dict[int, dict] = defaultdict(lambda: {"oro": 0, "plata": 0, "bronce": 0})

    for pos in posiciones:
        pid = pos["id_jugador"]
        if pid is None:
            continue
        p = pos["posicion"]
        if p == 1:
            podios[pid]["oro"] += 1
        elif p == 2:
            podios[pid]["plata"] += 1
        elif p == 3:
            podios[pid]["bronce"] += 1

    resultado = []
    for pid, counts in podios.items():
        total = counts["oro"] + counts["plata"] + counts["bronce"]
        if total == 0:
            continue
        info = jugadores_map.get(pid, {"nombre": "", "foto_url": None})
        resultado.append(
            {
                "id_jugador": pid,
                "nombre": info["nombre"],
                "foto_url": info.get("foto_url"),
                "oro": counts["oro"],
                "plata": counts["plata"],
                "bronce": counts["bronce"],
                "total": total,
            }
        )

    resultado.sort(
        key=lambda x: (-x["total"], -x["oro"], -x["plata"], x["nombre"])
    )
    return resultado


# ---------------------------------------------------------------------------
# M8 — Head-to-Head (pure row computation)
# ---------------------------------------------------------------------------


def compute_head_to_head_row(
    jugador_id: int,
    nombre: str,
    foto_url: "str | None",
    posiciones: list[dict],
    jugadores_map: dict,
) -> dict:
    """Computa el row de enfrentamientos directos del jugador target contra todos
    los rivales con quienes compartió al menos una reunión (C8).

    Lógica:
      - Agrupa posiciones por id_reunion.
      - Para cada reunión donde el target tiene fila:
        - Por cada otro jugador en esa reunión:
          - target.posicion < rival.posicion → victoria del target
          - target.posicion > rival.posicion → derrota del target
          - Mismo posicion (teóricamente imposible por modelo) → ignorado.
      - Excluye rivales con reuniones_compartidas == 0 (C8, por construcción).
      - Orden rivales: reuniones_compartidas DESC, rival_nombre ASC.

    Retorna:
      {jugador_id, nombre, foto_url, rivales: [HeadToHeadRivalItem dicts]}
    """
    # Group all posicion rows by id_reunion
    by_reunion: dict[int, list[dict]] = defaultdict(list)
    for pos in posiciones:
        if pos["id_jugador"] is not None:
            by_reunion[pos["id_reunion"]].append(pos)

    # Accumulate rival stats
    rival_stats: dict[int, dict] = defaultdict(
        lambda: {"victorias": 0, "derrotas": 0, "reuniones_compartidas": 0}
    )

    for rid, rows in by_reunion.items():
        # Find target's row in this meeting
        target_row = None
        for row in rows:
            if row["id_jugador"] == jugador_id:
                target_row = row
                break

        if target_row is None:
            continue  # Target not in this meeting — skip

        target_pos = target_row["posicion"]

        for row in rows:
            rival_id = row["id_jugador"]
            if rival_id == jugador_id:
                continue  # skip self

            rival_pos = row["posicion"]
            if target_pos == rival_pos:
                # Impossible by model, but guard anyway — skip tie
                continue

            rival_stats[rival_id]["reuniones_compartidas"] += 1
            if target_pos < rival_pos:
                rival_stats[rival_id]["victorias"] += 1
            else:
                rival_stats[rival_id]["derrotas"] += 1

    # Build rival list — exclude those with reuniones_compartidas == 0
    rivales = []
    for rival_id, stats in rival_stats.items():
        if stats["reuniones_compartidas"] == 0:
            continue
        rival_info = jugadores_map.get(rival_id, {"nombre": "", "foto_url": None})
        rivales.append(
            {
                "rival_id": rival_id,
                "rival_nombre": rival_info["nombre"],
                "rival_foto_url": rival_info.get("foto_url"),
                "victorias": stats["victorias"],
                "derrotas": stats["derrotas"],
                "reuniones_compartidas": stats["reuniones_compartidas"],
            }
        )

    rivales.sort(key=lambda x: (-x["reuniones_compartidas"], x["rival_nombre"]))

    return {
        "jugador_id": jugador_id,
        "nombre": nombre,
        "foto_url": foto_url,
        "rivales": rivales,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_resumen() -> dict:
    """Returns HistoricoResumenResponse-shaped dict with all empty lists."""
    return {
        "puntos_totales": [],
        "victorias": [],
        "campeones": [],
        "asistencias": [],
        "racha_victorias": [],
        "racha_asistencia": [],
        "promedios": [],
        "podios": [],
        "racha_inasistencia": [],
    }


# ---------------------------------------------------------------------------
# T-33 — Orchestrator: GET /historico/resumen
# ---------------------------------------------------------------------------


def get_historico_resumen(db: Session) -> dict:
    """
    Composes M1–M9 resumen from closed temporadas.

    Strategy (FETCH-ONCE / COMPUTE-IN-PYTHON):
      Step 1 — fetch closed temporadas ordered deterministically (R2).
      Step 2 — fetch jugadores catalog.
      Step 3 — fetch reuniones JOIN temporada for chronological global order.
      Step 4 — fetch posiciones (non-guest, non-null player).
      Step 5 — call all 8 compute_* pure functions and compose response.
    """
    # Step 1: fetch closed temporadas, deterministic order (fecha_inicio ASC, id ASC)
    temporadas = (
        db.query(Temporada)
        .filter(Temporada.estado == EstadoTemporada.cerrada)
        .order_by(Temporada.fecha_inicio.asc(), Temporada.id.asc())
        .all()
    )
    if not temporadas:
        return _empty_resumen()

    temporada_ids = [t.id for t in temporadas]

    # Convert SQLAlchemy Temporada objects to dicts for pure functions
    temporadas_dicts = [
        {
            "id": t.id,
            "nombre": t.nombre,
            "fecha_inicio": t.fecha_inicio,
            "campeon_id": t.campeon_id,
        }
        for t in temporadas
    ]

    # Step 2: fetch jugadores catalog
    jugadores = db.query(Jugador).all()
    jugadores_map = {
        j.id: {"nombre": j.nombre, "foto_url": j.foto_url}
        for j in jugadores
    }

    # Step 3: fetch reuniones JOIN temporada, ordered chronologically
    # (fecha_inicio ASC, temporada.id ASC, numero_jornada ASC)
    reunion_rows = (
        db.query(Reunion, Temporada.fecha_inicio, Temporada.id.label("t_id"))
        .join(Temporada, Reunion.id_temporada == Temporada.id)
        .filter(Reunion.id_temporada.in_(temporada_ids))
        .order_by(
            Temporada.fecha_inicio.asc(),
            Temporada.id.asc(),
            Reunion.numero_jornada.asc(),
        )
        .all()
    )
    reunion_dicts = [
        {
            "id": row.Reunion.id,
            "id_temporada": row.Reunion.id_temporada,
            "numero_jornada": row.Reunion.numero_jornada,
        }
        for row in reunion_rows
    ]
    reunion_ids = [r["id"] for r in reunion_dicts]

    # Step 4: fetch posiciones (non-guest, non-null player)
    if reunion_ids:
        posiciones = (
            db.query(Posicion)
            .filter(
                Posicion.id_reunion.in_(reunion_ids),
                Posicion.es_invitado == False,  # noqa: E712
                Posicion.id_jugador.isnot(None),
            )
            .all()
        )
        posicion_dicts = [
            {
                "id_jugador": p.id_jugador,
                "id_reunion": p.id_reunion,
                "posicion": p.posicion,
                "puntos": p.puntos,
            }
            for p in posiciones
        ]
    else:
        posicion_dicts = []

    # Step 5: fetch inscripciones for closed temporadas (for M10 eligibility)
    inscripciones_rows = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_temporada.in_(temporada_ids))
        .all()
    )
    # Represent as set of (id_jugador, id_temporada) tuples for O(1) lookup
    inscripciones_set: set[tuple[int, int]] = {
        (i.id_jugador, i.id_temporada) for i in inscripciones_rows
    }

    # Step 6: compose pure-calc results
    return {
        "puntos_totales": compute_puntos_totales(posicion_dicts, jugadores_map),
        "victorias": compute_victorias(posicion_dicts, jugadores_map),
        "campeones": compute_campeones(temporadas_dicts, jugadores_map),
        "asistencias": compute_asistencias(posicion_dicts, jugadores_map),
        "racha_victorias": compute_racha_victorias(
            posicion_dicts, reunion_dicts, temporadas_dicts, jugadores_map
        ),
        "racha_asistencia": compute_racha_asistencia(
            posicion_dicts, reunion_dicts, temporadas_dicts, jugadores_map
        ),
        "promedios": compute_promedios(posicion_dicts, jugadores_map),
        "podios": compute_podios(posicion_dicts, jugadores_map),
        "racha_inasistencia": compute_racha_inasistencia(
            posicion_dicts, reunion_dicts, temporadas_dicts, inscripciones_set, jugadores_map
        ),
    }


# ---------------------------------------------------------------------------
# T-35 — Orchestrator: GET /historico/head-to-head/{jugador_id}
# ---------------------------------------------------------------------------


def get_head_to_head(db: Session, jugador_id: int) -> dict:
    """
    Computes H2H row for the given player against all rivals in closed seasons.

    Raises HTTPException(404) if jugador_id does not exist.
    Returns 200 with rivales=[] if player exists but has no positions in
    closed seasons.
    """
    # 404 guard
    jugador = db.query(Jugador).filter(Jugador.id == jugador_id).first()
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Scope: only closed temporadas
    temporada_ids = [
        t.id
        for t in db.query(Temporada.id)
        .filter(Temporada.estado == EstadoTemporada.cerrada)
        .all()
    ]
    if not temporada_ids:
        return {
            "jugador_id": jugador.id,
            "nombre": jugador.nombre,
            "foto_url": jugador.foto_url,
            "rivales": [],
        }

    # Reunion ids where the target has a Posicion row (in closed temporadas)
    reunion_ids_target = [
        row.id_reunion
        for row in (
            db.query(Posicion.id_reunion)
            .join(Reunion, Posicion.id_reunion == Reunion.id)
            .filter(
                Reunion.id_temporada.in_(temporada_ids),
                Posicion.id_jugador == jugador_id,
                Posicion.es_invitado == False,  # noqa: E712
            )
            .all()
        )
    ]
    if not reunion_ids_target:
        return {
            "jugador_id": jugador.id,
            "nombre": jugador.nombre,
            "foto_url": jugador.foto_url,
            "rivales": [],
        }

    # All posiciones in those reunions (target + rivals, non-guest, non-null)
    posiciones = (
        db.query(Posicion)
        .filter(
            Posicion.id_reunion.in_(reunion_ids_target),
            Posicion.es_invitado == False,  # noqa: E712
            Posicion.id_jugador.isnot(None),
        )
        .all()
    )
    posicion_dicts = [
        {
            "id_jugador": p.id_jugador,
            "id_reunion": p.id_reunion,
            "posicion": p.posicion,
            "puntos": p.puntos,
        }
        for p in posiciones
    ]

    # Jugadores map for rival names / foto_url
    jugadores_map = {j.id: {"nombre": j.nombre, "foto_url": j.foto_url} for j in db.query(Jugador).all()}

    return compute_head_to_head_row(
        jugador_id,
        jugador.nombre,
        jugador.foto_url,
        posicion_dicts,
        jugadores_map,
    )
