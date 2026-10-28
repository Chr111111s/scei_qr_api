from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import (
    CurrentUser,
    get_current_user,
    get_incidencias_service,
    get_storage,
    require_roles,
)
from app.api.schemas import CambiarEstadoRequest, RegistrarSolucionRequest
from app.api.serializers import incident_public
from app.application.services.incidencias_service import IncidenciasService
from app.domain.enums import EstadoIncidencia, Rol
from app.domain.exceptions import BadRequestError
from app.infrastructure.storage.local import LocalStorage

router = APIRouter(prefix="/incidencias", tags=["incidencias"])
AlumnoUser = Annotated[CurrentUser, Depends(require_roles(Rol.ALUMNO))]
SupportUser = Annotated[CurrentUser, Depends(require_roles(Rol.SOPORTE))]
SupportOrAdminUser = Annotated[CurrentUser, Depends(require_roles(Rol.SOPORTE, Rol.ADMIN))]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]

_MAX_READ_BYTES = 5 * 1024 * 1024 + 1


@router.post("")
async def crear(
    user: AlumnoUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
    storage: Annotated[LocalStorage, Depends(get_storage)],
    equipo_id: Annotated[str, Form(alias="equipoId")],
    titulo: Annotated[str, Form()],
    descripcion: Annotated[str, Form()],
    foto: Annotated[UploadFile | None, File()] = None,
) -> dict:
    try:
        parsed_equipment_id = int(equipo_id)
    except ValueError as exc:
        raise BadRequestError("equipoId inválido") from exc

    foto_url: str | None = None
    if foto is not None:
        data = await foto.read(_MAX_READ_BYTES)
        foto_url = await storage.save_incident_photo(
            original_name=foto.filename or "",
            content_type=foto.content_type or "",
            data=data,
        )

    incident = await service.crear(
        equipo_id=parsed_equipment_id,
        titulo=titulo,
        descripcion=descripcion,
        reportada_por_id=user.user_id,
        foto_url=foto_url,
    )
    return incident_public(incident)


@router.get("/mis-reportes")
async def mis_reportes(
    user: AlumnoUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
) -> list[dict]:
    incidents = await service.mis_reportes(user.user_id)
    return [incident_public(incident) for incident in incidents]


@router.get("")
async def listar(
    _: SupportOrAdminUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
    estado: EstadoIncidencia | None = Query(default=None),
    equipo_id: str | None = Query(default=None, alias="equipoId"),
) -> list[dict]:
    parsed_equipment_id: int | None = None
    if equipo_id:
        try:
            parsed_equipment_id = int(equipo_id)
        except ValueError as exc:
            raise BadRequestError("equipoId inválido") from exc
    incidents = await service.find_all(estado=estado, equipo_id=parsed_equipment_id)
    return [incident_public(incident) for incident in incidents]


@router.get("/historial")
async def historial(
    _: SupportOrAdminUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
    estado: str | None = Query(default=None),
    tecnico_id: str | None = Query(default=None, alias="tecnicoId"),
) -> list[dict]:
    estado_filter: EstadoIncidencia | None = None
    if estado:
        try:
            estado_filter = EstadoIncidencia(estado)
        except ValueError:
            estado_filter = None

    tecnico_filter: int | None = None
    if tecnico_id:
        try:
            tecnico_filter = int(tecnico_id)
        except ValueError as exc:
            raise BadRequestError("tecnicoId inválido") from exc

    incidents = await service.historial(estado=estado_filter, tecnico_id=tecnico_filter)
    return [incident_public(incident) for incident in incidents]


@router.get("/{incident_id}")
async def detalle(
    incident_id: int,
    _: AuthenticatedUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
) -> dict:
    return incident_public(await service.find_one(incident_id))


@router.patch("/{incident_id}/tomar")
async def tomar(
    incident_id: int,
    user: SupportUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
) -> dict:
    return incident_public(await service.tomar(incident_id, user.user_id))


@router.patch("/{incident_id}/estado")
async def cambiar_estado(
    incident_id: int,
    body: CambiarEstadoRequest,
    _: SupportUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
) -> dict:
    return incident_public(await service.cambiar_estado(incident_id, body.estado))


@router.patch("/{incident_id}/solucion")
async def registrar_solucion(
    incident_id: int,
    body: RegistrarSolucionRequest,
    user: SupportUser,
    service: Annotated[IncidenciasService, Depends(get_incidencias_service)],
) -> dict:
    incident = await service.registrar_solucion(incident_id, body.solucion, user.user_id)
    return incident_public(incident)
