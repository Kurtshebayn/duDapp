from sqlalchemy import Column, Integer, String
from app.database import Base


class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    foto_url = Column(String, nullable=True)
