from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, get_reportes_service, require_roles
from app.application.services.reportes_service import ReportesService
from app.domain.enums import Rol

router = APIRouter(prefix="/reportes", tags=["reportes"])
AdminUser = Annotated[CurrentUser, Depends(require_roles(Rol.ADMIN))]


@router.get("/estadisticas")
async def estadisticas(
    _: AdminUser,
    service: Annotated[ReportesService, Depends(get_reportes_service)],
) -> dict:
    return await service.get_estadisticas()


@router.get("/exportar")
async def exportar(
    _: AdminUser,
    service: Annotated[ReportesService, Depends(get_reportes_service)],
    formato_query: str = Query(default="xlsx", alias="format"),
) -> Response:
    formato: Literal["xlsx", "pdf"] = "pdf" if formato_query == "pdf" else "xlsx"
    content, filename, content_type = await service.exportar(formato)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
