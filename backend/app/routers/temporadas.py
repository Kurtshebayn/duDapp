from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.consultas import (
    EstadisticasResponse,
    RankingEntryResponse,
    ReunionResumenResponse,
    TemporadaActivaDetalleResponse,
)
from app.schemas.reunion import ReunionCreate, ReunionResponse
from app.schemas.temporada import TemporadaCreate, TemporadaResponse
from app.services import consultas as consultas_service
from app.services import reunion as reunion_service
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


@router.get("/activa/estadisticas", response_model=EstadisticasResponse)
def estadisticas_temporada_activa(db: Session = Depends(get_db)):
    return consultas_service.get_estadisticas(db)
