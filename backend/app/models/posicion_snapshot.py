from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from app.database import Base


class PosicionSnapshot(Base):
    """
    Snapshot del ranking acumulado por jugador en cada jornada.

    - posicion: competition rank (1, 1, 3, 4) — ya resuelto con ties.
    - puntos_acumulados: suma de puntos del jugador hasta esta jornada inclusive.
    - Los invitados NUNCA se almacenan aquí (id_jugador NOT NULL).
    - Un jugador aparece en el snapshot de la jornada R solo si tiene
      asistencias > 0 hasta R.
    """

    __tablename__ = "posicion_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    id_temporada = Column(
        Integer, ForeignKey("temporadas.id"), nullable=False, index=True
    )
    id_reunion = Column(
        Integer, ForeignKey("reuniones.id"), nullable=False, index=True
    )
    id_jugador = Column(
        Integer, ForeignKey("jugadores.id"), nullable=False, index=True
    )
    posicion = Column(Integer, nullable=False)
    puntos_acumulados = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "id_reunion",
            "id_jugador",
            name="uq_snapshot_reunion_jugador",
        ),
        Index(
            "ix_snapshot_temporada_jugador_reunion",
            "id_temporada",
            "id_jugador",
            "id_reunion",
        ),
    )
