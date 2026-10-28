"""Initial schema compatible with the legacy Prisma database.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE \"Rol\" AS ENUM ('ALUMNO', 'SOPORTE', 'ADMIN')")
    op.execute(
        "CREATE TYPE \"EstadoUso\" AS ENUM ('ACTIVO', 'FINALIZADO')"
    )
    op.execute(
        "CREATE TYPE \"EstadoIncidencia\" AS ENUM "
        "('PENDIENTE', 'EN_ATENCION', 'RESUELTA')"
    )

    op.execute(
        """
        CREATE TABLE "Usuario" (
            "id" SERIAL NOT NULL,
            "username" TEXT NOT NULL,
            "passwordHash" TEXT NOT NULL,
            "fullName" TEXT NOT NULL,
            "rol" "Rol" NOT NULL,
            "activo" BOOLEAN NOT NULL DEFAULT true,
            "fcmToken" TEXT,
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "Usuario_pkey" PRIMARY KEY ("id")
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "Equipo" (
            "id" SERIAL NOT NULL,
            "codigo" TEXT NOT NULL,
            "nombre" TEXT NOT NULL,
            "descripcion" TEXT,
            "ubicacion" TEXT NOT NULL,
            "qrToken" TEXT NOT NULL,
            "activo" BOOLEAN NOT NULL DEFAULT true,
            "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "Equipo_pkey" PRIMARY KEY ("id")
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "Uso" (
            "id" SERIAL NOT NULL,
            "alumnoId" INTEGER NOT NULL,
            "equipoId" INTEGER NOT NULL,
            "inicio" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "fin" TIMESTAMP(3),
            "estado" "EstadoUso" NOT NULL DEFAULT 'ACTIVO',
            CONSTRAINT "Uso_pkey" PRIMARY KEY ("id")
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "Incidencia" (
            "id" SERIAL NOT NULL,
            "equipoId" INTEGER NOT NULL,
            "reportadaPorId" INTEGER NOT NULL,
            "atendidaPorId" INTEGER,
            "titulo" TEXT NOT NULL,
            "descripcion" TEXT NOT NULL,
            "fotoUrl" TEXT,
            "estado" "EstadoIncidencia" NOT NULL DEFAULT 'PENDIENTE',
            "solucion" TEXT,
            "creadaEn" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "actualizadaEn" TIMESTAMP(3) NOT NULL,
            CONSTRAINT "Incidencia_pkey" PRIMARY KEY ("id")
        )
        """
    )

    op.execute(
        'CREATE UNIQUE INDEX "Usuario_username_key" ON "Usuario"("username")'
    )
    op.execute(
        'CREATE UNIQUE INDEX "Usuario_fcmToken_key" ON "Usuario"("fcmToken")'
    )
    op.execute('CREATE UNIQUE INDEX "Equipo_codigo_key" ON "Equipo"("codigo")')
    op.execute('CREATE UNIQUE INDEX "Equipo_qrToken_key" ON "Equipo"("qrToken")')
    op.execute(
        'CREATE INDEX "Uso_alumnoId_estado_idx" ON "Uso"("alumnoId", "estado")'
    )
    op.execute('CREATE INDEX "Uso_equipoId_idx" ON "Uso"("equipoId")')
    op.execute('CREATE INDEX "Incidencia_estado_idx" ON "Incidencia"("estado")')
    op.execute('CREATE INDEX "Incidencia_equipoId_idx" ON "Incidencia"("equipoId")')

    op.execute(
        'ALTER TABLE "Uso" ADD CONSTRAINT "Uso_alumnoId_fkey" '
        'FOREIGN KEY ("alumnoId") REFERENCES "Usuario"("id") '
        "ON DELETE RESTRICT ON UPDATE CASCADE"
    )
    op.execute(
        'ALTER TABLE "Uso" ADD CONSTRAINT "Uso_equipoId_fkey" '
        'FOREIGN KEY ("equipoId") REFERENCES "Equipo"("id") '
        "ON DELETE RESTRICT ON UPDATE CASCADE"
    )
    op.execute(
        'ALTER TABLE "Incidencia" ADD CONSTRAINT "Incidencia_equipoId_fkey" '
        'FOREIGN KEY ("equipoId") REFERENCES "Equipo"("id") '
        "ON DELETE RESTRICT ON UPDATE CASCADE"
    )
    op.execute(
        'ALTER TABLE "Incidencia" ADD CONSTRAINT "Incidencia_reportadaPorId_fkey" '
        'FOREIGN KEY ("reportadaPorId") REFERENCES "Usuario"("id") '
        "ON DELETE RESTRICT ON UPDATE CASCADE"
    )
    op.execute(
        'ALTER TABLE "Incidencia" ADD CONSTRAINT "Incidencia_atendidaPorId_fkey" '
        'FOREIGN KEY ("atendidaPorId") REFERENCES "Usuario"("id") '
        "ON DELETE SET NULL ON UPDATE CASCADE"
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "Incidencia" CASCADE')
    op.execute('DROP TABLE IF EXISTS "Uso" CASCADE')
    op.execute('DROP TABLE IF EXISTS "Equipo" CASCADE')
    op.execute('DROP TABLE IF EXISTS "Usuario" CASCADE')
    op.execute('DROP TYPE IF EXISTS "EstadoIncidencia"')
    op.execute('DROP TYPE IF EXISTS "EstadoUso"')
    op.execute('DROP TYPE IF EXISTS "Rol"')
