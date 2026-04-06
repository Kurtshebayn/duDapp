from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.database import Base


class Posicion(Base):
    __tablename__ = "posiciones"

    id = Column(Integer, primary_key=True, index=True)
    id_reunion = Column(Integer, ForeignKey("reuniones.id"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id"), nullable=True)
    es_invitado = Column(Boolean, nullable=False, default=False)
    posicion = Column(Integer, nullable=False)
    puntos = Column(Integer, nullable=False)
