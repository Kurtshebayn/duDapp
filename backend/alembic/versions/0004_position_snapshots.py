"""create posicion_snapshot table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-11

FORWARD ONLY: this migration creates an empty posicion_snapshot table.
No backfill is performed — historical data is not retroactively snapshotted.
Narrative features (delta, racha, lider_desde) become available only from
the next registered reunion onward.

DOWNGRADE: drops the index first, then the table. No data caveats because
the table starts empty and backfill is never run automatically.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posicion_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_temporada", sa.Integer(), nullable=False),
        sa.Column("id_reunion", sa.Integer(), nullable=False),
        sa.Column("id_jugador", sa.Integer(), nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=False),
        sa.Column("puntos_acumulados", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_jugador"], ["jugadores.id"]),
        sa.ForeignKeyConstraint(["id_reunion"], ["reuniones.id"]),
        sa.ForeignKeyConstraint(["id_temporada"], ["temporadas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id_reunion",
            "id_jugador",
            name="uq_snapshot_reunion_jugador",
        ),
    )
    op.create_index(
        op.f("ix_posicion_snapshot_id"),
        "posicion_snapshot",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_posicion_snapshot_id_jugador"),
        "posicion_snapshot",
        ["id_jugador"],
        unique=False,
    )
    op.create_index(
        op.f("ix_posicion_snapshot_id_reunion"),
        "posicion_snapshot",
        ["id_reunion"],
        unique=False,
    )
    op.create_index(
        op.f("ix_posicion_snapshot_id_temporada"),
        "posicion_snapshot",
        ["id_temporada"],
        unique=False,
    )
    op.create_index(
        "ix_snapshot_temporada_jugador_reunion",
        "posicion_snapshot",
        ["id_temporada", "id_jugador", "id_reunion"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_snapshot_temporada_jugador_reunion",
        table_name="posicion_snapshot",
    )
    op.drop_index(
        op.f("ix_posicion_snapshot_id_temporada"),
        table_name="posicion_snapshot",
    )
    op.drop_index(
        op.f("ix_posicion_snapshot_id_reunion"),
        table_name="posicion_snapshot",
    )
    op.drop_index(
        op.f("ix_posicion_snapshot_id_jugador"),
        table_name="posicion_snapshot",
    )
    op.drop_index(
        op.f("ix_posicion_snapshot_id"),
        table_name="posicion_snapshot",
    )
    op.drop_table("posicion_snapshot")
