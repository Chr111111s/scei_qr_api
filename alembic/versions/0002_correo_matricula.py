"""add correo and matricula to Usuario

Revision ID: 0002_correo_matricula
Revises: 0001_initial
Create Date: 2026-11-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_correo_matricula"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("Usuario", sa.Column("correo", sa.Text(), nullable=True))
    op.create_unique_constraint("Usuario_correo_key", "Usuario", ["correo"])

    op.add_column("Usuario", sa.Column("matricula", sa.Text(), nullable=True))
    op.create_unique_constraint("Usuario_matricula_key", "Usuario", ["matricula"])


def downgrade() -> None:
    op.drop_constraint("Usuario_matricula_key", "Usuario", type_="unique")
    op.drop_column("Usuario", "matricula")

    op.drop_constraint("Usuario_correo_key", "Usuario", type_="unique")
    op.drop_column("Usuario", "correo")
