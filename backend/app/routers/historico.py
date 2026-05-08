"""
Router público /historico — sin autenticación requerida.

Endpoints:
  GET /historico/resumen                  → HistoricoResumenResponse
  GET /historico/head-to-head/{jugador_id} → HeadToHeadResponse
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.historico import HeadToHeadResponse, HistoricoResumenResponse
from app.services import historico as historico_service

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("/resumen", response_model=HistoricoResumenResponse)
def get_resumen(db: Session = Depends(get_db)):
    """
    Devuelve el resumen histórico cross-temporadas con 8 métricas:
    puntos_totales, victorias, campeones, asistencias, racha_victorias,
    racha_asistencia, promedios, podios.

    Solo considera temporadas cerradas (C1).
    Si no hay temporadas cerradas → 200 con todas las listas vacías.
    """
    return historico_service.get_historico_resumen(db)


@router.get("/head-to-head/{jugador_id}", response_model=HeadToHeadResponse)
def get_head_to_head(jugador_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el row de enfrentamientos directos del jugador contra todos los
    rivales con quienes compartió al menos una reunión en temporadas cerradas.

    404 si jugador_id no existe.
    200 con rivales=[] si el jugador existe pero no tiene historial cerrado.
    """
    return historico_service.get_head_to_head(db, jugador_id)
