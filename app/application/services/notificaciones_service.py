from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.ports.repositories import UserRepository


class NotificacionesService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def registrar_token(self, user_id: int, token: str) -> dict[str, bool]:
        existing = await self.users.find_by_fcm_token(token)
        if existing is not None and existing.id != user_id:
            raise ConflictError("El token FCM ya está registrado en otro usuario")
        updated = await self.users.update_fcm_token(user_id, token)
        if not updated:
            raise NotFoundError(f"Usuario {user_id} no encontrado")
        return {"registered": True}
