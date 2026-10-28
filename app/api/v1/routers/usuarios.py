from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, get_usuarios_service, require_roles
from app.api.schemas import CreateUsuarioRequest, UpdateUsuarioRequest
from app.api.serializers import user_public
from app.application.services.usuarios_service import UsuariosService
from app.domain.enums import Rol

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
AdminUser = Annotated[CurrentUser, Depends(require_roles(Rol.ADMIN))]


@router.get("")
async def listar(
    _: AdminUser,
    service: Annotated[UsuariosService, Depends(get_usuarios_service)],
    rol: str | None = Query(default=None),
    activo: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[dict]:
    rol_filter: Rol | None = None
    if rol:
        try:
            rol_filter = Rol(rol)
        except ValueError:
            rol_filter = None
    activo_filter = None if activo is None else activo == "true"
    users = await service.find_all(rol=rol_filter, activo=activo_filter, q=q or None)
    return [user_public(user) for user in users]


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(
    body: CreateUsuarioRequest,
    _: AdminUser,
    service: Annotated[UsuariosService, Depends(get_usuarios_service)],
) -> dict:
    user = await service.create(
        username=body.username,
        password=body.password,
        full_name=body.full_name,
        rol=body.rol,
        activo=body.activo,
    )
    return user_public(user)


@router.get("/{user_id}")
async def detalle(
    user_id: int,
    _: AdminUser,
    service: Annotated[UsuariosService, Depends(get_usuarios_service)],
) -> dict:
    return user_public(await service.find_one(user_id))


@router.patch("/{user_id}")
async def actualizar(
    user_id: int,
    body: UpdateUsuarioRequest,
    _: AdminUser,
    service: Annotated[UsuariosService, Depends(get_usuarios_service)],
) -> dict:
    values = body.model_dump(exclude_unset=True)
    password = values.pop("password", None)
    user = await service.update(user_id, values=values, password=password)
    return user_public(user)
