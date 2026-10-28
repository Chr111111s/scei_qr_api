from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_auth_service, get_current_user
from app.api.schemas import LoginRequest
from app.api.serializers import auth_user
from app.application.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    token, expires_in, user = await service.login(body.username, body.password)
    return {
        "accessToken": token,
        "tokenType": "Bearer",
        "expiresIn": expires_in,
        "user": auth_user(user),
    }


@router.post("/logout")
async def logout(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    return await service.logout(user.user_id)
