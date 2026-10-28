import logging
from pathlib import Path
from uuid import uuid4

from anyio import to_thread

from app.core.config import settings
from app.domain.exceptions import BadRequestError, PayloadTooLargeError
from app.domain.ports.storage import StoragePort

logger = logging.getLogger(__name__)

_ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}
_ALLOWED_EXTENSIONS = set(_ALLOWED_TYPES.values())
_MAX_PHOTO_BYTES = 5 * 1024 * 1024


class LocalStorage(StoragePort):
    def __init__(self, upload_dir: Path | None = None) -> None:
        self.upload_dir = upload_dir or settings.upload_path
        if settings.storage_driver != "local":
            logger.warning(
                "STORAGE_DRIVER=%s aún no implementado; usando driver local.",
                settings.storage_driver,
            )

    async def save_incident_photo(
        self, *, original_name: str, content_type: str, data: bytes
    ) -> str:
        if not data:
            raise BadRequestError("Archivo vacío")
        if len(data) > _MAX_PHOTO_BYTES:
            raise PayloadTooLargeError()

        extension = self._sanitize_extension(original_name, content_type)
        directory = self.upload_dir / "incidencias"
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4()}{extension}"
        await to_thread.run_sync((directory / filename).write_bytes, data)
        return f"/uploads/incidencias/{filename}"

    @staticmethod
    def _sanitize_extension(original_name: str, content_type: str) -> str:
        ext_from_name = Path(original_name or "").suffix.lower()
        extension = _ALLOWED_TYPES.get(content_type) or ext_from_name
        if extension not in _ALLOWED_EXTENSIONS:
            raise BadRequestError("Formato de imagen no soportado (jpg, png, webp, heic)")
        return extension
