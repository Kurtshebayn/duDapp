from datetime import date

from pydantic import BaseModel


class ResumenImportResponse(BaseModel):
    jugadores_inscriptos: int
    reuniones_creadas: int
    posiciones_creadas: int
    invitados_inferidos: int


class ImportarTemporadaResponse(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    estado: str
    campeon_id: int | None = None
    resumen_import: ResumenImportResponse

    model_config = {"from_attributes": True}
