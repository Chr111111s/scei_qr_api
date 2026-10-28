from datetime import UTC, datetime
from typing import Any, overload

from app.domain.entities import Equipment, Incident, Usage, User, UserSummary


def iso_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def auth_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "fullName": user.full_name,
        "rol": user.rol.value,
    }


def user_public(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "fullName": user.full_name,
        "rol": user.rol.value,
        "activo": user.activo,
        "createdAt": iso_timestamp(user.created_at),
    }


def user_summary(user: UserSummary | None) -> dict[str, Any] | None:
    if user is None:
        return None
    return {"id": user.id, "username": user.username, "fullName": user.full_name}


@overload
def equipment_public(equipment: Equipment) -> dict[str, Any]: ...


@overload
def equipment_public(equipment: None) -> None: ...


def equipment_public(equipment: Equipment | None) -> dict[str, Any] | None:
    if equipment is None:
        return None
    return {
        "id": equipment.id,
        "codigo": equipment.codigo,
        "nombre": equipment.nombre,
        "descripcion": equipment.descripcion,
        "ubicacion": equipment.ubicacion,
        "qrToken": equipment.qr_token,
        "activo": equipment.activo,
        "createdAt": iso_timestamp(equipment.created_at),
    }


def usage_public(usage: Usage, *, include_alumno: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": usage.id,
        "alumnoId": usage.alumno_id,
        "equipoId": usage.equipo_id,
        "inicio": iso_timestamp(usage.inicio),
        "fin": iso_timestamp(usage.fin),
        "estado": usage.estado.value,
        "equipo": equipment_public(usage.equipo),
    }
    if include_alumno:
        payload["alumno"] = user_summary(usage.alumno)
    return payload


def incident_public(incident: Incident) -> dict[str, Any]:
    return {
        "id": incident.id,
        "equipoId": incident.equipo_id,
        "reportadaPorId": incident.reportada_por_id,
        "atendidaPorId": incident.atendida_por_id,
        "titulo": incident.titulo,
        "descripcion": incident.descripcion,
        "fotoUrl": incident.foto_url,
        "estado": incident.estado.value,
        "solucion": incident.solucion,
        "creadaEn": iso_timestamp(incident.creada_en),
        "actualizadaEn": iso_timestamp(incident.actualizada_en),
        "equipo": equipment_public(incident.equipo),
        "reportadaPor": user_summary(incident.reportada_por),
        "atendidaPor": user_summary(incident.atendida_por),
    }
