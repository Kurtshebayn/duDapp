"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_email"), "usuarios", ["email"], unique=True)
    op.create_index(op.f("ix_usuarios_id"), "usuarios", ["id"], unique=False)

    op.create_table(
        "jugadores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jugadores_id"), "jugadores", ["id"], unique=False)

    op.create_table(
        "temporadas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("activa", "cerrada", name="estadotemporada"),
            nullable=False,
        ),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_temporadas_id"), "temporadas", ["id"], unique=False)

    op.create_table(
        "inscripciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_temporada", sa.Integer(), nullable=False),
        sa.Column("id_jugador", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_jugador"], ["jugadores.id"]),
        sa.ForeignKeyConstraint(["id_temporada"], ["temporadas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_temporada", "id_jugador", name="uq_inscripcion_temporada_jugador"),
    )
    op.create_index(op.f("ix_inscripciones_id"), "inscripciones", ["id"], unique=False)

    op.create_table(
        "reuniones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_temporada", sa.Integer(), nullable=False),
        sa.Column("numero_jornada", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["id_temporada"], ["temporadas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reuniones_id"), "reuniones", ["id"], unique=False)

    op.create_table(
        "posiciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_reunion", sa.Integer(), nullable=False),
        sa.Column("id_jugador", sa.Integer(), nullable=True),
        sa.Column("es_invitado", sa.Boolean(), nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=False),
        sa.Column("puntos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_jugador"], ["jugadores.id"]),
        sa.ForeignKeyConstraint(["id_reunion"], ["reuniones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_posiciones_id"), "posiciones", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_posiciones_id"), table_name="posiciones")
    op.drop_table("posiciones")
    op.drop_index(op.f("ix_reuniones_id"), table_name="reuniones")
    op.drop_table("reuniones")
    op.drop_index(op.f("ix_inscripciones_id"), table_name="inscripciones")
    op.drop_table("inscripciones")
    op.drop_index(op.f("ix_temporadas_id"), table_name="temporadas")
    op.drop_table("temporadas")
    op.drop_index(op.f("ix_jugadores_id"), table_name="jugadores")
    op.drop_table("jugadores")
    op.drop_index(op.f("ix_usuarios_email"), table_name="usuarios")
    op.drop_index(op.f("ix_usuarios_id"), table_name="usuarios")
    op.drop_table("usuarios")
    op.execute("DROP TYPE IF EXISTS estadotemporada")
