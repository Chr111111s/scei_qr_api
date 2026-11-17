from datetime import UTC, datetime

import pytest

from app.application.services.usos_service import UsosService
from app.domain.entities import Equipment, Usage
from app.domain.enums import EstadoUso
from app.domain.exceptions import ConflictError, NotFoundError


def _equipo(*, id_: int = 10, codigo: str = "LAB-PC-001", activo: bool = True) -> Equipment:
    return Equipment(
        id=id_,
        codigo=codigo,
        nombre=codigo,
        descripcion=None,
        ubicacion="Laboratorio 1",
        qr_token="qr-token",
        activo=activo,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _uso(*, id_: int = 1, alumno_id: int = 1, equipo_id: int = 10) -> Usage:
    return Usage(
        id=id_,
        alumno_id=alumno_id,
        equipo_id=equipo_id,
        inicio=datetime(2026, 1, 1, tzinfo=UTC),
        fin=None,
        estado=EstadoUso.ACTIVO,
    )


class _FakeEquipos:
    def __init__(self, equipo: Equipment | None) -> None:
        self.equipo = equipo

    async def find_by_qr_token(self, qr_token: str) -> Equipment | None:
        return self.equipo


class _FakeUsos:
    def __init__(
        self,
        *,
        activo_alumno: Usage | None = None,
        activo_equipo: Usage | None = None,
    ) -> None:
        self.activo_alumno = activo_alumno
        self.activo_equipo = activo_equipo
        self.created: Usage | None = None

    async def find_active_by_alumno(self, alumno_id: int) -> Usage | None:
        return self.activo_alumno

    async def find_active_by_equipo(self, equipo_id: int) -> Usage | None:
        return self.activo_equipo

    async def create(self, *, alumno_id: int, equipo_id: int) -> Usage:
        self.created = _uso(alumno_id=alumno_id, equipo_id=equipo_id)
        return self.created


async def test_iniciar_crea_el_uso_cuando_no_hay_duplicados() -> None:
    equipo = _equipo()
    usos = _FakeUsos()
    service = UsosService(usos, _FakeEquipos(equipo))

    uso = await service.iniciar("qr-token", alumno_id=1)

    assert uso.alumno_id == 1
    assert uso.equipo_id == equipo.id
    assert usos.created is not None


async def test_iniciar_rechaza_equipo_ya_en_uso_por_otro_alumno() -> None:
    equipo = _equipo()
    usos = _FakeUsos(activo_equipo=_uso(alumno_id=2, equipo_id=equipo.id))
    service = UsosService(usos, _FakeEquipos(equipo))

    with pytest.raises(ConflictError) as exc:
        await service.iniciar("qr-token", alumno_id=1)

    assert "ya está en uso" in str(exc.value)
    assert usos.created is None


async def test_iniciar_rechaza_segundo_uso_activo_del_mismo_alumno() -> None:
    equipo = _equipo()
    usos = _FakeUsos(activo_alumno=_uso(alumno_id=1, equipo_id=99))
    service = UsosService(usos, _FakeEquipos(equipo))

    with pytest.raises(ConflictError) as exc:
        await service.iniciar("qr-token", alumno_id=1)

    assert "uso activo" in str(exc.value)
    assert usos.created is None


async def test_iniciar_rechaza_qr_inexistente() -> None:
    service = UsosService(_FakeUsos(), _FakeEquipos(None))

    with pytest.raises(NotFoundError):
        await service.iniciar("qr-desconocido", alumno_id=1)


async def test_iniciar_rechaza_equipo_inactivo() -> None:
    service = UsosService(_FakeUsos(), _FakeEquipos(_equipo(activo=False)))

    with pytest.raises(NotFoundError):
        await service.iniciar("qr-token", alumno_id=1)
