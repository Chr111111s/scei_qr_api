from time import time

from sqlalchemy import delete

from app.infrastructure.db.models import Equipo, Usuario
from app.infrastructure.db.session import SessionLocal


async def test_admin_user_and_equipment_crud(client) -> None:
    stamp = int(time() * 1000)
    username = f"e2e_user_{stamp}"
    correo = f"e2e_{stamp}@example.com"
    matricula = f"M{str(stamp)[-8:]}"
    codigo = f"CRUD-{stamp}"
    user_id: int | None = None
    equipment_id: int | None = None

    try:
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Password123!"},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

        created_user = await client.post(
            "/api/v1/usuarios",
            headers=headers,
            json={
                "username": username,
                "password": "Password123!",
                "fullName": "Usuario CRUD",
                "correo": correo.upper(),
                "matricula": matricula.lower(),
                "rol": "ALUMNO",
                "activo": True,
            },
        )
        assert created_user.status_code == 201, created_user.text
        user = created_user.json()
        user_id = user["id"]
        assert user["fullName"] == "Usuario CRUD"
        assert user["correo"] == correo
        assert user["matricula"] == matricula
        assert user["rol"] == "ALUMNO"
        assert user["activo"] is True
        assert "password" not in user
        assert "passwordHash" not in user

        duplicate_user = await client.post(
            "/api/v1/usuarios",
            headers=headers,
            json={
                "username": username,
                "password": "Password123!",
                "fullName": "Duplicado",
                "rol": "ALUMNO",
            },
        )
        assert duplicate_user.status_code == 409

        duplicate_correo = await client.post(
            "/api/v1/usuarios",
            headers=headers,
            json={
                "username": f"{username}_correo",
                "password": "Password123!",
                "fullName": "Correo duplicado",
                "correo": correo,
                "rol": "ALUMNO",
            },
        )
        assert duplicate_correo.status_code == 409

        duplicate_matricula = await client.post(
            "/api/v1/usuarios",
            headers=headers,
            json={
                "username": f"{username}_matricula",
                "password": "Password123!",
                "fullName": "Matrícula duplicada",
                "matricula": matricula,
                "rol": "ALUMNO",
            },
        )
        assert duplicate_matricula.status_code == 409

        invalid_user = await client.post(
            "/api/v1/usuarios",
            headers=headers,
            json={
                "username": "",
                "password": "123",
                "fullName": "",
                "rol": "INVALIDO",
            },
        )
        assert invalid_user.status_code == 400

        filtered_users = await client.get(
            f"/api/v1/usuarios?rol=ALUMNO&activo=true&q={username}", headers=headers
        )
        assert filtered_users.status_code == 200
        assert [item["id"] for item in filtered_users.json()] == [user_id]

        detail = await client.get(f"/api/v1/usuarios/{user_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["username"] == username

        updated_user = await client.patch(
            f"/api/v1/usuarios/{user_id}",
            headers=headers,
            json={"fullName": "Usuario Editado", "activo": False},
        )
        assert updated_user.status_code == 200, updated_user.text
        assert updated_user.json()["fullName"] == "Usuario Editado"
        assert updated_user.json()["activo"] is False

        inactive_login = await client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "Password123!"},
        )
        assert inactive_login.status_code == 401

        reactivated = await client.patch(
            f"/api/v1/usuarios/{user_id}",
            headers=headers,
            json={"activo": True},
        )
        assert reactivated.status_code == 200
        assert reactivated.json()["activo"] is True

        user_login = await client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "Password123!"},
        )
        assert user_login.status_code == 200
        assert user_login.json()["user"]["id"] == user_id

        matricula_login = await client.post(
            "/api/v1/auth/login",
            json={"username": matricula.lower(), "password": "Password123!"},
        )
        assert matricula_login.status_code == 200
        assert matricula_login.json()["user"]["id"] == user_id

        created_equipment = await client.post(
            "/api/v1/equipos",
            headers=headers,
            json={
                "codigo": codigo,
                "nombre": "Equipo CRUD",
                "descripcion": "Descripción inicial",
                "ubicacion": "Laboratorio CRUD",
            },
        )
        assert created_equipment.status_code == 201, created_equipment.text
        equipment = created_equipment.json()
        equipment_id = equipment["id"]
        original_qr = equipment["qrToken"]

        duplicate_equipment = await client.post(
            "/api/v1/equipos",
            headers=headers,
            json={"codigo": codigo, "nombre": "Duplicado", "ubicacion": "Otra"},
        )
        assert duplicate_equipment.status_code == 409

        filtered_equipment = await client.get(
            f"/api/v1/equipos?q={codigo}&ubicacion=CRUD&activo=true", headers=headers
        )
        assert filtered_equipment.status_code == 200
        assert [item["id"] for item in filtered_equipment.json()] == [equipment_id]

        updated_equipment = await client.patch(
            f"/api/v1/equipos/{equipment_id}",
            headers=headers,
            json={"descripcion": None, "nombre": "Equipo Editado"},
        )
        assert updated_equipment.status_code == 200
        assert updated_equipment.json()["descripcion"] is None
        assert updated_equipment.json()["nombre"] == "Equipo Editado"

        regenerated = await client.post(
            f"/api/v1/equipos/{equipment_id}/regenerar-qr", headers=headers
        )
        assert regenerated.status_code == 201
        assert regenerated.json()["qrToken"] != original_qr

        resolved_old_qr = await client.get(f"/api/v1/equipos/qr/{original_qr}", headers=headers)
        assert resolved_old_qr.status_code == 404

        resolved_new_qr = await client.get(
            f"/api/v1/equipos/qr/{regenerated.json()['qrToken']}", headers=headers
        )
        assert resolved_new_qr.status_code == 200
        assert resolved_new_qr.json()["id"] == equipment_id

        deactivated = await client.patch(
            f"/api/v1/equipos/{equipment_id}",
            headers=headers,
            json={"activo": False},
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["activo"] is False

        inactive_qr = await client.get(
            f"/api/v1/equipos/qr/{regenerated.json()['qrToken']}", headers=headers
        )
        assert inactive_qr.status_code == 404
    finally:
        async with SessionLocal() as session:
            if equipment_id is not None:
                await session.execute(delete(Equipo).where(Equipo.id == equipment_id))
            if user_id is not None:
                await session.execute(delete(Usuario).where(Usuario.id == user_id))
            await session.commit()
