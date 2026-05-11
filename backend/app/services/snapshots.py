"""
Snapshot generation and replay service.

Responsibilities:
- _generar_snapshots_para_reunion: compute cumulative ranking up to a given
  reunion and persist PosicionSnapshot rows for all inscritos with asistencias > 0.
- _regenerar_snapshots_temporada: delete all snapshots for a temporada and
  replay for every reunion in numero_jornada order (delete-all + full replay).

Both helpers are transactional — they MUST be called inside an open transaction
(before db.commit()) in the calling service.

The public get_ranking_narrativo function (Phase E) will be added here in PR 3.
"""

from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.posicion_snapshot import PosicionSnapshot
from app.models.reunion import Reunion
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
