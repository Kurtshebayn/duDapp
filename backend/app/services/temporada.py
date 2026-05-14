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


def cerrar_temporada(db: Session, temporada_id: int) -> tuple[Temporada, bool, list[dict] | None]:
    """
    Closes a temporada and computes tie state in a single transaction.

    Returns (temporada, tie_detected, tied_players_or_none).

    Behavior:
    - If exactly ONE player holds max points: campeon_id auto-set to that id;
      tie_detected=False; tied_players=None.
    - If 2+ players tied at max: campeon_id stays None; tie_detected=True;
      tied_players=[{id_jugador, nombre}, ...] (all tied).
    - If ranking empty (no asistencias): campeon_id stays None;
      tie_detected=False; tied_players=None.
    """
    from app.services import consultas as consultas_service
    from app.services.ranking import detect_max_points_holders

    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")
    if temporada.estado == EstadoTemporada.cerrada:
        raise HTTPException(status_code=400, detail="La temporada ya está cerrada")

    # Compute tie BEFORE flipping estado, so consultas_service helpers
    # see the temporada in a consistent state (id-based, estado-agnostic).
    inscripciones = consultas_service.get_inscripciones(db, temporada_id)
    posiciones = consultas_service.get_todas_posiciones(db, temporada_id)
    winners = detect_max_points_holders(inscripciones, posiciones)

    tie_detected = len(winners) > 1
    tied_players = winners if tie_detected else None

    if len(winners) == 1:
        temporada.campeon_id = winners[0]["id_jugador"]

    temporada.estado = EstadoTemporada.cerrada
    db.commit()
    db.refresh(temporada)
    return temporada, tie_detected, tied_players


def designar_campeon(db: Session, temporada_id: int, id_jugador: int) -> Temporada:
    """
    Sets temporada.campeon_id to id_jugador, idempotent.

    Validations (REQ-3 in spec) — first failure wins:
    1. Temporada exists → 404
    2. estado == cerrada → 422
    3. id_jugador inscripto en esa temporada → 422
    4. id_jugador is among the max-points holders of the final ranking → 422

    Idempotent: same id → 200 no-op; different tied player → 200 overwrites.
    """
    from app.services import consultas as consultas_service
    from app.services.ranking import detect_max_points_holders

    temporada = db.query(Temporada).filter(Temporada.id == temporada_id).first()
    if not temporada:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")

    if temporada.estado != EstadoTemporada.cerrada:
        raise HTTPException(
            status_code=422,
            detail="No se puede designar campeón en una temporada que no está cerrada.",
        )

    inscripto = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.id_temporada == temporada_id,
            Inscripcion.id_jugador == id_jugador,
        )
        .first()
    )
    if not inscripto:
        raise HTTPException(
            status_code=422,
            detail=f"El jugador {id_jugador} no está inscripto en la temporada {temporada_id}.",
        )

    inscripciones = consultas_service.get_inscripciones(db, temporada_id)
    posiciones = consultas_service.get_todas_posiciones(db, temporada_id)
    winners = detect_max_points_holders(inscripciones, posiciones)
    winner_ids = {w["id_jugador"] for w in winners}

    if id_jugador not in winner_ids:
        raise HTTPException(
            status_code=422,
            detail=f"El jugador {id_jugador} no está entre los primeros del ranking final de la temporada {temporada_id}.",
        )

    # Idempotent set — same id is a no-op at the DB level (SQLAlchemy UPDATE
    # to identical value); different id overwrites.
    temporada.campeon_id = id_jugador
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
