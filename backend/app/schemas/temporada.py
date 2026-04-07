from datetime import date

from pydantic import BaseModel

from app.schemas.jugador import JugadorInput


class TemporadaCreate(BaseModel):
    nombre: str
    jugadores: list[JugadorInput]


class TemporadaResponse(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    estado: str

    model_config = {"from_attributes": True}
