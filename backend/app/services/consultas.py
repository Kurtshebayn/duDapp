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


def _get_inscripciones(db: Session, temporada_id: int) -> list[dict]:
    rows = (
        db.query(Jugador)
        .join(Inscripcion, Inscripcion.id_jugador == Jugador.id)
        .filter(Inscripcion.id_temporada == temporada_id)
        .all()
    )
    return [{"id_jugador": j.id, "nombre": j.nombre, "foto_url": j.foto_url} for j in rows]


def _get_todas_posiciones(db: Session, temporada_id: int) -> list[dict]:
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
    inscripciones = _get_inscripciones(db, temporada.id)
    posiciones = _get_todas_posiciones(db, temporada.id)
    ranking = calcular_ranking(inscripciones, posiciones)
    foto_map = {i["id_jugador"]: i["foto_url"] for i in inscripciones}
    for entry in ranking:
        entry["foto_url"] = foto_map.get(entry["id_jugador"])
    return ranking


def get_reuniones_activa(db: Session) -> list[Reunion]:
    temporada = _get_temporada_activa(db)
    return (
        db.query(Reunion)
        .filter(Reunion.id_temporada == temporada.id)
        .order_by(Reunion.numero_jornada)
        .all()
    )


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
