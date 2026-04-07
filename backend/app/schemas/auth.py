from pydantic import BaseModel


class LoginRequest(BaseModel):
    identificador: str  # email o nombre
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
