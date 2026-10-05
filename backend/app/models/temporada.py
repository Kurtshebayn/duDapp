import enum
from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey
from app.database import Base



class EstadoTemporada(str, enum.Enum):
    activa = "activa"
    cerrada = "cerrada"


class ModoPuntaje(str, enum.Enum):
    """Per-season scoring mode, chosen at creation and immutable afterwards."""

    fijo_15 = "fijo_15"  # position N = 15 - (N-1)
    por_asistentes = "por_asistentes"  # position N = total participants - (N-1)


class Temporada(Base):
    __tablename__ = "temporadas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    estado = Column(Enum(EstadoTemporada), nullable=False, default=EstadoTemporada.activa)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    campeon_id = Column(Integer, ForeignKey("jugadores.id", ondelete="SET NULL"), nullable=True)
    fecha_cierre = Column(Date, nullable=True)
    modo_puntaje = Column(
        Enum(ModoPuntaje),
        nullable=False,
        default=ModoPuntaje.fijo_15,
        server_default=ModoPuntaje.fijo_15.value,
    )
