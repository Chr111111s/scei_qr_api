from typing import Any
from uuid import uuid4

from app.domain.entities import Equipment
from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.ports.repositories import EquipmentRepository
from app.domain.ports.storage import QrGeneratorPort


class EquiposService:
    def __init__(self, equipos: EquipmentRepository, qr_generator: QrGeneratorPort) -> None:
        self.equipos = equipos
        self.qr_generator = qr_generator

    async def find_all(
        self, *, activo: bool | None, q: str | None, ubicacion: str | None
    ) -> list[Equipment]:
        return await self.equipos.find_all(activo=activo, q=q, ubicacion=ubicacion)

    async def find_one(self, equipment_id: int) -> Equipment:
        equipo = await self.equipos.find_by_id(equipment_id)
        if equipo is None:
            raise NotFoundError(f"Equipo {equipment_id} no encontrado")
        return equipo

    async def create(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        ubicacion: str,
    ) -> Equipment:
        if await self.equipos.find_by_code(codigo) is not None:
            raise ConflictError(f'El código "{codigo}" ya está registrado')
        return await self.equipos.create(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            ubicacion=ubicacion,
            qr_token=str(uuid4()),
        )

    async def update(self, equipment_id: int, values: dict[str, Any]) -> Equipment:
        await self.find_one(equipment_id)
        codigo = values.get("codigo")
        if codigo is not None:
            existing = await self.equipos.find_by_code(codigo)
            if existing is not None and existing.id != equipment_id:
                raise ConflictError(f'El código "{codigo}" ya está registrado')
        return await self.equipos.update(equipment_id, values)

    async def get_qr_image(self, equipment_id: int, format: str) -> tuple[bytes, str]:
        equipo = await self.find_one(equipment_id)
        if format == "svg":
            return self.qr_generator.svg(equipo.qr_token), "image/svg+xml"
        return self.qr_generator.png(equipo.qr_token), "image/png"

    async def resolve_qr_token(self, qr_token: str) -> Equipment:
        equipo = await self.equipos.find_by_qr_token(qr_token)
        if equipo is None or not equipo.activo:
            raise NotFoundError("QR no válido o equipo inactivo")
        return equipo

    async def regenerate_qr(self, equipment_id: int) -> Equipment:
        await self.find_one(equipment_id)
        return await self.equipos.update_qr_token(equipment_id, str(uuid4()))
