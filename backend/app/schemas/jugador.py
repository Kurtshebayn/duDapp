from pydantic import BaseModel, field_validator, model_validator


class JugadorInput(BaseModel):
    id: int | None = None
    nombre: str | None = None

    @model_validator(mode="after")
    def check_id_o_nombre(self):
        if self.id is None and not self.nombre:
            raise ValueError("Se requiere id o nombre del jugador")
        return self


class JugadorCreate(BaseModel):
    nombre: str

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v


class JugadorResponse(BaseModel):
    id: int
    nombre: str
    foto_url: str | None = None

    model_config = {"from_attributes": True}
