"""Endpoints de cohortes y carreras: `GET /cohortes` y `GET /carreras` (públicos)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.cohortes.infrastructure.pg_repository import PgCohorteRepository
from src.cohortes.presentation.schemas import CarreraResponse, CohorteResponse
from src.shared.database import get_session

router = APIRouter(tags=["Cohortes y carreras"])


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
