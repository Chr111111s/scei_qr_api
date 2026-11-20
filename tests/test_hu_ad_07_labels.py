from time import time

from sqlalchemy import delete

from app.infrastructure.db.models import Equipo
from app.infrastructure.db.session import SessionLocal


async def _token(client, username: str) -> str:
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Password123!"},
    )
    assert login.status_code == 200, login.text
    return login.json()["accessToken"]


async def test_hu_ad_07_descargar_e_imprimir_qr(client) -> None:
    """HU-AD-07: etiqueta individual PDF y lote por laboratorio."""
    stamp = int(time() * 1000)
    laboratorio = f"Laboratorio QA {stamp}"
    created_ids: list[int] = []

    try:
        admin = {"Authorization": f"Bearer {await _token(client, 'admin')}"}
        alumno = {"Authorization": f"Bearer {await _token(client, 'alumno1')}"}

        for suffix in ("A", "B"):
            created = await client.post(
                "/api/v1/equipos",
                headers=admin,
                json={
                    "codigo": f"QA-{stamp}-{suffix}",
                    "nombre": f"Equipo QA {suffix}",
                    "descripcion": "Equipo para etiquetas",
                    "laboratorio": laboratorio,
                    "ubicacion": f"Mesa {suffix}",
                },
            )
            assert created.status_code == 201, created.text
            payload = created.json()
            created_ids.append(payload["id"])
            assert payload["laboratorio"] == laboratorio

        equipment_id = created_ids[0]

        # CA 1: descarga del QR como PDF con plantilla de etiqueta.
        single = await client.get(f"/api/v1/equipos/{equipment_id}/qr?format=pdf", headers=admin)
        assert single.status_code == 200, single.text
        assert single.headers["content-type"] == "application/pdf"
        assert single.headers["content-disposition"].startswith("attachment;")
        assert "etiqueta-QA-" in single.headers["content-disposition"]
        assert single.content.startswith(b"%PDF")
        assert len(single.content) > 1000

        # CA 1: sigue disponible la imagen PNG.
        png = await client.get(f"/api/v1/equipos/{equipment_id}/qr", headers=admin)
        assert png.status_code == 200
        assert png.headers["content-type"] == "image/png"

        # Formato no soportado: error de validación en lugar de devolver otro
        # formato de manera silenciosa.
        invalid = await client.get(f"/api/v1/equipos/{equipment_id}/qr?format=jpg", headers=admin)
        assert invalid.status_code == 400

        # CA 2: etiquetas por lote para todos los equipos del laboratorio.
        sheet = await client.get(
            "/api/v1/equipos/etiquetas",
            headers=admin,
            params={"laboratorio": laboratorio},
        )
        assert sheet.status_code == 200, sheet.text
        assert sheet.headers["content-type"] == "application/pdf"
        assert sheet.headers["content-disposition"].startswith("attachment;")
        assert (
            f"etiquetas-{laboratorio.replace(' ', '-')}.pdf" in sheet.headers["content-disposition"]
        )
        assert sheet.content.startswith(b"%PDF")
        assert len(sheet.content) > len(single.content)

        # El listado también filtra por laboratorio para preparar el lote.
        listado = await client.get(
            "/api/v1/equipos",
            headers=admin,
            params={"laboratorio": laboratorio},
        )
        assert listado.status_code == 200, listado.text
        assert {item["id"] for item in listado.json()} == set(created_ids)

        # Lote inexistente: 404 explícito.
        empty = await client.get(
            "/api/v1/equipos/etiquetas",
            headers=admin,
            params={"laboratorio": f"Sin equipos {stamp}"},
        )
        assert empty.status_code == 404

        # Solo ADMIN puede descargar etiquetas.
        forbidden = await client.get(
            "/api/v1/equipos/etiquetas",
            headers=alumno,
            params={"laboratorio": laboratorio},
        )
        assert forbidden.status_code == 403
    finally:
        if created_ids:
            async with SessionLocal() as session:
                await session.execute(delete(Equipo).where(Equipo.id.in_(created_ids)))
                await session.commit()


async def test_hu_ad_07_nombre_de_archivo_seguro(client) -> None:
    """El nombre de la etiqueta no permite inyectar cabeceras."""
    stamp = int(time() * 1000)
    codigo = f'QA {stamp}/A "x"'
    equipment_id: int | None = None

    try:
        admin = {"Authorization": f"Bearer {await _token(client, 'admin')}"}
        created = await client.post(
            "/api/v1/equipos",
            headers=admin,
            json={
                "codigo": codigo,
                "nombre": "Equipo con código especial",
                "ubicacion": "Mesa 1",
            },
        )
        assert created.status_code == 201, created.text
        equipment_id = created.json()["id"]

        response = await client.get(f"/api/v1/equipos/{equipment_id}/qr?format=pdf", headers=admin)
        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert disposition.startswith("attachment;")
        assert "\n" not in disposition and "\r" not in disposition
        # Sin espacios, comillas internas ni barras en el nombre del archivo.
        filename = disposition.split("filename=", 1)[1]
        assert filename.startswith('"') and filename.endswith('"')
        assert "/" not in filename
        assert f'"{stamp}' not in filename
        assert filename.endswith('.pdf"')
    finally:
        if equipment_id is not None:
            async with SessionLocal() as session:
                await session.execute(delete(Equipo).where(Equipo.id == equipment_id))
                await session.commit()
