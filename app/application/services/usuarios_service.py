from typing import Any

from app.core.security import hash_password
from app.domain.entities import User
from app.domain.enums import Rol
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.ports.repositories import UserRepository


class UsuariosService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def find_all(self, *, rol: Rol | None, activo: bool | None, q: str | None) -> list[User]:
        return await self.users.find_all(rol=rol, activo=activo, q=q)

    async def find_one(self, user_id: int) -> User:
        user = await self.users.find_by_id(user_id)
        if user is None:
            raise NotFoundError(f"Usuario {user_id} no encontrado")
        return user

    async def create(
        self,
        *,
        username: str,
        password: str,
        full_name: str,
        rol: Rol,
        activo: bool | None,
    ) -> User:
        if await self.users.exists_username(username):
            raise ConflictError(f'El usuario "{username}" ya existe')
        return await self.users.create(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            rol=rol,
            activo=True if activo is None else activo,
        )

    async def update(
        self,
        user_id: int,
        *,
        values: dict[str, Any],
        password: str | None,
    ) -> User:
        await self.find_one(user_id)

        username = values.get("username")
        if username is not None and await self.users.exists_username(username, exclude_id=user_id):
            raise ConflictError(f'El usuario "{username}" ya existe')

        clean_values = {key: value for key, value in values.items() if value is not None}
        if password:
            clean_values["password_hash"] = hash_password(password)
        return await self.users.update(user_id, clean_values)
