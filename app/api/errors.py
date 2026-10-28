import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import AppError

logger = logging.getLogger(__name__)

_ERROR_NAMES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _path(request: Request) -> str:
    query = request.url.query
    return f"{request.url.path}?{query}" if query else request.url.path


def _payload(request: Request, status_code: int, message: Any, error: str) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "path": _path(request),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(request, exc.status_code, exc.message, exc.error),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        messages: list[str] = []
        for error in exc.errors():
            location = ".".join(
                str(part) for part in error.get("loc", ()) if part not in ("body", "query", "path")
            )
            message = str(error.get("msg", "Invalid value"))
            messages.append(f"{location}: {message}" if location else message)
        return JSONResponse(
            status_code=400,
            content=_payload(request, 400, messages, "Bad Request"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        status_code = exc.status_code
        error = _ERROR_NAMES.get(status_code, HTTPStatus(status_code).phrase)
        message: Any = exc.detail
        if status_code == 404 and exc.detail == "Not Found":
            message = f"Cannot {request.method} {request.url.path}"
        return JSONResponse(
            status_code=status_code,
            content=_payload(request, status_code, message, error),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database integrity error: %s", exc)
        return JSONResponse(
            status_code=409,
            content=_payload(
                request,
                409,
                "El recurso ya existe o viola una restricción de unicidad",
                "Conflict",
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_payload(request, 500, "Error interno del servidor", "Internal Server Error"),
        )
