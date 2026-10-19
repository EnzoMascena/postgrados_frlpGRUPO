"""
Health check — GET /api/v1/health.

Responde si la API está viva Y si llega a la base de datos. El compose lo
usa como healthcheck del backend: si la base no responde devuelve 503 y el
contenedor queda "unhealthy".

Es público: junto con el login y las rutas públicas de inscripción, es una
de las pocas excepciones del deny-by-default (no lleva require_role).

Como el health_controller del módulo 03, recibe la Session por Depends:
así los tests la pueden reemplazar por una base de test o por una rota.
"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, text

from app.core.database import get_session
from app.core.schemas import CamelModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


class HealthRead(CamelModel):
    """Estado de la API y de su conexión a la base."""

    estado: str
    base_de_datos: str


@router.get(
    "/health",
    response_model=HealthRead,
    summary="Estado de la API y de la base",
    responses={503: {"model": HealthRead, "description": "La base de datos no responde"}},
)
def health(session: Session = Depends(get_session)):
    """Hace un `SELECT 1` contra PostgreSQL. 200 si responde; 503 si no."""
    try:
        session.exec(text("SELECT 1"))
    except SQLAlchemyError:
        # El detalle técnico va al log, nunca a la respuesta.
        logger.exception("Health check: la base de datos no responde")
        caida = HealthRead(estado="error", base_de_datos="sin conexión")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=caida.model_dump(),
        )
    return HealthRead(estado="ok", base_de_datos="ok")
