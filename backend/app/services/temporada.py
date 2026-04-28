from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
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
            # Reusa jugador existente case-insensitive con strip; si no existe, lo crea.
            # Mantiene consistencia con la regla de unicidad del catálogo (POST /jugadores).
            nombre_normalizado = ji.nombre.strip()
            jugador = (
                db.query(Jugador)
                .filter(func.lower(Jugador.nombre) == nombre_normalizado.lower())
                .first()
            )
            if jugador is None:
                jugador = Jugador(nombre=nombre_normalizado)
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


def inscribir_jugador_en_activa(db: Session, id_jugador: int) -> Inscripcion:
    """
    Inscribe un jugador existente a la temporada activa, después de iniciada.

    Validaciones:
    - Debe existir una temporada en estado `activa` → si no, 404.
    - El jugador debe existir → si no, 404.
    - El jugador no debe estar ya inscrito → si lo está, 409.
    """
    temporada = db.query(Temporada).filter(Temporada.estado == EstadoTemporada.activa).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="No hay temporada activa")

    jugador = db.query(Jugador).filter(Jugador.id == id_jugador).first()
    if not jugador:
        raise HTTPException(status_code=404, detail=f"Jugador {id_jugador} no encontrado")

    ya_inscrito = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.id_temporada == temporada.id,
            Inscripcion.id_jugador == id_jugador,
        )
        .first()
    )
    if ya_inscrito is not None:
        raise HTTPException(
            status_code=409,
            detail=f"El jugador '{jugador.nombre}' ya está inscrito en la temporada activa",
        )

    inscripcion = Inscripcion(id_temporada=temporada.id, id_jugador=id_jugador)
    db.add(inscripcion)
    db.commit()
    db.refresh(inscripcion)
    return inscripcion
