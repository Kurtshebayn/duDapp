from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.jugador import Jugador
from app.schemas.jugador import JugadorResponse

router = APIRouter(prefix="/jugadores", tags=["jugadores"])


@router.get("", response_model=list[JugadorResponse])
def listar_jugadores(db: Session = Depends(get_db)):
    return db.query(Jugador).order_by(Jugador.nombre).all()
