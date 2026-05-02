import enum
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey
from app.database import Base



class EstadoTemporada(str, enum.Enum):
    activa = "activa"
    cerrada = "cerrada"


class Temporada(Base):
    __tablename__ = "temporadas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    estado = Column(Enum(EstadoTemporada), nullable=False, default=EstadoTemporada.activa)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    campeon_id = Column(Integer, ForeignKey("jugadores.id", ondelete="SET NULL"), nullable=True)
