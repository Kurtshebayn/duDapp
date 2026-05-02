"""import temporadas: fecha nullable + campeon_id FK

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-29

DOWNGRADE WARNING: Running downgrade() after any CSV import has occurred will fail
because ALTER COLUMN reuniones.fecha NOT NULL cannot succeed while NULL values exist.
Before downgrading, first run:
    UPDATE reuniones SET fecha = '1900-01-01' WHERE fecha IS NULL;
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Make Reunion.fecha nullable (imported reunions have no known date)
    op.alter_column("reuniones", "fecha", existing_type=sa.Date(), nullable=True)

    # 2. Add nullable campeon_id FK to Temporada (points to jugadores)
    op.add_column(
        "temporadas",
        sa.Column("campeon_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_temporadas_campeon_id_jugadores",
        source_table="temporadas",
        referent_table="jugadores",
        local_cols=["campeon_id"],
        remote_cols=["id"],
        ondelete="SET NULL",  # if a Jugador is deleted, blank the campeon — never cascade-delete the Temporada
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_temporadas_campeon_id_jugadores", "temporadas", type_="foreignkey"
    )
    op.drop_column("temporadas", "campeon_id")
    # WARNING: this fails if any reuniones row has fecha IS NULL (after first import).
    # Run: UPDATE reuniones SET fecha = '1900-01-01' WHERE fecha IS NULL; before this.
    op.alter_column("reuniones", "fecha", existing_type=sa.Date(), nullable=False)
