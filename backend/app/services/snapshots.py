"""
Snapshot generation, replay, and narrative read service.

Responsibilities:
- _generar_snapshots_para_reunion: compute cumulative ranking up to a given
  reunion and persist PosicionSnapshot rows for all inscritos with asistencias > 0.
- _regenerar_snapshots_temporada: delete all snapshots for a temporada and
  replay for every reunion in numero_jornada order (delete-all + full replay).
- get_ranking_narrativo: on-read computation of narrative fields (delta, racha,
  lider_desde_jornada) for the current active temporada.

Both write helpers are transactional — they MUST be called inside an open
transaction (before db.commit()) in the calling service.
"""

from collections import defaultdict

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.posicion_snapshot import PosicionSnapshot
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada
from app.services.consultas import get_inscripciones, get_todas_posiciones
from app.services.narrativa import (
    compute_delta_posicion,
    compute_lider_desde_jornada,
    compute_racha,
)
from app.services.ranking import assign_competition_ranks, calcular_ranking


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_inscripciones_for_temporada(db: Session, temporada_id: int) -> list[dict]:
    """Load all inscritos for the temporada as dicts compatible with calcular_ranking."""
    rows = (
        db.query(Jugador)
        .join(Inscripcion, Inscripcion.id_jugador == Jugador.id)
        .filter(Inscripcion.id_temporada == temporada_id)
        .all()
    )
    return [{"id_jugador": j.id, "nombre": j.nombre} for j in rows]


def _get_posiciones_up_to_reunion(
    db: Session, temporada_id: int, hasta_numero_jornada: int
) -> list[dict]:
    """
    Load all Posicion rows for the temporada whose reunion.numero_jornada
    is <= hasta_numero_jornada. Returns dicts compatible with calcular_ranking.
    """
    reunion_ids = [
        r.id
        for r in db.query(Reunion.id)
        .filter(
            Reunion.id_temporada == temporada_id,
            Reunion.numero_jornada <= hasta_numero_jornada,
        )
        .all()
    ]
    if not reunion_ids:
        return []

    posiciones = (
        db.query(Posicion)
        .filter(Posicion.id_reunion.in_(reunion_ids))
        .all()
    )
    return [
        {
            "id_jugador": p.id_jugador,
            "es_invitado": p.es_invitado,
            "puntos": p.puntos,
        }
        for p in posiciones
    ]


def _generar_snapshots_para_reunion(
    db: Session, temporada_id: int, reunion_id: int
) -> None:
    """
    Compute cumulative ranking up to (and including) the given reunion and
    insert one PosicionSnapshot per inscrito with asistencias > 0.

    MUST be called inside an open transaction AFTER db.flush() has made
    the Posicion rows for this reunion visible to queries.

    Invitados are never stored — calcular_ranking already excludes them.
    """
    reunion = db.query(Reunion).filter(Reunion.id == reunion_id).first()
    if reunion is None:
        raise ValueError(f"Reunion {reunion_id} not found")

    inscripciones = _get_inscripciones_for_temporada(db, temporada_id)
    posiciones = _get_posiciones_up_to_reunion(db, temporada_id, reunion.numero_jornada)

    ranking = calcular_ranking(inscripciones, posiciones)
    ranked = assign_competition_ranks(ranking)

    for entry in ranked:
        # calcular_ranking already filters asistencias > 0; guard is implicit.
        snapshot = PosicionSnapshot(
            id_temporada=temporada_id,
            id_reunion=reunion_id,
            id_jugador=entry["id_jugador"],
            posicion=entry["posicion"],
            puntos_acumulados=entry["puntos"],
        )
        db.add(snapshot)


def _regenerar_snapshots_temporada(db: Session, temporada_id: int) -> None:
    """
    Delete ALL existing snapshot rows for the temporada, then replay
    _generar_snapshots_para_reunion for each reunion in numero_jornada order.

    MUST be called inside an open transaction AFTER db.flush() has made
    the updated Posicion rows visible.
    """
    # Delete all existing snapshots for this temporada
    db.query(PosicionSnapshot).filter(
        PosicionSnapshot.id_temporada == temporada_id
    ).delete(synchronize_session=False)

    # Replay for every reunion ordered by numero_jornada
    reuniones = (
        db.query(Reunion)
        .filter(Reunion.id_temporada == temporada_id)
        .order_by(Reunion.numero_jornada)
        .all()
    )

    for reunion in reuniones:
        _generar_snapshots_para_reunion(db, temporada_id, reunion.id)


# ---------------------------------------------------------------------------
# Public read: narrative ranking
# ---------------------------------------------------------------------------


