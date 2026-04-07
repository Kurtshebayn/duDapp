from datetime import date

from pydantic import BaseModel


class RankingEntryResponse(BaseModel):
    id_jugador: int
    nombre: str
    puntos: int
    asistencias: int


class PosicionResultadoResponse(BaseModel):
    posicion: int
    puntos: int
    nombre: str
    es_invitado: bool


class ReunionResultadosResponse(BaseModel):
    id: int
    numero_jornada: int
    fecha: date
    posiciones: list[PosicionResultadoResponse]


class ReunionResumenResponse(BaseModel):
    id: int
    numero_jornada: int
    fecha: date

    model_config = {"from_attributes": True}


class EstadisticasEntryResponse(BaseModel):
    id_jugador: int
    nombre: str
    puntos: int
    asistencias: int
    promedio: float
    inasistencias: int


class EstadisticasResponse(BaseModel):
    ranking: list[EstadisticasEntryResponse]
    top3: list[EstadisticasEntryResponse]
    mejor_promedio: EstadisticasEntryResponse | None
    mas_inasistencias: EstadisticasEntryResponse | None
