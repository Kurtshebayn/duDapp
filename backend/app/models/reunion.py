from sqlalchemy import Column, Integer, Date, ForeignKey
from app.database import Base


class Reunion(Base):
    __tablename__ = "reuniones"

    id = Column(Integer, primary_key=True, index=True)
    id_temporada = Column(Integer, ForeignKey("temporadas.id"), nullable=False)
    numero_jornada = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=True)
