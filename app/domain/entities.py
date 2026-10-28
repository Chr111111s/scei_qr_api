from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import EstadoIncidencia, EstadoUso, Rol


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    full_name: str
    rol: Rol
    activo: bool
    fcm_token: str | None
    created_at: datetime


@dataclass(frozen=True)
class Equipment:
    id: int
    codigo: str
    nombre: str
    descripcion: str | None
    ubicacion: str
    qr_token: str
    activo: bool
    created_at: datetime


@dataclass(frozen=True)
class UserSummary:
    id: int
    username: str
    full_name: str


@dataclass(frozen=True)
class Usage:
    id: int
    alumno_id: int
    equipo_id: int
    inicio: datetime
    fin: datetime | None
    estado: EstadoUso
    equipo: Equipment | None = None
    alumno: UserSummary | None = None


@dataclass(frozen=True)
class Incident:
    id: int
    equipo_id: int
    reportada_por_id: int
    atendida_por_id: int | None
    titulo: str
    descripcion: str
    foto_url: str | None
    estado: EstadoIncidencia
    solucion: str | None
    creada_en: datetime
    actualizada_en: datetime
    equipo: Equipment | None = None
    reportada_por: UserSummary | None = None
    atendida_por: UserSummary | None = None


@dataclass(frozen=True)
class EquipmentUsageCount:
    equipment: Equipment
    usos: int
    incidencias: int


@dataclass(frozen=True)
class ReportData:
    equipos: list[EquipmentUsageCount]
    usos: list[Usage]
    incidencias: list[Incident]
