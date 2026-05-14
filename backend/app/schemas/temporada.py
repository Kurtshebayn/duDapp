from datetime import date

from pydantic import BaseModel, model_serializer

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

    @model_serializer(mode="wrap")
    def _omit_tied_players_when_none(self, handler):
        # REQ-6 / D6: tied_players key is OMITTED entirely when no tie exists.
        # campeon_id and tie_detected remain present (REQ-5).
        data = handler(self)
        if data.get("tied_players") is None:
            data.pop("tied_players", None)
        return data


class DesignarCampeonRequest(BaseModel):
    id_jugador: int


class InscripcionCreate(BaseModel):
    id_jugador: int


class InscripcionResponse(BaseModel):
    id: int
    id_temporada: int
    id_jugador: int

    model_config = {"from_attributes": True}
