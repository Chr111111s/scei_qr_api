from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities import (
    Equipment,
    EquipmentUsageCount,
    Incident,
    Usage,
    User,
    UserSummary,
)
from app.domain.enums import EstadoIncidencia, EstadoUso, Rol
from app.infrastructure.db.base import utcnow
from app.infrastructure.db.models import Equipo, Incidencia, Uso, Usuario


def _user(row: Usuario) -> User:
    return User(
        id=row.id,
        username=row.username,
        password_hash=row.password_hash,
        full_name=row.full_name,
        rol=Rol(row.rol),
        activo=row.activo,
        fcm_token=row.fcm_token,
        created_at=row.created_at,
    )


def _equipment(row: Equipo) -> Equipment:
    return Equipment(
        id=row.id,
        codigo=row.codigo,
        nombre=row.nombre,
        descripcion=row.descripcion,
        ubicacion=row.ubicacion,
        qr_token=row.qr_token,
        activo=row.activo,
        created_at=row.created_at,
    )


def _summary(row: Usuario | None) -> UserSummary | None:
    if row is None:
        return None
    return UserSummary(id=row.id, username=row.username, full_name=row.full_name)


def _usage(row: Uso) -> Usage:
    return Usage(
        id=row.id,
        alumno_id=row.alumno_id,
        equipo_id=row.equipo_id,
        inicio=row.inicio,
        fin=row.fin,
        estado=EstadoUso(row.estado),
        equipo=_equipment(row.equipo) if row.equipo is not None else None,
        alumno=_summary(row.alumno) if row.alumno is not None else None,
    )


