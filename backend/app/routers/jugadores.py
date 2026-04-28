import os

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.jugador import Jugador
from app.models.usuario import Usuario
from app.schemas.jugador import JugadorCreate, JugadorResponse
from app.services import jugador as jugador_service

router = APIRouter(prefix="/jugadores", tags=["jugadores"])


def _cloudinary_configured() -> bool:
    return all(
        os.getenv(v)
        for v in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    )


@router.get("", response_model=list[JugadorResponse])
def listar_jugadores(db: Session = Depends(get_db)):
    return db.query(Jugador).order_by(Jugador.nombre).all()


@router.post("", response_model=JugadorResponse, status_code=201)
def crear_jugador(
    body: JugadorCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return jugador_service.crear_jugador(db, body.nombre)


@router.post("/{id}/foto", response_model=JugadorResponse)
def subir_foto(
    id: int,
    foto: UploadFile,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    jugador = db.query(Jugador).filter(Jugador.id == id).first()
    if jugador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado")

    if not _cloudinary_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary no está configurado en el servidor",
        )

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )

    result = cloudinary.uploader.upload(
        foto.file,
        folder="dudapp/jugadores",
        public_id=f"jugador_{id}",
        overwrite=True,
        resource_type="image",
    )

    jugador.foto_url = result["secure_url"]
    db.commit()
    db.refresh(jugador)
    return jugador
