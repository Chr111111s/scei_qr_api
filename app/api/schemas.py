from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import EstadoIncidencia, Rol

_FORMATO_CORREO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
_FORMATO_MATRICULA = r"^[A-Z0-9]{6,12}$"


def _normalizar_correo(value: str | None) -> str | None:
    return value.strip().lower() if isinstance(value, str) else value


def _normalizar_matricula(value: str | None) -> str | None:
    return value.strip().upper() if isinstance(value, str) else value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LoginRequest(StrictModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)


class CreateUsuarioRequest(StrictModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)
    full_name: str = Field(alias="fullName", min_length=1)
    correo: str | None = Field(default=None, pattern=_FORMATO_CORREO, max_length=254)
    matricula: str | None = Field(default=None, pattern=_FORMATO_MATRICULA)
    rol: Rol
    activo: bool | None = None

    @field_validator("correo", mode="before")
    @classmethod
    def normalizar_correo(cls, value: str | None) -> str | None:
        return _normalizar_correo(value)

    @field_validator("matricula", mode="before")
    @classmethod
    def normalizar_matricula(cls, value: str | None) -> str | None:
        return _normalizar_matricula(value)


class UpdateUsuarioRequest(StrictModel):
    username: str | None = Field(default=None, min_length=1)
    password: str | None = Field(default=None, min_length=6)
    full_name: str | None = Field(default=None, alias="fullName", min_length=1)
    correo: str | None = Field(default=None, pattern=_FORMATO_CORREO, max_length=254)
    matricula: str | None = Field(default=None, pattern=_FORMATO_MATRICULA)
    rol: Rol | None = None
    activo: bool | None = None

    @field_validator("correo", mode="before")
    @classmethod
    def normalizar_correo(cls, value: str | None) -> str | None:
        return _normalizar_correo(value)

    @field_validator("matricula", mode="before")
    @classmethod
    def normalizar_matricula(cls, value: str | None) -> str | None:
        return _normalizar_matricula(value)


class CreateEquipoRequest(StrictModel):
    codigo: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    descripcion: str | None = None
    ubicacion: str = Field(min_length=1)


class UpdateEquipoRequest(StrictModel):
    codigo: str | None = Field(default=None, min_length=1)
    nombre: str | None = Field(default=None, min_length=1)
    descripcion: str | None = None
    ubicacion: str | None = Field(default=None, min_length=1)
    activo: bool | None = None


class IniciarUsoRequest(StrictModel):
    qr_token: str = Field(alias="qrToken", min_length=1)


class CambiarEstadoRequest(StrictModel):
    estado: EstadoIncidencia


class RegistrarSolucionRequest(StrictModel):
    solucion: str = Field(min_length=1)


class RegistrarTokenRequest(StrictModel):
    token: str = Field(min_length=1)
