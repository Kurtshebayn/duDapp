from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.jugador import Jugador


def crear_jugador(db: Session, nombre: str) -> Jugador:
    """
    Crea un nuevo jugador en el catálogo.

    Asume `nombre` ya pasó la validación del schema (no vacío, strip aplicado).
    Rechaza duplicados case-insensitive (Juan == JUAN == juan).
    """
    existente = (
        db.query(Jugador)
        .filter(func.lower(Jugador.nombre) == nombre.lower())
        .first()
    )
    if existente is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un jugador con nombre '{nombre}'",
        )

    jugador = Jugador(nombre=nombre)
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador
