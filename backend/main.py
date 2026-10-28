"""Crea la app FastAPI: middleware, manejadores de errores y los routers de cada módulo."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.shared.config import settings
from src.shared.error_handlers import registrar_manejadores_de_errores
from src.shared.health import router as health_router
from src.shared.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # acá se engancha la tarea de vencimiento (E6)
    yield


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

# Acá suma su router cada dueño, con prefix="/api/v1", una línea por módulo:
# app.include_router(autenticacion_router, prefix="/api/v1")        # Luca (L1)
# app.include_router(cohortes_router, prefix="/api/v1")             # Fran (F2)
# app.include_router(inscripcion_router, prefix="/api/v1")          # Fran (F4)
# app.include_router(gestion_documental_router, prefix="/api/v1")   # Fran (F5)
# app.include_router(legajos_router, prefix="/api/v1")              # Luca (L3)
