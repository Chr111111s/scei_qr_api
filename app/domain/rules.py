from app.domain.enums import EstadoIncidencia

TRANSICIONES_VALIDAS: dict[EstadoIncidencia, list[EstadoIncidencia]] = {
    EstadoIncidencia.PENDIENTE: [EstadoIncidencia.EN_ATENCION],
    EstadoIncidencia.EN_ATENCION: [EstadoIncidencia.RESUELTA],
    EstadoIncidencia.RESUELTA: [],
}


def estados_permitidos(estado: EstadoIncidencia) -> list[EstadoIncidencia]:
    return TRANSICIONES_VALIDAS[estado]
