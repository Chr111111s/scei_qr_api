from datetime import UTC, datetime

from app.api.serializers import iso_timestamp
from app.core.security import (
    create_access_token,
    decode_access_token,
    expiration_to_seconds,
    hash_password,
    verify_password,
)
from app.domain.enums import EstadoIncidencia
from app.domain.rules import TRANSICIONES_VALIDAS, estados_permitidos


def test_expiration_to_seconds() -> None:
    assert expiration_to_seconds("8h") == 28800
    assert expiration_to_seconds("30m") == 1800
    assert expiration_to_seconds("7d") == 604800
    assert expiration_to_seconds("10s") == 10
    assert expiration_to_seconds("invalid") == 28800


def test_password_hash_roundtrip() -> None:
    password_hash = hash_password("Password123!")
    assert password_hash != "Password123!"
    assert verify_password("Password123!", password_hash)
    assert not verify_password("wrong", password_hash)


def test_jwt_payload_contract() -> None:
    token, expires_in = create_access_token(user_id=7, username="alumno1", role="ALUMNO")
    payload = decode_access_token(token)
    assert expires_in == 28800
    assert payload["sub"] == 7
    assert payload["username"] == "alumno1"
    assert payload["role"] == "ALUMNO"
    assert "exp" in payload


def test_incident_state_machine() -> None:
    assert TRANSICIONES_VALIDAS[EstadoIncidencia.PENDIENTE] == [EstadoIncidencia.EN_ATENCION]
    assert estados_permitidos(EstadoIncidencia.EN_ATENCION) == [EstadoIncidencia.RESUELTA]
    assert estados_permitidos(EstadoIncidencia.RESUELTA) == []


def test_iso_timestamp_contract() -> None:
    assert iso_timestamp(datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=UTC)) == (
        "2026-01-02T03:04:05.123Z"
    )
    assert iso_timestamp(None) is None
