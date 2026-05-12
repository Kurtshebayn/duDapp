from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada
from app.services.ranking import calcular_ranking


def _get_temporada_activa(db: Session) -> Temporada:
    temporada = db.query(Temporada).filter(Temporada.estado == EstadoTemporada.activa).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="No hay temporada activa")
    return temporada


def get_inscripciones(db: Session, temporada_id: int) -> list[dict]:
    rows = (
        db.query(Jugador)
        .join(Inscripcion, Inscripcion.id_jugador == Jugador.id)
        .filter(Inscripcion.id_temporada == temporada_id)
        .all()
    )
    return [{"id_jugador": j.id, "nombre": j.nombre, "foto_url": j.foto_url} for j in rows]


def get_todas_posiciones(db: Session, temporada_id: int) -> list[dict]:
    reunion_ids = [
        r.id
        for r in db.query(Reunion.id).filter(Reunion.id_temporada == temporada_id).all()
    ]
    if not reunion_ids:
        return []
    posiciones = db.query(Posicion).filter(Posicion.id_reunion.in_(reunion_ids)).all()
    return [
        {"id_jugador": p.id_jugador, "es_invitado": p.es_invitado, "puntos": p.puntos}
        for p in posiciones
    ]


def get_temporada_activa_detalle(db: Session) -> dict:
    temporada = _get_temporada_activa(db)
    jugadores = (
        db.query(Jugador)
        .join(Inscripcion, Inscripcion.id_jugador == Jugador.id)
        .filter(Inscripcion.id_temporada == temporada.id)
        .order_by(Jugador.nombre)
        .all()
    )
    total_reuniones = db.query(Reunion).filter(Reunion.id_temporada == temporada.id).count()
    return {
        "id": temporada.id,
        "nombre": temporada.nombre,
        "estado": temporada.estado,
        "fecha_inicio": temporada.fecha_inicio,
        "jugadores": jugadores,
        "total_reuniones": total_reuniones,
    }


def get_ranking(db: Session) -> list[dict]:
    temporada = _get_temporada_activa(db)
    inscripciones = get_inscripciones(db, temporada.id)
    posiciones = get_todas_posiciones(db, temporada.id)
    ranking = calcular_ranking(inscripciones, posiciones)
    foto_map = {i["id_jugador"]: i["foto_url"] for i in inscripciones}
    for entry in ranking:
        entry["foto_url"] = foto_map.get(entry["id_jugador"])
    return ranking


def get_reuniones_activa(db: Session) -> list[dict]:
    """
    Return reuniones of the active temporada ordered by numero_jornada,
    each enriched with a `ganador` field.

    ganador rules (spec S-WA-*):
    - If posicion=1 is held by an inscrito (es_invitado=False), ganador contains
      that jugador's data.
    - If posicion=1 is held by an invitado OR no posicion rows exist, ganador=None.
    """
    temporada = _get_temporada_activa(db)

    reuniones = (
        db.query(Reunion)
        .filter(Reunion.id_temporada == temporada.id)
        .order_by(Reunion.numero_jornada)
        .all()
    )
    if not reuniones:
        return []

    reunion_ids = [r.id for r in reuniones]

    # Load all posicion=1 rows for these reuniones (including invitados)
    posicion_1_rows = (
        db.query(Posicion)
        .filter(
            Posicion.id_reunion.in_(reunion_ids),
            Posicion.posicion == 1,
        )
        .all()
    )

    # Build a map: id_reunion → ganador dict or None
    # Only mark as ganador when posicion=1 AND es_invitado=False
    ganador_map: dict[int, dict | None] = {}
    jugador_ids_needed = {
        p.id_jugador for p in posicion_1_rows if not p.es_invitado and p.id_jugador is not None
    }

    jugador_info: dict[int, dict] = {}
    if jugador_ids_needed:
        jugadores = (
            db.query(Jugador)
            .filter(Jugador.id.in_(jugador_ids_needed))
            .all()
        )
        jugador_info = {j.id: {"nombre": j.nombre, "foto_url": j.foto_url} for j in jugadores}

    for p in posicion_1_rows:
        if p.es_invitado or p.id_jugador is None:
            ganador_map[p.id_reunion] = None
        else:
            info = jugador_info.get(p.id_jugador, {})
            ganador_map[p.id_reunion] = {
                "id_jugador": p.id_jugador,
                "nombre": info.get("nombre", ""),
                "foto_url": info.get("foto_url"),
            }

    # Build enriched response dicts
    return [
        {
            "id": r.id,
            "numero_jornada": r.numero_jornada,
            "fecha": r.fecha,
            "ganador": ganador_map.get(r.id),
        }
        for r in reuniones
    ]


def get_resultados_reunion(db: Session, reunion_id: int) -> dict:
    reunion = db.query(Reunion).filter(Reunion.id == reunion_id).first()
    if not reunion:
        raise HTTPException(status_code=404, detail="Reunión no encontrada")

    posiciones_db = (
        db.query(Posicion)
        .filter(Posicion.id_reunion == reunion_id)
        .order_by(Posicion.posicion)
        .all()
    )

    jugadores_map: dict[int, dict] = {
        j.id: {"nombre": j.nombre, "foto_url": j.foto_url}
        for j in db.query(Jugador).all()
    }

    posiciones = [
        {
            "posicion": p.posicion,
            "puntos": p.puntos,
            "nombre": "Invitado" if p.es_invitado else jugadores_map.get(p.id_jugador, {}).get("nombre", "?"),
            "es_invitado": p.es_invitado,
            "id_jugador": p.id_jugador,
            "foto_url": None if p.es_invitado else jugadores_map.get(p.id_jugador, {}).get("foto_url"),
        }
        for p in posiciones_db
    ]

    return {
        "id": reunion.id,
        "numero_jornada": reunion.numero_jornada,
        "fecha": reunion.fecha,
        "posiciones": posiciones,
    }
