from typing import Any, Protocol

from app.domain.entities import (
    Equipment,
    EquipmentUsageCount,
    Incident,
    Usage,
    User,
)
from app.domain.enums import EstadoIncidencia, Rol


class UserRepository(Protocol):
    async def find_all(
        self, *, rol: Rol | None, activo: bool | None, q: str | None
    ) -> list[User]: ...

    async def find_by_id(self, user_id: int) -> User | None: ...

    async def find_by_username(self, username: str) -> User | None: ...

    async def find_by_fcm_token(self, token: str) -> User | None: ...

    async def exists_username(self, username: str, *, exclude_id: int | None = None) -> bool: ...

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        full_name: str,
        rol: Rol,
        activo: bool,
    ) -> User: ...

    async def update(self, user_id: int, values: dict[str, Any]) -> User: ...

    async def update_fcm_token(self, user_id: int, token: str) -> bool: ...


class EquipmentRepository(Protocol):
    async def find_all(
        self,
        *,
        activo: bool | None,
        q: str | None,
        ubicacion: str | None,
    ) -> list[Equipment]: ...

    async def find_by_id(self, equipment_id: int) -> Equipment | None: ...

    async def find_by_code(self, codigo: str) -> Equipment | None: ...

    async def find_by_qr_token(self, qr_token: str) -> Equipment | None: ...

    async def create(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        ubicacion: str,
        qr_token: str,
    ) -> Equipment: ...

    async def update(self, equipment_id: int, values: dict[str, Any]) -> Equipment: ...

    async def update_qr_token(self, equipment_id: int, qr_token: str) -> Equipment: ...


class UsageRepository(Protocol):
    async def find_active_by_alumno(self, alumno_id: int) -> Usage | None: ...

    async def find_by_id(self, usage_id: int) -> Usage | None: ...

    async def create(self, *, alumno_id: int, equipo_id: int) -> Usage: ...

    async def finalize(self, usage_id: int) -> Usage: ...

    async def list_by_alumno(self, alumno_id: int) -> list[Usage]: ...

    async def list_history(self, *, equipo_id: int, alumno_id: int | None) -> list[Usage]: ...


class IncidentRepository(Protocol):
    async def create(
        self,
        *,
        equipo_id: int,
        reportada_por_id: int,
        titulo: str,
        descripcion: str,
        foto_url: str | None,
    ) -> Incident: ...

    async def find_by_id(self, incident_id: int) -> Incident | None: ...

    async def list_by_reporter(self, user_id: int) -> list[Incident]: ...

    async def list_filtered(
        self, *, estado: EstadoIncidencia | None, equipo_id: int | None
    ) -> list[Incident]: ...

    async def list_history(
        self, *, estado: EstadoIncidencia | None, tecnico_id: int | None
    ) -> list[Incident]: ...

    async def take(self, incident_id: int, tecnico_id: int) -> bool: ...

    async def change_state(self, incident_id: int, estado: EstadoIncidencia) -> Incident: ...

    async def add_solution(self, incident_id: int, solucion: str, tecnico_id: int) -> Incident: ...


class ReportRepository(Protocol):
    async def get_estadisticas(self) -> dict[str, Any]: ...

    async def get_equipment_usage_counts(self) -> list[EquipmentUsageCount]: ...

    async def list_usages_for_export(self) -> list[Usage]: ...

    async def list_incidents_for_export(self) -> list[Incident]: ...
