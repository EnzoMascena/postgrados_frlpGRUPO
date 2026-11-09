"""Crea la app FastAPI: middleware, manejadores de errores y los routers de cada módulo."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.autenticacion.presentation.router import router as autenticacion_router
from src.cohortes.presentation.router import router as cohortes_router
from src.gestion_documental.presentation.router import router as gestion_documental_router
from src.inscripcion.presentation.router import router as inscripcion_router
from src.inscripcion.presentation.seguimiento import router as seguimiento_router
from src.legajos.infrastructure.job_vencimiento import iniciar_programador
from src.legajos.presentation.router import router as legajos_router
from src.shared.config import settings
from src.shared.error_handlers import registrar_manejadores_de_errores
from src.shared.health import router as health_router
from src.shared.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # La tarea de vencimiento corre todos los días a las 3:00 dentro de este proceso (E6, ADR-007).
    # En los tests no se programa: se prueba llamando a la tarea directamente.
    programador = None if settings.environment == "testing" else iniciar_programador()
    yield
    if programador is not None:
        programador.shutdown()  # espera a que termine una corrida en curso


app = FastAPI(
    title="Sistema de Posgrado UTN FRLP · API",
    version="0.5.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

# El último middleware que se agrega es el más externo: CORS tiene que ver todas las respuestas.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_lista,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Disposition"],  # el front lee el nombre del archivo de las descargas
)
registrar_manejadores_de_errores(app)

app.include_router(health_router, prefix="/api/v1")
app.include_router(autenticacion_router, prefix="/api/v1")  # Luca (L1)
app.include_router(cohortes_router, prefix="/api/v1")  # Fran (F2)
app.include_router(inscripcion_router, prefix="/api/v1")  # Fran (F4)
app.include_router(seguimiento_router, prefix="/api/v1")  # Fran (F5)
app.include_router(gestion_documental_router, prefix="/api/v1")  # Fran (F5)
app.include_router(legajos_router, prefix="/api/v1")  # Luca (L3)

# Acá suma su router cada dueño, con prefix="/api/v1", una línea por módulo:
