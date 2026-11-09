"""Endpoints del aspirante con su link de seguimiento: `GET /seguimiento/{token}` (F5).

Acá suma F6 el `PUT /seguimiento/{token}` y el `POST /seguimiento/{token}/enviar`.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.inscripcion.presentation.dependencies import MENSAJE_LINK_INVALIDO, legajo_id_desde_token
from src.legajos.application.obtener_detalle import obtener_detalle
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.schemas import LegajoDetalleAspiranteResponse
from src.shared.database import get_session

router = APIRouter(prefix="/seguimiento", tags=["Seguimiento del aspirante"])

LINK_INVALIDO: dict[int | str, dict[str, Any]] = {
    404: {
        "description": "El link no existe o venció",
        "content": {
            "application/json": {
                "example": {
                    "statusCode": 404,
                    "error": "NOT_FOUND",
                    "message": MENSAJE_LINK_INVALIDO,
                    "field": None,
                    "timestamp": "2026-11-04T14:20:00Z",
                }
            }
        },
    },
}


@router.get(
    "/{token}",
    response_model=LegajoDetalleAspiranteResponse,
    summary="Ver mi legajo",
    description=(
        "Aspirante, con el token de su link (ADR-005). Sus datos, el checklist de documentos "
        "con los que ya subió, los faltantes, la última observación y `puedeEditar` (verdadero "
        "en BORRADOR y OBSERVADO). Es el mismo detalle que ve el coordinador, sin el historial "
        "ni las acciones."
    ),
    responses=LINK_INVALIDO,
)
def ver_mi_legajo(
    legajo_id: UUID = Depends(legajo_id_desde_token), session: Session = Depends(get_session)
) -> LegajoDetalleAspiranteResponse:
    detalle = obtener_detalle(legajo_id, PgLegajoRepository(session), "aspirante")
    return LegajoDetalleAspiranteResponse.model_validate(detalle)
