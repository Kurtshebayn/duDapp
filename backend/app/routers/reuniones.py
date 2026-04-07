from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.consultas import ReunionResultadosResponse
from app.schemas.reunion import ReunionCreate, ReunionResponse
from app.services import consultas as consultas_service
from app.services import reunion as reunion_service

router = APIRouter(prefix="/reuniones", tags=["reuniones"])


# ── Admin endpoints ───────────────────────────────────────────────────────────


@router.put("/{reunion_id}", response_model=ReunionResponse)
def editar_reunion(
    reunion_id: int,
    body: ReunionCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return reunion_service.editar_reunion(db, reunion_id, body.fecha, body.posiciones)


# ── Public endpoints ──────────────────────────────────────────────────────────


@router.get("/{reunion_id}", response_model=ReunionResultadosResponse)
def resultados_reunion(reunion_id: int, db: Session = Depends(get_db)):
    return consultas_service.get_resultados_reunion(db, reunion_id)
