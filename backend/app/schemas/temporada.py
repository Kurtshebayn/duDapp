from datetime import date

from pydantic import BaseModel

from app.schemas.jugador import JugadorInput


class TemporadaCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    jugadores: list[JugadorInput]


class TiedPlayerSchema(BaseModel):
    id_jugador: int
    nombre: str


class TemporadaResponse(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    estado: str
    campeon_id: int | None = None
    tie_detected: bool = False
    tied_players: list[TiedPlayerSchema] | None = None

    model_config = {"from_attributes": True}


class DesignarCampeonRequest(BaseModel):
    id_jugador: int


class InscripcionCreate(BaseModel):
    id_jugador: int


class InscripcionResponse(BaseModel):
    id: int
    id_temporada: int
    id_jugador: int

    model_config = {"from_attributes": True}
