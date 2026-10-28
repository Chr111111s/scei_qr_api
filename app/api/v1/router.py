from fastapi import APIRouter

from app.api.v1.routers import (
    auth,
    equipos,
    health,
    incidencias,
    notificaciones,
    reportes,
    usos,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(equipos.router)
api_router.include_router(usos.router)
api_router.include_router(incidencias.router)
api_router.include_router(reportes.router)
api_router.include_router(notificaciones.router)