def _incident(row: Incidencia) -> Incident:
    return Incident(
        id=row.id,
        equipo_id=row.equipo_id,
        reportada_por_id=row.reportada_por_id,
        atendida_por_id=row.atendida_por_id,
        titulo=row.titulo,
        descripcion=row.descripcion,
        foto_url=row.foto_url,
        estado=EstadoIncidencia(row.estado),
        solucion=row.solucion,
        creada_en=row.creada_en,
        actualizada_en=row.actualizada_en,
        equipo=_equipment(row.equipo) if row.equipo is not None else None,
        reportada_por=_summary(row.reportada_por),
        atendida_por=_summary(row.atendida_por),
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_all(self, *, rol: Rol | None, activo: bool | None, q: str | None) -> list[User]:
        stmt = select(Usuario)
        if rol is not None:
            stmt = stmt.where(Usuario.rol == rol)
        if activo is not None:
            stmt = stmt.where(Usuario.activo == activo)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(Usuario.username.ilike(pattern), Usuario.full_name.ilike(pattern))
            )
        stmt = stmt.order_by(Usuario.id.asc())
        result = await self.session.execute(stmt)
        return [_user(row) for row in result.scalars().all()]

    async def find_by_id(self, user_id: int) -> User | None:
        row = await self.session.get(Usuario, user_id)
        return _user(row) if row else None

    async def find_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(Usuario).where(Usuario.username == username))
        row = result.scalar_one_or_none()
        return _user(row) if row else None

    async def find_by_fcm_token(self, token: str) -> User | None:
        result = await self.session.execute(select(Usuario).where(Usuario.fcm_token == token))
        row = result.scalar_one_or_none()
        return _user(row) if row else None

    async def exists_username(self, username: str, *, exclude_id: int | None = None) -> bool:
        stmt = select(Usuario.id).where(Usuario.username == username)
        if exclude_id is not None:
            stmt = stmt.where(Usuario.id != exclude_id)
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        full_name: str,
        rol: Rol,
        activo: bool,
    ) -> User:
        row = Usuario(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            rol=rol,
            activo=activo,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return _user(row)

    async def update(self, user_id: int, values: dict[str, Any]) -> User:
        row = await self.session.get(Usuario, user_id)
        if row is None:
            raise LookupError(user_id)
        for key, value in values.items():
            setattr(row, key, value)
        await self.session.commit()
        await self.session.refresh(row)
        return _user(row)

    async def update_fcm_token(self, user_id: int, token: str) -> bool:
        row = await self.session.get(Usuario, user_id)
        if row is None:
            return False
        row.fcm_token = token
        await self.session.commit()
        return True


class SqlAlchemyEquipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_all(
        self,
        *,
        activo: bool | None,
        q: str | None,
        ubicacion: str | None,
    ) -> list[Equipment]:
        stmt = select(Equipo)
        if activo is not None:
            stmt = stmt.where(Equipo.activo == activo)
        if ubicacion:
            stmt = stmt.where(Equipo.ubicacion.ilike(f"%{ubicacion}%"))
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(or_(Equipo.codigo.ilike(pattern), Equipo.nombre.ilike(pattern)))
        stmt = stmt.order_by(Equipo.codigo.asc())
        result = await self.session.execute(stmt)
        return [_equipment(row) for row in result.scalars().all()]

    async def find_by_id(self, equipment_id: int) -> Equipment | None:
        row = await self.session.get(Equipo, equipment_id)
        return _equipment(row) if row else None

    async def find_by_code(self, codigo: str) -> Equipment | None:
        result = await self.session.execute(select(Equipo).where(Equipo.codigo == codigo))
        row = result.scalar_one_or_none()
        return _equipment(row) if row else None

    async def find_by_qr_token(self, qr_token: str) -> Equipment | None:
        result = await self.session.execute(select(Equipo).where(Equipo.qr_token == qr_token))
        row = result.scalar_one_or_none()
        return _equipment(row) if row else None

    async def create(
        self,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        ubicacion: str,
        qr_token: str,
    ) -> Equipment:
        row = Equipo(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            ubicacion=ubicacion,
            qr_token=qr_token,
            activo=True,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return _equipment(row)

    async def update(self, equipment_id: int, values: dict[str, Any]) -> Equipment:
        row = await self.session.get(Equipo, equipment_id)
        if row is None:
            raise LookupError(equipment_id)
        for key, value in values.items():
            setattr(row, key, value)
        await self.session.commit()
        await self.session.refresh(row)
        return _equipment(row)

    async def update_qr_token(self, equipment_id: int, qr_token: str) -> Equipment:
        return await self.update(equipment_id, {"qr_token": qr_token})


class SqlAlchemyUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_active_by_alumno(self, alumno_id: int) -> Usage | None:
        stmt = (
            select(Uso)
            .where(Uso.alumno_id == alumno_id, Uso.estado == EstadoUso.ACTIVO)
            .options(selectinload(Uso.equipo), selectinload(Uso.alumno))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return _usage(row) if row else None

    async def find_by_id(self, usage_id: int) -> Usage | None:
        stmt = (
            select(Uso)
            .where(Uso.id == usage_id)
            .options(selectinload(Uso.equipo), selectinload(Uso.alumno))
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return _usage(row) if row else None

    async def create(self, *, alumno_id: int, equipo_id: int) -> Usage:
        row = Uso(
            alumno_id=alumno_id,
            equipo_id=equipo_id,
            inicio=utcnow(),
            estado=EstadoUso.ACTIVO,
        )
        self.session.add(row)
        await self.session.commit()
        created = await self.find_by_id(row.id)
        assert created is not None
        return created

    async def finalize(self, usage_id: int) -> Usage:
        await self.session.execute(
            update(Uso).where(Uso.id == usage_id).values(fin=utcnow(), estado=EstadoUso.FINALIZADO)
        )
        await self.session.commit()
        updated = await self.find_by_id(usage_id)
        assert updated is not None
        return updated

    async def list_by_alumno(self, alumno_id: int) -> list[Usage]:
        stmt = (
            select(Uso)
            .where(Uso.alumno_id == alumno_id)
            .options(selectinload(Uso.equipo), selectinload(Uso.alumno))
            .order_by(Uso.inicio.desc())
        )
        result = await self.session.execute(stmt)
        return [_usage(row) for row in result.scalars().all()]

    async def list_history(self, *, equipo_id: int, alumno_id: int | None) -> list[Usage]:
        stmt = (
            select(Uso)
            .where(Uso.equipo_id == equipo_id)
            .options(selectinload(Uso.equipo), selectinload(Uso.alumno))
            .order_by(Uso.inicio.desc())
        )
        if alumno_id is not None:
            stmt = stmt.where(Uso.alumno_id == alumno_id)
        result = await self.session.execute(stmt)
        return [_usage(row) for row in result.scalars().all()]


class SqlAlchemyIncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _load_options():
        return (
            selectinload(Incidencia.equipo),
            selectinload(Incidencia.reportada_por),
            selectinload(Incidencia.atendida_por),
        )

    async def create(
        self,
        *,
        equipo_id: int,
        reportada_por_id: int,
        titulo: str,
        descripcion: str,
        foto_url: str | None,
    ) -> Incident:
        now = utcnow()
        row = Incidencia(
            equipo_id=equipo_id,
            reportada_por_id=reportada_por_id,
            titulo=titulo,
            descripcion=descripcion,
            foto_url=foto_url,
            estado=EstadoIncidencia.PENDIENTE,
            creada_en=now,
            actualizada_en=now,
        )
        self.session.add(row)
        await self.session.commit()
        created = await self.find_by_id(row.id)
        assert created is not None
        return created

    async def find_by_id(self, incident_id: int) -> Incident | None:
        stmt = select(Incidencia).where(Incidencia.id == incident_id).options(*self._load_options())
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return _incident(row) if row else None

    async def list_by_reporter(self, user_id: int) -> list[Incident]:
        stmt = (
            select(Incidencia)
            .where(Incidencia.reportada_por_id == user_id)
            .options(*self._load_options())
            .order_by(Incidencia.creada_en.desc())
        )
        result = await self.session.execute(stmt)
        return [_incident(row) for row in result.scalars().all()]

    async def list_filtered(
        self, *, estado: EstadoIncidencia | None, equipo_id: int | None
    ) -> list[Incident]:
        stmt = select(Incidencia).options(*self._load_options())
        if estado is not None:
            stmt = stmt.where(Incidencia.estado == estado)
        if equipo_id is not None:
            stmt = stmt.where(Incidencia.equipo_id == equipo_id)
        stmt = stmt.order_by(Incidencia.creada_en.desc())
        result = await self.session.execute(stmt)
        return [_incident(row) for row in result.scalars().all()]

    async def list_history(
        self, *, estado: EstadoIncidencia | None, tecnico_id: int | None
    ) -> list[Incident]:
        stmt = select(Incidencia).options(*self._load_options())
        if estado is not None:
            stmt = stmt.where(Incidencia.estado == estado)
        if tecnico_id is not None:
            stmt = stmt.where(Incidencia.atendida_por_id == tecnico_id)
        stmt = stmt.order_by(Incidencia.actualizada_en.desc())
        result = await self.session.execute(stmt)
        return [_incident(row) for row in result.scalars().all()]

    async def take(self, incident_id: int, tecnico_id: int) -> bool:
        result = await self.session.execute(
            update(Incidencia)
            .where(
                Incidencia.id == incident_id,
                Incidencia.estado == EstadoIncidencia.PENDIENTE,
            )
            .values(
                estado=EstadoIncidencia.EN_ATENCION,
                atendida_por_id=tecnico_id,
                actualizada_en=utcnow(),
            )
            .returning(Incidencia.id)
        )
        await self.session.commit()
        return result.scalar_one_or_none() is not None

    async def change_state(self, incident_id: int, estado: EstadoIncidencia) -> Incident:
        await self.session.execute(
            update(Incidencia)
            .where(Incidencia.id == incident_id)
            .values(estado=estado, actualizada_en=utcnow())
        )
        await self.session.commit()
        updated = await self.find_by_id(incident_id)
        assert updated is not None
        return updated

    async def add_solution(self, incident_id: int, solucion: str, tecnico_id: int) -> Incident:
        await self.session.execute(
            update(Incidencia)
            .where(Incidencia.id == incident_id)
            .values(
                estado=EstadoIncidencia.RESUELTA,
                solucion=solucion,
                atendida_por_id=tecnico_id,
                actualizada_en=utcnow(),
            )
        )
        await self.session.commit()
        updated = await self.find_by_id(incident_id)
        assert updated is not None
        return updated


class SqlAlchemyReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _count(self, model: type, *conditions: Any) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_estadisticas(self) -> dict[str, Any]:
        total_equipos = await self._count(Equipo)
        equipos_activos = await self._count(Equipo, Equipo.activo.is_(True))
        total_usuarios = await self._count(Usuario)
        alumnos = await self._count(Usuario, Usuario.rol == Rol.ALUMNO)
        soportes = await self._count(Usuario, Usuario.rol == Rol.SOPORTE)
        admins = await self._count(Usuario, Usuario.rol == Rol.ADMIN)
        usos_activos = await self._count(Uso, Uso.estado == EstadoUso.ACTIVO)
        usos_finalizados = await self._count(Uso, Uso.estado == EstadoUso.FINALIZADO)
        pendientes = await self._count(Incidencia, Incidencia.estado == EstadoIncidencia.PENDIENTE)
        en_atencion = await self._count(
            Incidencia, Incidencia.estado == EstadoIncidencia.EN_ATENCION
        )
        resueltas = await self._count(Incidencia, Incidencia.estado == EstadoIncidencia.RESUELTA)

        grouped = await self.session.execute(
            select(Uso.equipo_id, func.count().label("total"))
            .group_by(Uso.equipo_id)
            .order_by(func.count().desc())
            .limit(10)
        )
        grouped_rows = grouped.all()
        equipo_ids = [row.equipo_id for row in grouped_rows]
        equipos_map: dict[int, Equipment] = {}
        if equipo_ids:
            result = await self.session.execute(select(Equipo).where(Equipo.id.in_(equipo_ids)))
            equipos_map = {row.id: _equipment(row) for row in result.scalars().all()}
        usos_por_equipo = [
            {
                "equipo": _equipment_dict(equipos_map.get(row.equipo_id)),
                "totalUsos": int(row.total),
            }
            for row in grouped_rows
        ]

        grouped_tecnicos = await self.session.execute(
            select(Incidencia.atendida_por_id, func.count().label("total"))
            .where(Incidencia.atendida_por_id.is_not(None))
            .group_by(Incidencia.atendida_por_id)
        )
        tecnico_rows = grouped_tecnicos.all()
        tecnico_ids = [row.atendida_por_id for row in tecnico_rows if row.atendida_por_id]
        tecnicos_map: dict[int, UserSummary] = {}
        if tecnico_ids:
            tecnicos_result = await self.session.execute(
                select(Usuario).where(Usuario.id.in_(tecnico_ids))
            )
            tecnicos_map = {
                row.id: UserSummary(id=row.id, username=row.username, full_name=row.full_name)
                for row in tecnicos_result.scalars().all()
            }
        incidencias_por_tecnico = [
            {
                "tecnico": (
                    _summary_dict(tecnicos_map.get(row.atendida_por_id))
                    if row.atendida_por_id
                    else None
                ),
                "totalAtendidas": int(row.total),
            }
            for row in tecnico_rows
        ]

        return {
            "equipos": {"total": total_equipos, "activos": equipos_activos},
            "usuarios": {
                "total": total_usuarios,
                "alumnos": alumnos,
                "soportes": soportes,
                "admins": admins,
            },
            "usos": {"activos": usos_activos, "finalizados": usos_finalizados},
            "incidencias": {
                "pendientes": pendientes,
                "enAtencion": en_atencion,
                "resueltas": resueltas,
            },
            "usosPorEquipo": usos_por_equipo,
            "incidenciasPorTecnico": incidencias_por_tecnico,
        }

    async def get_equipment_usage_counts(self) -> list[EquipmentUsageCount]:
        usos_count = (
            select(func.count(Uso.id))
            .where(Uso.equipo_id == Equipo.id)
            .correlate(Equipo)
            .scalar_subquery()
        )
        inc_count = (
            select(func.count(Incidencia.id))
            .where(Incidencia.equipo_id == Equipo.id)
            .correlate(Equipo)
            .scalar_subquery()
        )
        stmt = select(Equipo, usos_count, inc_count).order_by(Equipo.id.asc())
        result = await self.session.execute(stmt)
        return [
            EquipmentUsageCount(
                equipment=_equipment(row[0]),
                usos=int(row[1]),
                incidencias=int(row[2]),
            )
            for row in result.all()
        ]

    async def list_usages_for_export(self) -> list[Usage]:
        stmt = (
            select(Uso)
            .options(selectinload(Uso.equipo), selectinload(Uso.alumno))
            .order_by(Uso.inicio.desc())
        )
        result = await self.session.execute(stmt)
        return [_usage(row) for row in result.scalars().all()]

    async def list_incidents_for_export(self) -> list[Incident]:
        stmt = (
            select(Incidencia)
            .options(
                selectinload(Incidencia.equipo),
                selectinload(Incidencia.reportada_por),
                selectinload(Incidencia.atendida_por),
            )
            .order_by(Incidencia.creada_en.desc())
        )
        result = await self.session.execute(stmt)
        return [_incident(row) for row in result.scalars().all()]


def _equipment_dict(equipment: Equipment | None) -> dict[str, Any] | None:
    if equipment is None:
        return None
    return {
        "id": equipment.id,
        "codigo": equipment.codigo,
        "nombre": equipment.nombre,
    }


def _summary_dict(user: UserSummary | None) -> dict[str, Any] | None:
    if user is None:
        return None
    return {"id": user.id, "username": user.username, "fullName": user.full_name}
