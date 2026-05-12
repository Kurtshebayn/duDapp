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


class JugadorGanadorResponse(BaseModel):
    """Brief jugador info used as the winner in a reunion summary."""

    id_jugador: int
    nombre: str
    foto_url: str | None = None


class ReunionResumenResponse(BaseModel):
    id: int
    numero_jornada: int
    fecha: date | None
    ganador: JugadorGanadorResponse | None = None


class RankingNarrativoEntry(BaseModel):
    """
    One entry in the narrative ranking for the active temporada.

    delta_posicion uses the SEMANTIC convention (decisions-supplement engram #98):
      delta = anterior_posicion - nueva_posicion
      Positive  → player rose (improved rank).
      Negative  → player dropped.
      Zero      → first appearance or unchanged.
    """

    id_jugador: int
    nombre: str
    foto_url: str | None = None
    puntos: int
    asistencias: int
    posicion: int
    delta_posicion: int
    racha: int
    lider_desde_jornada: int | None = None
