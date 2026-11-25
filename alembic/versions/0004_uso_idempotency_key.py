"""add idempotencyKey to Uso

Revision ID: 0004_uso_idempotency
Revises: 0003_equipo_laboratorio
Create Date: 2026-11-24

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_uso_idempotency"
down_revision: str | None = "0003_equipo_laboratorio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("Uso", sa.Column("idempotencyKey", sa.Text(), nullable=True))
    op.execute(
        'CREATE UNIQUE INDEX "Uso_alumnoId_idempotencyKey_key" '
        'ON "Uso"("alumnoId", "idempotencyKey") '
        'WHERE "idempotencyKey" IS NOT NULL'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS "Uso_alumnoId_idempotencyKey_key"')
    op.drop_column("Uso", "idempotencyKey")
