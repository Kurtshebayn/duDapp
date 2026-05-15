"""add fecha_cierre to temporadas

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-15

Adds a nullable Date column `fecha_cierre` to `temporadas`.
`cerrar_temporada()` will set this atomically on season close.

NULLS LAST ordering (`ORDER BY fecha_cierre DESC NULLS LAST, id DESC`) allows
the public endpoint to find the most-recently-closed season, with historical
rows (NULL) falling after post-migration rows.

No backfill — the 5 bulk-imported historical seasons stay NULL by design.
Frontend hero degrades gracefully when fecha_cierre is NULL.

DOWNGRADE: drops the column. Safe because the column is nullable and carries
no NOT NULL constraints or foreign keys.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "temporadas",
        sa.Column("fecha_cierre", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("temporadas", "fecha_cierre")