def get_ranking_narrativo(db: Session) -> list[dict]:
    """
    Return the current ranking of the active temporada enriched with
    delta_posicion, racha, and lider_desde_jornada per player.

    Returns an empty list when there is no active temporada or no snapshots exist.

    delta_posicion uses the SEMANTIC convention (decisions-supplement #98):
      delta = anterior_posicion - nueva_posicion
      Positive → rose. Negative → dropped. Zero → first appearance or unchanged.
    """
    # 1. Resolve active temporada — return [] if none exists
    temporada = (
        db.query(Temporada)
        .filter(Temporada.estado == EstadoTemporada.activa)
        .first()
    )
    if not temporada:
        return []

    # 2. Load inscripciones and all posiciones for the current ranking
    inscripciones = get_inscripciones(db, temporada.id)
    posiciones = get_todas_posiciones(db, temporada.id)

    ranking = calcular_ranking(inscripciones, posiciones)
    if not ranking:
        return []

    ranked_actual = assign_competition_ranks(ranking)

    # Build foto_url map
    foto_map = {i["id_jugador"]: i["foto_url"] for i in inscripciones}

    # 3. Load full snapshot history for the temporada — one query with JOIN on reuniones
    rows = (
        db.query(
            PosicionSnapshot.id_jugador,
            PosicionSnapshot.posicion,
            Reunion.numero_jornada,
        )
        .join(Reunion, Reunion.id == PosicionSnapshot.id_reunion)
        .filter(PosicionSnapshot.id_temporada == temporada.id)
        .order_by(PosicionSnapshot.id_jugador, Reunion.numero_jornada)
        .all()
    )

    # 4. Group history by id_jugador (already ordered by numero_jornada)
    history_by_jugador: dict[int, list[dict]] = defaultdict(list)
    for id_jugador, posicion, numero_jornada in rows:
        history_by_jugador[id_jugador].append(
            {"numero_jornada": numero_jornada, "posicion": posicion}
        )

    # 5. Build enriched entries
    result: list[dict] = []
    for entry in ranked_actual:
        pid = entry["id_jugador"]
        history = history_by_jugador.get(pid, [])

        result.append(
            {
                "id_jugador": pid,
                "nombre": entry["nombre"],
                "foto_url": foto_map.get(pid),
                "puntos": entry["puntos"],
                "asistencias": entry["asistencias"],
                "posicion": entry["posicion"],
                "delta_posicion": compute_delta_posicion(history),
                "racha": compute_racha(history),
                "lider_desde_jornada": compute_lider_desde_jornada(history),
            }
        )

    return result


def get_ranking_narrativo_cerrada(db: Session) -> dict | None:
    """
    Return the ranking + champion summary for the most recently closed temporada.

    "Most recent" is resolved by ORDER BY fecha_cierre DESC NULLS LAST, id DESC:
      - Seasons with a concrete fecha_cierre rank before NULL ones (post-migration preference).
      - Among NULLs (bulk-imported historical seasons), higher id wins.

    Returns None when no closed temporada exists (caller raises 404).

    The returned dict has shape:
      temporada_id, temporada_nombre, fecha_cierre, campeon (None or dict), ranking (list).

    Each ranking entry includes: posicion, id_jugador, nombre, foto_url, puntos,
    asistencias, promedio, racha — but NO delta_posicion and NO lider_desde_jornada
    (design decision D5: those fields are only meaningful for a live season).
    """
    from sqlalchemy import nullslast

    # 1. Resolve "última cerrada" — NULLS LAST on fecha_cierre, id DESC as tiebreaker
    temporada = (
        db.query(Temporada)
        .filter(Temporada.estado == EstadoTemporada.cerrada)
        .order_by(nullslast(desc(Temporada.fecha_cierre)), desc(Temporada.id))
        .first()
    )
    if temporada is None:
        return None

    # 2. Load inscripciones + all posiciones for this temporada
    inscripciones = get_inscripciones(db, temporada.id)
    posiciones = get_todas_posiciones(db, temporada.id)

    ranking = calcular_ranking(inscripciones, posiciones)
    ranked_actual = assign_competition_ranks(ranking)

    # Build foto_url map from inscripciones
    foto_map = {i["id_jugador"]: i["foto_url"] for i in inscripciones}

    # 3. Load full snapshot history for this temporada (same query as get_ranking_narrativo)
    rows = (
        db.query(
            PosicionSnapshot.id_jugador,
            PosicionSnapshot.posicion,
            Reunion.numero_jornada,
        )
        .join(Reunion, Reunion.id == PosicionSnapshot.id_reunion)
        .filter(PosicionSnapshot.id_temporada == temporada.id)
        .order_by(PosicionSnapshot.id_jugador, Reunion.numero_jornada)
        .all()
    )

    # 4. Group history by id_jugador
    history_by_jugador: dict[int, list[dict]] = defaultdict(list)
    for id_jugador, posicion, numero_jornada in rows:
        history_by_jugador[id_jugador].append(
            {"numero_jornada": numero_jornada, "posicion": posicion}
        )

    # 5. Build entries — only racha, no delta_posicion, no lider_desde_jornada
    entries: list[dict] = []
    for entry in ranked_actual:
        pid = entry["id_jugador"]
        history = history_by_jugador.get(pid, [])
        asistencias = entry["asistencias"]
        promedio = round(entry["puntos"] / asistencias, 1) if asistencias else 0.0
        entries.append(
            {
                "posicion": entry["posicion"],
                "id_jugador": pid,
                "nombre": entry["nombre"],
                "foto_url": foto_map.get(pid),
                "puntos": entry["puntos"],
                "asistencias": asistencias,
                "promedio": promedio,
                "racha": compute_racha(history),
            }
        )

    # 6. Build embedded campeon dict — None when campeon_id is NULL (tie not resolved)
    campeon_dict = None
    if temporada.campeon_id is not None:
        champ_entry = next(
            (e for e in entries if e["id_jugador"] == temporada.campeon_id),
            None,
        )
        if champ_entry is not None:
            campeon_dict = {
                "id": champ_entry["id_jugador"],
                "nombre": champ_entry["nombre"],
                "foto_url": champ_entry["foto_url"],
                "puntos": champ_entry["puntos"],
                "asistencias": champ_entry["asistencias"],
                "promedio": champ_entry["promedio"],
            }

    return {
        "temporada_id": temporada.id,
        "temporada_nombre": temporada.nombre,
        "fecha_cierre": temporada.fecha_cierre,
        "campeon": campeon_dict,
        "ranking": entries,
    }
