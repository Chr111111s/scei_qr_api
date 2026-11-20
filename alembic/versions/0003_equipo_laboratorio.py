"""add laboratorio to Equipo

Revision ID: 0003_equipo_laboratorio
Revises: 0002_correo_matricula
Create Date: 2026-11-19

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_equipo_laboratorio"
down_revision: str | None = "0002_correo_matricula"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("Equipo", sa.Column("laboratorio", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("Equipo", "laboratorio")
