from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_usos_service, require_roles
from app.api.schemas import IniciarUsoRequest
from app.api.serializers import usage_public
from app.application.services.usos_service import UsosService
from app.domain.enums import Rol
from app.domain.exceptions import BadRequestError

router = APIRouter(prefix="/usos", tags=["usos"])
AlumnoUser = Annotated[CurrentUser, Depends(require_roles(Rol.ALUMNO))]
AdminUser = Annotated[CurrentUser, Depends(require_roles(Rol.ADMIN))]


@router.post("")
async def iniciar(
    body: IniciarUsoRequest,
    user: AlumnoUser,
    service: Annotated[UsosService, Depends(get_usos_service)],
) -> dict:
    usage = await service.iniciar(body.qr_token, user.user_id)
    return usage_public(usage)


@router.patch("/{usage_id}/finalizar")
async def finalizar(
    usage_id: int,
    user: AlumnoUser,
    service: Annotated[UsosService, Depends(get_usos_service)],
) -> dict:
    usage = await service.finalizar(usage_id, user.user_id)
    return usage_public(usage)


@router.get("/mis-registros")
async def mis_registros(
    user: AlumnoUser,
    service: Annotated[UsosService, Depends(get_usos_service)],
) -> list[dict]:
    usos = await service.mis_registros(user.user_id)
    return [usage_public(usage) for usage in usos]


@router.get("/historial")
async def historial(
    _: AdminUser,
    service: Annotated[UsosService, Depends(get_usos_service)],
    equipo_id: int = Query(alias="equipoId"),
    alumno_id: str | None = Query(default=None, alias="alumnoId"),
) -> list[dict]:
    parsed_alumno_id: int | None = None
    if alumno_id:
        try:
            parsed_alumno_id = int(alumno_id)
        except ValueError as exc:
            raise BadRequestError("alumnoId inválido") from exc
    usos = await service.historial(equipo_id, parsed_alumno_id)
    return [usage_public(usage, include_alumno=True) for usage in usos]
