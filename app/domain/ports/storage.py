from typing import Protocol


class StoragePort(Protocol):
    async def save_incident_photo(
        self, *, original_name: str, content_type: str, data: bytes
    ) -> str: ...


class QrGeneratorPort(Protocol):
    def png(self, payload: str) -> bytes: ...

    def svg(self, payload: str) -> bytes: ...
