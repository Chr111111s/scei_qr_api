import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.core.security import hash_password
from app.domain.enums import Rol
from app.infrastructure.db.models import Equipo, Usuario
from app.infrastructure.db.session import SessionLocal, engine

DEMO_PASSWORD = "Password123!"

USERS = [
    ("admin", "Ana Torres (Administradora)", Rol.ADMIN),
    ("soporte", "Carlos Mena (Soporte técnico)", Rol.SOPORTE),
    ("alumno1", "Lucía Fernández (Alumna)", Rol.ALUMNO),
    ("alumno2", "Mateo Ruiz (Alumno)", Rol.ALUMNO),
]

EQUIPMENT = [
    (
        "LAB-PC-001",
        "PC Dell OptiPlex 7090",
        "Equipo de cómputo para talleres de programación",
        "Laboratorio de Cómputo 1, Fila A",
    ),
    (
        "LAB-PC-002",
        "PC HP ProDesk 400",
        "Equipo de diseño gráfico",
        "Laboratorio de Cómputo 1, Fila B",
    ),
    (
        "LAB-MON-001",
        'Monitor Samsung 24"',
        "Monitor externo para estaciones",
        "Laboratorio de Electrónica, Mesa 3",
    ),
    (
        "TALL-PROY-001",
        "Proyector Epson X49",
        "Proyector para salones",
        "Salón 201",
    ),
]


async def seed() -> None:
    print("Sembrando datos de prueba...")
    async with SessionLocal() as session:
        password_hash = hash_password(DEMO_PASSWORD)

        for username, full_name, rol in USERS:
            exists = await session.scalar(select(Usuario.id).where(Usuario.username == username))
            if exists is None:
                session.add(
                    Usuario(
                        username=username,
                        password_hash=password_hash,
                        full_name=full_name,
                        rol=rol,
                        activo=True,
                    )
                )
        print(f"   OK {len(USERS)} usuarios verificados/creados")

        for codigo, nombre, descripcion, ubicacion in EQUIPMENT:
            exists = await session.scalar(select(Equipo.id).where(Equipo.codigo == codigo))
            if exists is None:
                session.add(
                    Equipo(
                        codigo=codigo,
                        nombre=nombre,
                        descripcion=descripcion,
                        ubicacion=ubicacion,
                        qr_token=str(uuid4()),
                        activo=True,
                    )
                )
        print(f"   OK {len(EQUIPMENT)} equipos verificados/creados")

        await session.commit()

    await engine.dispose()
    print("Seed completado.")
    print("Login: admin / soporte / alumno1 / alumno2 -> Password123!")


if __name__ == "__main__":
    asyncio.run(seed())
