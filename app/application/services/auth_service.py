from app.core.security import create_access_token, verify_password
from app.domain.entities import User
from app.domain.exceptions import UnauthorizedError
from app.domain.ports.repositories import UserRepository


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def login(self, username: str, password: str) -> tuple[str, int, User]:
        user = await self.users.find_by_username(username)
        if user is None or not user.activo or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Usuario o contraseña incorrectos")

        token, expires_in = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.rol.value,
        )
        return token, expires_in, user

    async def logout(self, user_id: int) -> dict[str, str]:
        # Stateless JWT: the client discards the token. Endpoint kept for symmetry.
        del user_id
        return {"message": "Sesión cerrada"}
