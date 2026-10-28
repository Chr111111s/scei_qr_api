from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    get_current_user,
    get_notificaciones_service,
)
from app.api.schemas import RegistrarTokenRequest
from app.application.services.notificaciones_service import NotificacionesService

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/token", status_code=status.HTTP_201_CREATED)
async def registrar_token(
    body: RegistrarTokenRequest,
    user: AuthenticatedUser,
    service: Annotated[NotificacionesService, Depends(get_notificaciones_service)],
) -> dict[str, bool]:
    return await service.registrar_token(user.user_id, body.token)
