from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.consultas import (
    RankingEntryResponse,
    RankingNarrativoEntry,
    ReunionResumenResponse,
    TemporadaActivaDetalleResponse,
)
from app.schemas.import_temporada import ImportarTemporadaResponse
from app.schemas.reunion import ReunionCreate, ReunionResponse
from app.schemas.temporada import (
    InscripcionCreate,
    InscripcionResponse,
    TemporadaCreate,
    TemporadaResponse,
)
from app.services import consultas as consultas_service
from app.services import import_temporada as import_service
from app.services import reunion as reunion_service
from app.services import snapshots as snapshots_service
from app.services import temporada as temporada_service

router = APIRouter(prefix="/temporadas", tags=["temporadas"])


# ── Admin endpoints ───────────────────────────────────────────────────────────


@router.post("", response_model=TemporadaResponse, status_code=201)
def crear_temporada(
    body: TemporadaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return temporada_service.crear_temporada(db, body.nombre, body.fecha_inicio, body.jugadores, user.id)


@router.post("/{temporada_id}/cerrar", response_model=TemporadaResponse)
def cerrar_temporada(
    temporada_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return temporada_service.cerrar_temporada(db, temporada_id)


@router.post("/{temporada_id}/reuniones", response_model=ReunionResponse, status_code=201)
def registrar_reunion(
    temporada_id: int,
    body: ReunionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return reunion_service.registrar_reunion(db, temporada_id, body.fecha, body.posiciones)


@router.post("/activa/inscripciones", response_model=InscripcionResponse, status_code=201)
def inscribir_jugador_en_activa(
    body: InscripcionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return temporada_service.inscribir_jugador_en_activa(db, body.id_jugador)


@router.post("/import", response_model=ImportarTemporadaResponse, status_code=201)
def importar_temporada(
    nombre: str = Form(...),
    fecha_inicio: date = Form(...),
    archivo: UploadFile = File(...),
    campeon_nombre: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Import a complete closed historical season from a CSV file.

    Multipart form fields:
    - nombre: season name (must be unique)
    - fecha_inicio: ISO date (YYYY-MM-DD)
    - archivo: CSV file (UTF-8, `;` or `,` separator)
    - campeon_nombre: optional champion name (must match a CSV header)

    Returns HTTP 201 with the created season and import summary counts.
    Raises 409 on duplicate name, 422 on any validation failure.
    """
    archivo_bytes = archivo.file.read()
    result = import_service.importar_temporada(
        db=db,
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        archivo_bytes=archivo_bytes,
        campeon_nombre=campeon_nombre,
        usuario_id=user.id,
    )
    # Build the response dict combining Temporada fields + resumen_import
    return {
        "id": result.temporada.id,
        "nombre": result.temporada.nombre,
        "fecha_inicio": result.temporada.fecha_inicio,
        "estado": result.temporada.estado,
        "campeon_id": result.temporada.campeon_id,
        "resumen_import": {
            "jugadores_inscriptos": result.resumen.jugadores_inscriptos,
            "reuniones_creadas": result.resumen.reuniones_creadas,
            "posiciones_creadas": result.resumen.posiciones_creadas,
            "invitados_inferidos": result.resumen.invitados_inferidos,
        },
    }


# ── Public endpoints ──────────────────────────────────────────────────────────


@router.get("/activa", response_model=TemporadaActivaDetalleResponse)
def get_temporada_activa(db: Session = Depends(get_db)):
    return consultas_service.get_temporada_activa_detalle(db)


@router.get("/activa/ranking", response_model=list[RankingEntryResponse])
def ranking_temporada_activa(db: Session = Depends(get_db)):
    return consultas_service.get_ranking(db)


@router.get("/activa/reuniones", response_model=list[ReunionResumenResponse])
def listar_reuniones_temporada_activa(db: Session = Depends(get_db)):
    return consultas_service.get_reuniones_activa(db)


@router.get("/activa/ranking-narrativo", response_model=list[RankingNarrativoEntry])
def ranking_narrativo_temporada_activa(db: Session = Depends(get_db)):
    """
    Public endpoint — no auth required.
    Returns the current ranking of the active temporada enriched with narrative
    fields: delta_posicion (SEMANTIC convention), racha, lider_desde_jornada.
    Returns an empty list when there is no active temporada or no snapshots exist.
    """
    return snapshots_service.get_ranking_narrativo(db)
