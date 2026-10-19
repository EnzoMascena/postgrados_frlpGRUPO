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

from fastapi import FastAPI

from app.core import health
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

app = FastAPI(
    title="Sistema de Posgrado — API",
    description=DESCRIPTION,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# Todo error sale con el formato de ARQUITECTURA §11.2 y en español.
registrar_handlers(app)

# Headers de seguridad en todas las respuestas (NFR-S05, módulo 05).
# Sin CORS: el front llama a /api y el proxy de Vite lo reenvía (mismo origen).
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router, prefix=API_PREFIX)
