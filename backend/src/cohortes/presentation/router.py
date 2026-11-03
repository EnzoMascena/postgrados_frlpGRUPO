"""Endpoints de cohortes y carreras: `GET /cohortes` y `GET /carreras` (públicos) y
`PATCH /cohortes/{id}/inscripcion` (coordinador)."""

from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO
from src.autenticacion.presentation.dependencies import MENSAJE_SIN_PERMISO, require_role
from src.cohortes.application.cambiar_periodo import (
    MENSAJE_COHORTE_INEXISTENTE,
    cambiar_periodo_de_inscripcion,
)
from src.cohortes.infrastructure.pg_repository import PgCohorteRepository
from src.cohortes.presentation.schemas import (
    CambiarPeriodoRequest,
    CarreraResponse,
    CohorteResponse,
)
from src.shared.config import settings
from src.shared.database import get_session
from src.shared.roles import Rol

router = APIRouter(tags=["Cohortes y carreras"])


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger, con el formato de ARQUITECTURA §11.2."""
    ejemplo = {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-01T14:20:00Z",
    }
    return {"content": {"application/json": {"example": ejemplo}}}


@router.get(
    "/cohortes",
    response_model=list[CohorteResponse],
    summary="Listar cohortes",
    description=(
        "Público: lo usa el formulario de inscripción (NFR-S01). Devuelve todas las cohortes, de "
        "la más nueva a la más vieja, con su período de inscripción (`inscripcionAbierta` y "
        "`proximaApertura`)."
    ),
)
def listar_cohortes(session: Session = Depends(get_session)) -> list[CohorteResponse]:
    cohortes = PgCohorteRepository(session).listar_cohortes()
    return [CohorteResponse.model_validate(cohorte) for cohorte in cohortes]


@router.patch(
    "/cohortes/{cohorte_id}/inscripcion",
    response_model=CohorteResponse,
    dependencies=[Depends(require_role(Rol.COORDINADOR))],
    summary="Abrir o cerrar la inscripción",
    description=(
        "Coordinador (BR-009). Abre o cierra el período de inscripción de una cohorte; cada "
        "cohorte tiene el suyo. Al cerrar se puede informar `proximaApertura`, que no puede ser "
        "una fecha pasada y que el formulario muestra en el aviso. Al abrir se borra."
    ),
    responses={
        401: {
            "description": "Sin token, con un token inválido o vencido, o con un usuario inactivo",
            **_error(401, "UNAUTHORIZED", MENSAJE_TOKEN_INVALIDO),
        },
        403: {
            "description": "El usuario no es coordinador",
            **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
        },
        404: {
            "description": "No hay una cohorte con ese id",
            **_error(404, "NOT_FOUND", MENSAJE_COHORTE_INEXISTENTE),
        },
        422: {
            "description": "La próxima apertura es una fecha pasada, o falta `abierta`",
            **_error(
                422,
                "VALIDATION_ERROR",
                "La próxima apertura no puede ser una fecha pasada",
                "proximaApertura",
            ),
        },
    },
)
def cambiar_periodo(
    cohorte_id: UUID, datos: CambiarPeriodoRequest, session: Session = Depends(get_session)
) -> CohorteResponse:
    # "Hoy" en Argentina: en UTC, después de las 21 hs ya sería mañana.
    hoy = datetime.now(ZoneInfo(settings.zona_horaria)).date()
    cohorte = cambiar_periodo_de_inscripcion(
        cohorte_id, datos.abierta, datos.proxima_apertura, PgCohorteRepository(session), hoy
    )
    return CohorteResponse.model_validate(cohorte)


@router.get(
    "/carreras",
    response_model=list[CarreraResponse],
    summary="Listar carreras activas",
    description=(
        "Público: lo usa el formulario de inscripción (NFR-S01). Devuelve solo las carreras "
        "activas, ordenadas por nombre."
    ),
)
def listar_carreras(session: Session = Depends(get_session)) -> list[CarreraResponse]:
    carreras = PgCohorteRepository(session).listar_carreras_activas()
    return [CarreraResponse.model_validate(carrera) for carrera in carreras]
