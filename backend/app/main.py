import os
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import Base, SessionLocal, engine
from app.routers import auth, historico, jugadores, reuniones, temporadas


def _setup_admin() -> None:
    """Crea o actualiza el admin si ADMIN_PASSWORD está definida en el entorno."""
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        return

    from app.models.usuario import Usuario

    email = os.getenv("ADMIN_EMAIL", "admin@dudo.com")
    nombre = os.getenv("ADMIN_NOMBRE", "Admin")
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario:
            usuario.password_hash = password_hash
            usuario.nombre = nombre
            db.commit()
            print(f"[setup_admin] Contrasena actualizada para {email}")
        else:
            db.add(Usuario(email=email, nombre=nombre, password_hash=password_hash))
            db.commit()
            print(f"[setup_admin] Admin creado: {email}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_admin()
    yield


app = FastAPI(title="duDapp API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(temporadas.router)
app.include_router(reuniones.router)
app.include_router(jugadores.router)
app.include_router(historico.router)


@app.get("/health")
def health():
    return {"status": "ok"}
