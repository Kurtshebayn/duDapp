from datetime import date

from pydantic import BaseModel


class PosicionInput(BaseModel):
    id_jugador: int | None = None
    es_invitado: bool = False
    posicion: int


class ReunionCreate(BaseModel):
    fecha: date
    posiciones: list[PosicionInput]


class ReunionResponse(BaseModel):
    id: int
    id_temporada: int
    numero_jornada: int
    fecha: date | None

    model_config = {"from_attributes": True}
