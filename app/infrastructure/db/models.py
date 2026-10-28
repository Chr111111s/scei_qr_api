from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import EstadoIncidencia, EstadoUso, Rol
from app.infrastructure.db.base import Base, utcnow


def _enum_type(enum_cls: type, name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        create_type=False,
        values_callable=lambda enum: [item.value for item in enum],
    )


class Usuario(Base):
    __tablename__ = "Usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column("passwordHash", Text, nullable=False)
    full_name: Mapped[str] = mapped_column("fullName", Text, nullable=False)
    rol: Mapped[Rol] = mapped_column(_enum_type(Rol, "Rol"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fcm_token: Mapped[str | None] = mapped_column("fcmToken", Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    usos: Mapped[list[Uso]] = relationship(back_populates="alumno")
    incidencias_reportadas: Mapped[list[Incidencia]] = relationship(
        back_populates="reportada_por", foreign_keys="Incidencia.reportada_por_id"
    )
    incidencias_atendidas: Mapped[list[Incidencia]] = relationship(
        back_populates="atendida_por", foreign_keys="Incidencia.atendida_por_id"
    )


class Equipo(Base):
    __tablename__ = "Equipo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    ubicacion: Mapped[str] = mapped_column(Text, nullable=False)
    qr_token: Mapped[str] = mapped_column("qrToken", Text, nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    usos: Mapped[list[Uso]] = relationship(back_populates="equipo")
    incidencias: Mapped[list[Incidencia]] = relationship(back_populates="equipo")


class Uso(Base):
    __tablename__ = "Uso"
    __table_args__ = (
        Index("Uso_alumnoId_estado_idx", "alumnoId", "estado"),
        Index("Uso_equipoId_idx", "equipoId"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alumno_id: Mapped[int] = mapped_column(
        "alumnoId",
        ForeignKey("Usuario.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    equipo_id: Mapped[int] = mapped_column(
        "equipoId",
        ForeignKey("Equipo.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    estado: Mapped[EstadoUso] = mapped_column(
        _enum_type(EstadoUso, "EstadoUso"), nullable=False, default=EstadoUso.ACTIVO
    )

    alumno: Mapped[Usuario] = relationship(back_populates="usos", foreign_keys=[alumno_id])
    equipo: Mapped[Equipo] = relationship(back_populates="usos", foreign_keys=[equipo_id])


class Incidencia(Base):
    __tablename__ = "Incidencia"
    __table_args__ = (
        Index("Incidencia_estado_idx", "estado"),
        Index("Incidencia_equipoId_idx", "equipoId"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipo_id: Mapped[int] = mapped_column(
        "equipoId", ForeignKey("Equipo.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    reportada_por_id: Mapped[int] = mapped_column(
        "reportadaPorId",
        ForeignKey("Usuario.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    atendida_por_id: Mapped[int | None] = mapped_column(
        "atendidaPorId",
        ForeignKey("Usuario.id", ondelete="SET NULL", onupdate="CASCADE"),
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    foto_url: Mapped[str | None] = mapped_column("fotoUrl", Text)
    estado: Mapped[EstadoIncidencia] = mapped_column(
        _enum_type(EstadoIncidencia, "EstadoIncidencia"),
        nullable=False,
        default=EstadoIncidencia.PENDIENTE,
    )
    solucion: Mapped[str | None] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(
        "creadaEn", DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    actualizada_en: Mapped[datetime] = mapped_column(
        "actualizadaEn",
        DateTime(timezone=False),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    equipo: Mapped[Equipo] = relationship(back_populates="incidencias", foreign_keys=[equipo_id])
    reportada_por: Mapped[Usuario] = relationship(
        back_populates="incidencias_reportadas", foreign_keys=[reportada_por_id]
    )
    atendida_por: Mapped[Usuario | None] = relationship(
        back_populates="incidencias_atendidas", foreign_keys=[atendida_por_id]
    )
