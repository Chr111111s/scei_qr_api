# scei_qr_api (FastAPI)

Backend del sistema de **control de equipos por QR** (`scei_qr`), migrado de
NestJS a **FastAPI + SQLAlchemy async + PostgreSQL**. Mantiene el mismo contrato
HTTP que consumía la aplicación Flutter:

- Prefijo: `/api/v1`
- Swagger: `/api/docs` · OpenAPI: `/api/openapi.json`
- JWT HS256 de 8 h y roles `ADMIN`, `SOPORTE`, `ALUMNO`
- Errores con el formato `{ statusCode, message, error, timestamp, path }`
- Fotos servidas en `/uploads/incidencias/...`

## Arquitectura

```
app/
├── main.py                 # composición FastAPI, CORS, estáticos, errores
├── core/                   # settings, JWT, bcrypt
├── domain/                 # entidades, enums, reglas y puertos
├── application/services/   # casos de uso (SOLID)
├── infrastructure/         # SQLAlchemy, QR, storage, exportadores, FCM
└── api/                    # routers, validación, serialización y guards
```

La capa de aplicación depende de puertos (`Protocol`), no de SQLAlchemy. Los
adaptadores de infraestructura implementan esos puertos.

## Arranque con Docker (recomendado)

```bash
cp .env.example .env
docker compose up -d --build
```

El contenedor de la API:

1. aplica `alembic upgrade head`;
2. ejecuta el seed si `SEED_ON_START=true` (valor por defecto del compose);
3. levanta Uvicorn en `http://localhost:3000`.

Ver logs y salud:

```bash
docker compose logs -f api
curl http://localhost:3000/api/v1/health
```

### Ejecutar el seed manualmente

El seed es idempotente (no duplica usuarios ni equipos):

```bash
docker compose exec api python -m app.seed
# o, si la API no está corriendo:
docker compose run --rm api python -m app.seed
```

Credenciales demo:

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `Password123!` | ADMIN |
| `soporte` | `Password123!` | SOPORTE |
| `alumno1` | `Password123!` | ALUMNO |
| `alumno2` | `Password123!` | ALUMNO |

## Arranque local sin Docker para la API

Requiere PostgreSQL 16 (puede ser el contenedor `db` del compose):

```bash
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 3000
```

## Base de datos existente (Neon o Prisma)

El esquema inicial de Alembic replica exactamente tablas, columnas CamelCase,
enums, índices y FKs de Prisma. Si ya existe una base con ese esquema:

```bash
# No ejecutes upgrade sobre una base ya creada por Prisma.
alembic stamp 0001_initial
```

Con Docker, marca la revisión antes de arrancar la API:

```bash
docker compose run --rm --entrypoint alembic api stamp 0001_initial
docker compose up -d api
```

Después usa `DATABASE_URL`/`DIRECT_URL` con driver `asyncpg`. Los hashes bcrypt
existentes son compatibles y no hace falta re-sembrar.

> Neon: usa la URL pooled para `DATABASE_URL` y la directa (sin `-pooler`) para
> `DIRECT_URL`.

## Pruebas

Con la base levantada y migrada:

```bash
docker compose up -d db
alembic upgrade head
python -m app.seed
pytest
```

Las pruebas E2E crean datos con códigos únicos y los eliminan al terminar.

## Calidad

```bash
ruff check app tests
ruff format --check app tests
mypy app
pytest
```

## Endpoints principales

Ver Swagger en `/api/docs`. El inventario completo, roles y códigos de estado
se mantiene igual que en el backend NestJS original (incluidos los `201` de
creación de usuarios/equipos/regeneración de QR/token FCM y los `200` de login,
usos e incidencias).

## Notas de compatibilidad

- `GET /uploads/...` es público, igual que en el backend anterior.
- Las transiciones de incidencias se validan con `PENDIENTE → EN_ATENCION → RESUELTA`.
- `PATCH /incidencias/{id}/tomar` es atómico mediante `UPDATE ... WHERE estado='PENDIENTE'`.
- Los duplicados de unicidad se traducen a `409 Conflict` en lugar de un `500` genérico.
    