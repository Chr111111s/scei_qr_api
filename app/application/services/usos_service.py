from app.domain.entities import Usage
from app.domain.enums import EstadoUso
from app.domain.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.domain.ports.repositories import EquipmentRepository, UsageRepository


class UsosService:
    def __init__(self, usos: UsageRepository, equipos: EquipmentRepository) -> None:
        self.usos = usos
        self.equipos = equipos

    async def iniciar(self, qr_token: str, alumno_id: int) -> Usage:
        equipo = await self.equipos.find_by_qr_token(qr_token)
        if equipo is None or not equipo.activo:
            raise NotFoundError("QR no válido o equipo inactivo")

        uso_activo = await self.usos.find_active_by_alumno(alumno_id)
        if uso_activo is not None:
            if uso_activo.equipo_id == equipo.id:
                message = (
                    "Ya tiene un uso activo para este equipo. Finalícelo antes de iniciar otro."
                )
            else:
                codigo = uso_activo.equipo.codigo if uso_activo.equipo else uso_activo.equipo_id
                message = (
                    f'Ya tiene un uso activo del equipo "{codigo}". '
                    "Finalícelo antes de escanear otro QR."
                )
            raise ConflictError(message)

        return await self.usos.create(alumno_id=alumno_id, equipo_id=equipo.id)

    async def finalizar(self, usage_id: int, alumno_id: int) -> Usage:
        uso = await self.usos.find_by_id(usage_id)
        if uso is None:
            raise NotFoundError(f"Uso {usage_id} no encontrado")
        if uso.alumno_id != alumno_id:
            raise ForbiddenError("Solo puede finalizar sus propios usos")
        if uso.estado == EstadoUso.FINALIZADO:
            raise ConflictError("El uso ya fue finalizado")
        return await self.usos.finalize(usage_id)

    async def mis_registros(self, alumno_id: int) -> list[Usage]:
        return await self.usos.list_by_alumno(alumno_id)

    async def historial(self, equipo_id: int, alumno_id: int | None) -> list[Usage]:
        return await self.usos.list_history(equipo_id=equipo_id, alumno_id=alumno_id)
