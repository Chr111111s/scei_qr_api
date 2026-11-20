import re
import unicodedata
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import (
    CurrentUser,
    get_current_user,
    get_equipos_service,
    require_roles,
)
from app.api.schemas import CreateEquipoRequest, UpdateEquipoRequest
from app.api.serializers import equipment_public
from app.application.services.equipos_service import EquiposService
from app.domain.enums import Rol

router = APIRouter(prefix="/equipos", tags=["equipos"])
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
AdminUser = Annotated[CurrentUser, Depends(require_roles(Rol.ADMIN))]


@router.get("")
async def listar(
    _: AuthenticatedUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
    activo: str | None = Query(default=None),
    q: str | None = Query(default=None),
    ubicacion: str | None = Query(default=None),
    laboratorio: str | None = Query(default=None),
) -> list[dict]:
    activo_filter = None if activo is None else activo == "true"
    equipos = await service.find_all(
        activo=activo_filter,
        q=q or None,
        ubicacion=ubicacion or None,
        laboratorio=laboratorio or None,
    )
    return [equipment_public(equipo) for equipo in equipos]


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(
    body: CreateEquipoRequest,
    _: AdminUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
) -> dict:
    equipo = await service.create(
        codigo=body.codigo,
        nombre=body.nombre,
        descripcion=body.descripcion,
        ubicacion=body.ubicacion,
        laboratorio=body.laboratorio,
    )
    return equipment_public(equipo)


@router.get("/etiquetas")
async def etiquetas_por_lote(
    _: AdminUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
    laboratorio: str | None = Query(default=None),
    ubicacion: str | None = Query(default=None),
    activo: bool | None = Query(default=True),
) -> Response:
    """HU-AD-07: PDF con las etiquetas de un lote de equipos."""
    content, nombre = await service.get_labels_sheet(
        laboratorio=laboratorio or None,
        ubicacion=ubicacion or None,
        activo=activo,
    )
    filename = f"etiquetas-{_slug(nombre)}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/qr/{qr_token}")
async def resolver_qr(
    qr_token: str,
    _: AuthenticatedUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
) -> dict:
    return equipment_public(await service.resolve_qr_token(qr_token))


@router.get("/{equipment_id}")
async def detalle(
    equipment_id: int,
    _: AuthenticatedUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
) -> dict:
    return equipment_public(await service.find_one(equipment_id))


@router.patch("/{equipment_id}")
async def actualizar(
    equipment_id: int,
    body: UpdateEquipoRequest,
    _: AdminUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
) -> dict:
    equipo = await service.update(equipment_id, body.model_dump(exclude_unset=True))
    return equipment_public(equipo)


@router.get("/{equipment_id}/qr")
async def descargar_qr(
    equipment_id: int,
    _: AdminUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
    formato: Literal["png", "svg", "pdf"] = Query(default="png", alias="format"),
) -> Response:
    content, content_type, filename = await service.get_qr_document(equipment_id, formato)
    disposition = "attachment" if formato == "pdf" else "inline"
    filename = _slug(filename)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'{disposition}; filename="{filename}"',
        },
    )


@router.post("/{equipment_id}/regenerar-qr", status_code=status.HTTP_201_CREATED)
async def regenerar_qr(
    equipment_id: int,
    _: AdminUser,
    service: Annotated[EquiposService, Depends(get_equipos_service)],
) -> dict:
    return equipment_public(await service.regenerate_qr(equipment_id))


def _slug(value: str) -> str:
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", sin_acentos).strip("-")
    return slug[:60] or "equipos"
