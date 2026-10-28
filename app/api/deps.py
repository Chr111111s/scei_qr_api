from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.auth_service import AuthService
from app.application.services.equipos_service import EquiposService
from app.application.services.incidencias_service import IncidenciasService
from app.application.services.notificaciones_service import NotificacionesService
from app.application.services.reportes_service import ReportesService
from app.application.services.usos_service import UsosService
from app.application.services.usuarios_service import UsuariosService
from app.core.security import decode_access_token
from app.domain.enums import Rol
from app.domain.exceptions import ForbiddenError, UnauthorizedError
from app.infrastructure.db.repositories import (
    SqlAlchemyEquipmentRepository,
    SqlAlchemyIncidentRepository,
    SqlAlchemyReportRepository,
    SqlAlchemyUsageRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_session
from app.infrastructure.exports.pdf import PdfExporter
from app.infrastructure.exports.xlsx import XlsxExporter
from app.infrastructure.qr import QrCodeGenerator
from app.infrastructure.storage.local import LocalStorage

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    username: str
    role: Rol


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
        username = str(payload["username"])
        role = Rol(payload["role"])
    except Exception as exc:
        raise UnauthorizedError() from exc
    return CurrentUser(user_id=user_id, username=username, role=role)


def require_roles(*roles: Rol) -> Callable[..., Awaitable[CurrentUser]]:
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return dependency


def get_user_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_equipment_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyEquipmentRepository:
    return SqlAlchemyEquipmentRepository(session)


def get_usage_repository(session: AsyncSession = Depends(get_session)) -> SqlAlchemyUsageRepository:
    return SqlAlchemyUsageRepository(session)


def get_incident_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyIncidentRepository:
    return SqlAlchemyIncidentRepository(session)


def get_report_repository(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyReportRepository:
    return SqlAlchemyReportRepository(session)


def get_auth_service(
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(users)


def get_usuarios_service(
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UsuariosService:
    return UsuariosService(users)


def get_equipos_service(
    equipos: SqlAlchemyEquipmentRepository = Depends(get_equipment_repository),
) -> EquiposService:
    return EquiposService(equipos, QrCodeGenerator())


def get_usos_service(
    usos: SqlAlchemyUsageRepository = Depends(get_usage_repository),
    equipos: SqlAlchemyEquipmentRepository = Depends(get_equipment_repository),
) -> UsosService:
    return UsosService(usos, equipos)


def get_incidencias_service(
    incidencias: SqlAlchemyIncidentRepository = Depends(get_incident_repository),
    equipos: SqlAlchemyEquipmentRepository = Depends(get_equipment_repository),
) -> IncidenciasService:
    return IncidenciasService(incidencias, equipos)


def get_reportes_service(
    reports: SqlAlchemyReportRepository = Depends(get_report_repository),
) -> ReportesService:
    return ReportesService(reports, XlsxExporter(), PdfExporter())


def get_notificaciones_service(
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> NotificacionesService:
    return NotificacionesService(users)


def get_storage() -> LocalStorage:
    return LocalStorage()
