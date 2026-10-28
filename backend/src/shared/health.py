"""GET /health: dice si la API está viva y si la base de datos responde."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from src.shared.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sistema"])


@router.get(
    "/health",
    summary="Estado del servicio",
    description="Prueba la conexión con la base de datos con un `SELECT 1`. Es público.",
    responses={
        200: {"content": {"application/json": {"example": {"status": "ok", "baseDeDatos": "ok"}}}},
        503: {
            "description": "La base de datos no responde",
            "content": {
                "application/json": {"example": {"status": "error", "baseDeDatos": "error"}}
            },
        },
    },
)
def health(session: Session = Depends(get_session)):
    try:
        session.exec(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("La base de datos no respondió al health check", exc_info=True)
        return JSONResponse(status_code=503, content={"status": "error", "baseDeDatos": "error"})
    return {"status": "ok", "baseDeDatos": "ok"}
