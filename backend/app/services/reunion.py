from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.posicion import Posicion
from app.models.reunion import Reunion
from app.models.temporada import EstadoTemporada, Temporada
from app.services import snapshots as snapshots_service
from app.services.puntos import calcular_puntos


def registrar_reunion(
    db: Session,
    temporada_id: int,
    fecha: date,
    posiciones_input: list,
) -> Reunion:
    temporada = _get_temporada_activa(db, temporada_id)

    count = db.query(Reunion).filter(Reunion.id_temporada == temporada_id).count()
    reunion = Reunion(
        id_temporada=temporada_id,
        numero_jornada=count + 1,
        fecha=fecha,
    )
    db.add(reunion)
    db.flush()

    _guardar_posiciones(db, reunion.id, posiciones_input)
    db.flush()  # ensure Posicion rows are visible before snapshot generation

    snapshots_service._generar_snapshots_para_reunion(db, temporada_id, reunion.id)

    db.commit()
    db.refresh(reunion)
    return reunion


def editar_reunion(
    db: Session,
    reunion_id: int,
    fecha: date,
    posiciones_input: list,
) -> Reunion:
    reunion = db.query(Reunion).filter(Reunion.id == reunion_id).first()
    if not reunion:
        raise HTTPException(status_code=404, detail="Reunión no encontrada")

    _get_temporada_activa(db, reunion.id_temporada)

    db.query(Posicion).filter(Posicion.id_reunion == reunion_id).delete()
    reunion.fecha = fecha
    _guardar_posiciones(db, reunion_id, posiciones_input)
    db.flush()  # ensure updated Posicion rows are visible before snapshot replay

    snapshots_service._regenerar_snapshots_temporada(db, reunion.id_temporada)

    db.commit()
    db.refresh(reunion)
    return reunion


def _get_temporada_activa(db: Session, temporada_id: int) -> Temporada:
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")
    if temporada.estado == EstadoTemporada.cerrada:
        raise HTTPException(status_code=400, detail="La temporada está cerrada")
    return temporada


def _guardar_posiciones(db: Session, reunion_id: int, posiciones_input: list) -> None:
    for p in posiciones_input:
        db.add(Posicion(
            id_reunion=reunion_id,
            id_jugador=p.id_jugador,
            es_invitado=p.es_invitado,
            posicion=p.posicion,
            puntos=calcular_puntos(p.posicion),
        ))
