from time import time

from sqlalchemy import delete

from app.core.config import settings
from app.infrastructure.db.models import Equipo, Incidencia, Uso
from app.infrastructure.db.session import SessionLocal

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082"
)


async def _login(client, username: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123!"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tokenType"] == "Bearer"
    assert payload["expiresIn"] == 28800
    assert payload["user"]["rol"]
    return payload["accessToken"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_full_flow(client) -> None:
    stamp = int(time() * 1000)
    created_equipment: list[int] = []
    created_usage: int | None = None
    created_incident: int | None = None
    uploaded_photo: str | None = None

    try:
        health = await client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        admin_token = await _login(client, "admin")
        soporte_token = await _login(client, "soporte")
        alumno_token = await _login(client, "alumno1")

        invalid = await client.post(
            "/api/v1/auth/login",
            json={"username": "alumno1", "password": "incorrecta"},
        )
        assert invalid.status_code == 401
        assert invalid.json()["message"] == "Usuario o contraseña incorrectos"

        short_password = await client.post(
            "/api/v1/auth/login",
            json={"username": "alumno1", "password": "123"},
        )
        assert short_password.status_code == 400
        assert short_password.json()["error"] == "Bad Request"

        created = await client.post(
            "/api/v1/equipos",
            headers=_auth(admin_token),
            json={
                "codigo": f"E2E-{stamp}",
                "nombre": "Equipo E2E",
                "descripcion": "Creado por prueba e2e",
                "ubicacion": "Laboratorio E2E",
            },
        )
        assert created.status_code == 201, created.text
        equipment = created.json()
        equipment_id = equipment["id"]
        qr_token = equipment["qrToken"]
        created_equipment.append(equipment_id)

        forbidden = await client.post(
            "/api/v1/equipos",
            headers=_auth(alumno_token),
            json={"codigo": f"NO-{stamp}", "nombre": "x", "ubicacion": "y"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"] == "Forbidden"

        qr_png = await client.get(f"/api/v1/equipos/{equipment_id}/qr", headers=_auth(admin_token))
        assert qr_png.status_code == 200
        assert qr_png.headers["content-type"] == "image/png"
        assert len(qr_png.content) > 100

        qr_svg = await client.get(
            f"/api/v1/equipos/{equipment_id}/qr?format=svg",
            headers=_auth(admin_token),
        )
        assert qr_svg.status_code == 200
        assert qr_svg.headers["content-type"] == "image/svg+xml"
        assert qr_svg.content.startswith(b"<?xml")

        resolved = await client.get(f"/api/v1/equipos/qr/{qr_token}", headers=_auth(alumno_token))
        assert resolved.status_code == 200
        assert resolved.json()["id"] == equipment_id
        assert resolved.json()["activo"] is True

        started = await client.post(
            "/api/v1/usos",
            headers=_auth(alumno_token),
            json={"qrToken": qr_token},
        )
        assert started.status_code == 200, started.text
        usage = started.json()
        created_usage = usage["id"]
        assert usage["estado"] == "ACTIVO"
        assert usage["equipo"]["codigo"] == f"E2E-{stamp}"

        other_equipment = await client.post(
            "/api/v1/equipos",
            headers=_auth(admin_token),
            json={"codigo": f"E2E2-{stamp}", "nombre": "Otro", "ubicacion": "Lab"},
        )
        assert other_equipment.status_code == 201
        created_equipment.append(other_equipment.json()["id"])

        conflict = await client.post(
            "/api/v1/usos",
            headers=_auth(alumno_token),
            json={"qrToken": other_equipment.json()["qrToken"]},
        )
        assert conflict.status_code == 409
        assert conflict.json()["error"] == "Conflict"

        finished = await client.patch(
            f"/api/v1/usos/{created_usage}/finalizar",
            headers=_auth(alumno_token),
        )
        assert finished.status_code == 200
        assert finished.json()["estado"] == "FINALIZADO"
        assert finished.json()["fin"] is not None

        incident = await client.post(
            "/api/v1/incidencias",
            headers=_auth(alumno_token),
            data={
                "equipoId": str(equipment_id),
                "titulo": "Falla E2E",
                "descripcion": "Prueba automatizada de flujo completo",
            },
            files={"foto": ("fallo.png", PNG_1X1, "image/png")},
        )
        assert incident.status_code == 200, incident.text
        incident_payload = incident.json()
        created_incident = incident_payload["id"]
        assert incident_payload["estado"] == "PENDIENTE"
        assert incident_payload["fotoUrl"].startswith("/uploads/incidencias/")
        uploaded_photo = incident_payload["fotoUrl"]

        photo = await client.get(uploaded_photo)
        assert photo.status_code == 200
        assert photo.content == PNG_1X1

        mine = await client.get("/api/v1/incidencias/mis-reportes", headers=_auth(alumno_token))
        assert mine.status_code == 200
        assert any(item["id"] == created_incident for item in mine.json())

        pending = await client.get(
            "/api/v1/incidencias?estado=PENDIENTE", headers=_auth(soporte_token)
        )
        assert pending.status_code == 200
        assert any(item["id"] == created_incident for item in pending.json())

        invalid_filter = await client.get(
            "/api/v1/incidencias?estado=INVALIDO", headers=_auth(soporte_token)
        )
        assert invalid_filter.status_code == 400

        cannot_take = await client.patch(
            f"/api/v1/incidencias/{created_incident}/tomar",
            headers=_auth(alumno_token),
        )
        assert cannot_take.status_code == 403

        taken = await client.patch(
            f"/api/v1/incidencias/{created_incident}/tomar",
            headers=_auth(soporte_token),
        )
        assert taken.status_code == 200
        assert taken.json()["estado"] == "EN_ATENCION"
        assert taken.json()["atendidaPor"]["username"] == "soporte"

        taken_again = await client.patch(
            f"/api/v1/incidencias/{created_incident}/tomar",
            headers=_auth(soporte_token),
        )
        assert taken_again.status_code == 409

        invalid_transition = await client.patch(
            f"/api/v1/incidencias/{created_incident}/estado",
            headers=_auth(soporte_token),
            json={"estado": "PENDIENTE"},
        )
        assert invalid_transition.status_code == 409
        assert "Transición no permitida" in invalid_transition.json()["message"]

        solution = await client.patch(
            f"/api/v1/incidencias/{created_incident}/solucion",
            headers=_auth(soporte_token),
            json={"solucion": "Se reemplazó el componente; probado OK"},
        )
        assert solution.status_code == 200
        assert solution.json()["estado"] == "RESUELTA"
        assert solution.json()["solucion"] == "Se reemplazó el componente; probado OK"

        history = await client.get("/api/v1/incidencias/historial", headers=_auth(soporte_token))
        assert history.status_code == 200
        assert any(item["id"] == created_incident for item in history.json())

        stats = await client.get("/api/v1/reportes/estadisticas", headers=_auth(admin_token))
        assert stats.status_code == 200
        stats_payload = stats.json()
        assert stats_payload["equipos"]["total"] > 0
        assert stats_payload["usuarios"]["alumnos"] > 0
        assert "pendientes" in stats_payload["incidencias"]
        assert isinstance(stats_payload["usosPorEquipo"], list)

        xlsx = await client.get("/api/v1/reportes/exportar?format=xlsx", headers=_auth(admin_token))
        assert xlsx.status_code == 200
        assert xlsx.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert xlsx.content[:2] == b"PK"

        pdf = await client.get("/api/v1/reportes/exportar?format=pdf", headers=_auth(admin_token))
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.content.startswith(b"%PDF-")

        usage_history = await client.get(
            f"/api/v1/usos/historial?equipoId={equipment_id}",
            headers=_auth(admin_token),
        )
        assert usage_history.status_code == 200
        assert any(item["id"] == created_usage for item in usage_history.json())

        my_usages = await client.get("/api/v1/usos/mis-registros", headers=_auth(alumno_token))
        assert my_usages.status_code == 200
        assert any(item["id"] == created_usage for item in my_usages.json())

        token_response = await client.post(
            "/api/v1/notificaciones/token",
            headers=_auth(alumno_token),
            json={"token": f"fcm-test-{stamp}"},
        )
        assert token_response.status_code == 201
        assert token_response.json() == {"registered": True}

        logout = await client.post("/api/v1/auth/logout", headers=_auth(alumno_token))
        assert logout.status_code == 200
        assert logout.json()["message"] == "Sesión cerrada"

        assert (await client.get("/api/v1/equipos")).status_code == 401
        assert (await client.get("/api/v1/reportes/estadisticas")).status_code == 401
    finally:
        async with SessionLocal() as session:
            if created_incident is not None:
                await session.execute(delete(Incidencia).where(Incidencia.id == created_incident))
            if created_usage is not None:
                await session.execute(delete(Uso).where(Uso.id == created_usage))
            for equipment_id in created_equipment:
                await session.execute(delete(Equipo).where(Equipo.id == equipment_id))
            await session.commit()
        if uploaded_photo is not None:
            photo_path = settings.upload_path / uploaded_photo.removeprefix("/uploads/")
            photo_path.unlink(missing_ok=True)
