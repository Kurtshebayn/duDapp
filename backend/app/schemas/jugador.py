from pydantic import BaseModel, model_validator


class JugadorInput(BaseModel):
    id: int | None = None
    nombre: str | None = None

    @model_validator(mode="after")
    def check_id_o_nombre(self):
        if self.id is None and not self.nombre:
            raise ValueError("Se requiere id o nombre del jugador")
        return self


class JugadorResponse(BaseModel):
    id: int
    nombre: str
    foto_url: str | None = None

    model_config = {"from_attributes": True}
