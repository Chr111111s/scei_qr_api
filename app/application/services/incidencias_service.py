from app.domain.entities import Incident
from app.domain.enums import EstadoIncidencia
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.ports.repositories import EquipmentRepository, IncidentRepository
from app.domain.rules import estados_permitidos


class IncidenciasService:
    def __init__(
        self,
        incidencias: IncidentRepository,
        equipos: EquipmentRepository,
    ) -> None:
        self.incidencias = incidencias
        self.equipos = equipos

    async def crear(
        self,
        *,
        equipo_id: int,
        titulo: str,
        descripcion: str,
        reportada_por_id: int,
        foto_url: str | None,
    ) -> Incident:
        equipo = await self.equipos.find_by_id(equipo_id)
        if equipo is None:
            raise NotFoundError(f"Equipo {equipo_id} no encontrado")
        return await self.incidencias.create(
            equipo_id=equipo_id,
            reportada_por_id=reportada_por_id,
            titulo=titulo,
            descripcion=descripcion,
            foto_url=foto_url,
        )

    async def mis_reportes(self, user_id: int) -> list[Incident]:
        return await self.incidencias.list_by_reporter(user_id)

    async def find_all(
        self, *, estado: EstadoIncidencia | None, equipo_id: int | None
    ) -> list[Incident]:
        return await self.incidencias.list_filtered(estado=estado, equipo_id=equipo_id)

    async def find_one(self, incident_id: int) -> Incident:
        incidencia = await self.incidencias.find_by_id(incident_id)
        if incidencia is None:
            raise NotFoundError(f"Incidencia {incident_id} no encontrada")
        return incidencia

    async def tomar(self, incident_id: int, tecnico_id: int) -> Incident:
        await self.find_one(incident_id)
        taken = await self.incidencias.take(incident_id, tecnico_id)
        if not taken:
            raise ConflictError("La incidencia ya fue tomada por otro técnico o cambió de estado")
        return await self.find_one(incident_id)

    async def cambiar_estado(self, incident_id: int, estado: EstadoIncidencia) -> Incident:
        incidencia = await self.find_one(incident_id)
        permitidas = estados_permitidos(incidencia.estado)
        if estado not in permitidas:
            validas = ", ".join(item.value for item in permitidas) or "ninguno (resuelta)"
            raise ConflictError(
                f"Transición no permitida: {incidencia.estado.value} → {estado.value}. "
                f"Estados válidos desde aquí: {validas}"
            )
        return await self.incidencias.change_state(incident_id, estado)

    async def registrar_solucion(
        self, incident_id: int, solucion: str, tecnico_id: int
    ) -> Incident:
        incidencia = await self.find_one(incident_id)
        if incidencia.estado != EstadoIncidencia.EN_ATENCION:
            raise ConflictError(
                "Solo puede registrarse solución en una incidencia EN_ATENCION. "
                f"Estado actual: {incidencia.estado.value}."
            )
        effective_technician = incidencia.atendida_por_id or tecnico_id
        return await self.incidencias.add_solution(incident_id, solucion, effective_technician)

    async def historial(
        self, *, estado: EstadoIncidencia | None, tecnico_id: int | None
    ) -> list[Incident]:
        return await self.incidencias.list_history(estado=estado, tecnico_id=tecnico_id)
