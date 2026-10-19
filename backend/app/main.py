"""
Entrypoint del backend — Sistema de Posgrado (UTN FRLP).
========================================================

Este archivo es SOLO el punto de entrada, como el main.py de la cátedra:
crea la app, registra los routers de cada módulo y maneja el arranque.
No tiene lógica de negocio ni SQL.

    Request → [middleware de headers] → router del módulo
            → controller → service → repository → PostgreSQL

Swagger (NFR-M02): http://localhost:8000/api/docs

Ejecutar en desarrollo (desde backend/):
    uv run alembic upgrade head      # crea o actualiza las tablas
    uv run uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth import controller as auth_controller
from app.core import health, scheduler
from app.core.config import API_PREFIX
from app.core.errores import registrar_handlers
from app.core.middleware import SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

DESCRIPTION = """
API del **Sistema de Posgrado** de la UTN FRLP: inscripción, legajos,
seguimiento académico, planilla docente y estadísticas.

- Todas las rutas cuelgan de `/api/v1`, con JSON en camelCase.
- Arquitectura en 3 capas por módulo: controller → service → repository.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Al arrancar programa los jobs diarios (ARQUITECTURA §12); al apagar los frena.

    El esquema NO se crea acá (como hacía la cátedra con create_all): lo
    maneja Alembic, y start.sh corre la migración antes de levantar la API.
    """
    scheduler.iniciar()
    yield
    scheduler.detener()


app = FastAPI(
    title="Sistema de Posgrado — API",
    description=DESCRIPTION,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Todo error sale con el formato de ARQUITECTURA §11.2 y en español.
registrar_handlers(app)

# Headers de seguridad en todas las respuestas (NFR-S05, módulo 05).
# Sin CORS: el front llama a /api y el proxy de Vite lo reenvía (mismo origen).
app.add_middleware(SecurityHeadersMiddleware)

# Un router por módulo, todos bajo /api/v1.
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth_controller.router, prefix=API_PREFIX)
