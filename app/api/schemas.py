from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoIncidencia, Rol


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LoginRequest(StrictModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)


class CreateUsuarioRequest(StrictModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)
    full_name: str = Field(alias="fullName", min_length=1)
    rol: Rol
    activo: bool | None = None


class UpdateUsuarioRequest(StrictModel):
    username: str | None = Field(default=None, min_length=1)
    password: str | None = Field(default=None, min_length=6)
    full_name: str | None = Field(default=None, alias="fullName", min_length=1)
    rol: Rol | None = None
    activo: bool | None = None


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
