from datetime import date

from pydantic import BaseModel

from app.schemas.jugador import JugadorResponse


class TemporadaActivaDetalleResponse(BaseModel):
    id: int
    nombre: str
    estado: str
    fecha_inicio: date
    jugadores: list[JugadorResponse]
    total_reuniones: int


class RankingEntryResponse(BaseModel):
    id_jugador: int
    nombre: str
    puntos: int
    asistencias: int
    foto_url: str | None = None


class PosicionResultadoResponse(BaseModel):
    posicion: int
    puntos: int
    nombre: str
    es_invitado: bool
    id_jugador: int | None = None
    foto_url: str | None = None


class ReunionResultadosResponse(BaseModel):
    id: int
    numero_jornada: int
    fecha: date | None
    posiciones: list[PosicionResultadoResponse]


class ReunionResumenResponse(BaseModel):
    id: int
    numero_jornada: int
    fecha: date | None

    model_config = {"from_attributes": True}


class EstadisticasEntryResponse(BaseModel):
    id_jugador: int
    nombre: str
    puntos: int
    asistencias: int
    promedio: float
    inasistencias: int
    foto_url: str | None = None


class EstadisticasResponse(BaseModel):
    ranking: list[EstadisticasEntryResponse]
    top3: list[EstadisticasEntryResponse]
    mejor_promedio: EstadisticasEntryResponse | None
    mas_inasistencias: EstadisticasEntryResponse | None
