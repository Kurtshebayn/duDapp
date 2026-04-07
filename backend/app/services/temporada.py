from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inscripcion import Inscripcion
from app.models.jugador import Jugador
from app.models.temporada import EstadoTemporada, Temporada


def crear_temporada(db: Session, nombre: str, fecha_inicio: date, jugadores_input: list, usuario_id: int) -> Temporada:
    if db.query(Temporada).filter(Temporada.estado == EstadoTemporada.activa).first():
        raise HTTPException(status_code=400, detail="Ya existe una temporada activa")

    temporada = Temporada(
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        estado=EstadoTemporada.activa,
        id_usuario=usuario_id,
    )
    db.add(temporada)
    db.flush()

    for ji in jugadores_input:
        if ji.id is not None:
            jugador = db.query(Jugador).filter(Jugador.id == ji.id).first()
            if not jugador:
                raise HTTPException(status_code=404, detail=f"Jugador {ji.id} no encontrado")
        else:
            jugador = Jugador(nombre=ji.nombre)
            db.add(jugador)
            db.flush()

        db.add(Inscripcion(id_temporada=temporada.id, id_jugador=jugador.id))

    db.commit()
    db.refresh(temporada)
    return temporada


def cerrar_temporada(db: Session, temporada_id: int) -> Temporada:
    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")
    if temporada.estado == EstadoTemporada.cerrada:
        raise HTTPException(status_code=400, detail="La temporada ya está cerrada")

    temporada.estado = EstadoTemporada.cerrada
    db.commit()
    db.refresh(temporada)
    return temporada
