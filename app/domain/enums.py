from enum import StrEnum


class Rol(StrEnum):
    ALUMNO = "ALUMNO"
    SOPORTE = "SOPORTE"
    ADMIN = "ADMIN"


class EstadoUso(StrEnum):
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"


class EstadoIncidencia(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_ATENCION = "EN_ATENCION"
    RESUELTA = "RESUELTA"
