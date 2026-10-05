"""add modo_puntaje to temporadas

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-05

Adds a NOT NULL per-season scoring mode `modo_puntaje` to `temporadas`,
backed by the native Postgres enum `modopuntaje` (same pattern as
`estadotemporada`):

- fijo_15: position N = 15 - (N-1) (historical rule).
- por_asistentes: position N = total participants in the meeting - (N-1).

server_default 'fijo_15' backfills every existing season with the historical
rule, so stored points and behavior of existing seasons are unchanged.

DOWNGRADE: drops the column, then the enum type.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

modo_puntaje_enum = sa.Enum("fijo_15", "por_asistentes", name="modopuntaje")


def upgrade() -> None:
    modo_puntaje_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "temporadas",
        sa.Column(
            "modo_puntaje",
            modo_puntaje_enum,
            nullable=False,
            server_default="fijo_15",
        ),
    )


def downgrade() -> None:
    op.drop_column("temporadas", "modo_puntaje")
    modo_puntaje_enum.drop(op.get_bind(), checkfirst=True)
