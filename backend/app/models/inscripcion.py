from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base


class Inscripcion(Base):
    __tablename__ = "inscripciones"

    id = Column(Integer, primary_key=True, index=True)
    id_temporada = Column(Integer, ForeignKey("temporadas.id"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("id_temporada", "id_jugador", name="uq_inscripcion_temporada_jugador"),
    )
