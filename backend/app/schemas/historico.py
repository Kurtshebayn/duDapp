from datetime import date

from pydantic import BaseModel


# --- Helpers ---


class TemporadaResumen(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date


# --- Items por métrica ---


class PuntosTotalesItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    puntos: int


class VictoriasItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    victorias: int


class CampeonItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    campeonatos: int


class AsistenciaItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    asistencias: int


class RachaItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    longitud: int
    temporada_inicio: TemporadaResumen
    jornada_inicio: int
    temporada_fin: TemporadaResumen
    jornada_fin: int


class PromedioItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    puntos: int
    asistencias: int
    promedio: float


class PodiosItem(BaseModel):
    id_jugador: int
    nombre: str
    foto_url: str | None = None
    oro: int
    plata: int
    bronce: int
    total: int


# --- Response del resumen ---


class HistoricoResumenResponse(BaseModel):
    puntos_totales: list[PuntosTotalesItem]
    victorias: list[VictoriasItem]
    campeones: list[CampeonItem]
    asistencias: list[AsistenciaItem]
    racha_victorias: list[RachaItem]
    racha_asistencia: list[RachaItem]
    promedios: list[PromedioItem]
    podios: list[PodiosItem]
    racha_inasistencia: list[RachaItem]


# --- Response del head-to-head ---


class HeadToHeadRivalItem(BaseModel):
    rival_id: int
    rival_nombre: str
    rival_foto_url: str | None = None
    victorias: int
    derrotas: int
    reuniones_compartidas: int


class HeadToHeadResponse(BaseModel):
    jugador_id: int
    nombre: str
    foto_url: str | None = None
    rivales: list[HeadToHeadRivalItem]
