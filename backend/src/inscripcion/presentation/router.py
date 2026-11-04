"""Endpoints públicos de la inscripción: `POST /legajos` y `POST /legajos/recuperar-acceso`."""

from datetime import date
from functools import partial
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from src.inscripcion.application.inscribir import MENSAJE_CARRERA_NO_DISPONIBLE, inscribir
from src.inscripcion.application.recuperar_acceso import (
    MENSAJE_RECUPERAR_ACCESO,
    recuperar_acceso,
)
from src.inscripcion.domain.inscripcion import MENSAJE_DNI_REPETIDO, mensaje_periodo_cerrado
from src.inscripcion.infrastructure.links import (
    crear_link_seguimiento,
    enviar_link_de_seguimiento,
)
from src.inscripcion.infrastructure.pg_repository import PgInscripcionRepository
from src.inscripcion.presentation.schemas import (
    InscripcionRequest,
    InscripcionResponse,
    RecuperarAccesoRequest,
    RecuperarAccesoResponse,
)
from src.shared.database import get_session

router = APIRouter(prefix="/legajos", tags=["Inscripción"])


def _cuerpo_de_error(
    status: int, codigo: str, mensaje: str, campo: str | None = None
) -> dict[str, Any]:
    """El cuerpo de un error de ejemplo, con el formato de ARQUITECTURA §11.2."""
    return {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-03T14:20:00Z",
    }


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger."""
    ejemplo = _cuerpo_de_error(status, codigo, mensaje, campo)
    return {"content": {"application/json": {"example": ejemplo}}}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=InscripcionResponse,
    summary="Inscribirse (crear el borrador)",
    description=(
        "Público: lo usa el formulario (NFR-S01). Crea el legajo en BORRADOR con un código de "
        "seguimiento y manda por email el link para seguir la inscripción, que vence a los 60 "
        "días (ADR-005). El `token` de la respuesta es el mismo del link: en la base se guarda "
        "solo su hash. El DNI se guarda sin puntos ni espacios y los emails en minúsculas.\n\n"
        "Los ids del ejemplo son inventados y dan 422: para probar, sacá `cohorteId` de "
        "`GET /cohortes` y `carreraIds` de `GET /carreras`."
    ),
    responses={
        409: {
            "description": (
                "La cohorte tiene la inscripción cerrada (`PERIODO_CERRADO`), o el DNI o el email "
                "ya están inscriptos en esa cohorte (`CONFLICT`, con `field`)"
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "dni_repetido": {
                            "summary": "El DNI ya está inscripto en la cohorte",
                            "value": _cuerpo_de_error(409, "CONFLICT", MENSAJE_DNI_REPETIDO, "dni"),
                        },
                        "periodo_cerrado": {
                            "summary": "La cohorte tiene la inscripción cerrada",
                            "value": _cuerpo_de_error(
                                409,
                                "PERIODO_CERRADO",
                                mensaje_periodo_cerrado(date(2027, 3, 1)),
                            ),
                        },
                    }
                }
            },
        },
        422: {
            "description": (
                "Un campo no cumple una regla: DNI de 7 u 8 dígitos, emails válidos, motivación "
                "de 50 caracteres o más, 1 o 2 carreras distintas y activas, tipo de beca solo si "
                "la pide, o una cohorte que no existe"
            ),
            **_error(422, "VALIDATION_ERROR", MENSAJE_CARRERA_NO_DISPONIBLE, "carreraIds"),
        },
    },
)
def crear_legajo(
    datos: InscripcionRequest, session: Session = Depends(get_session)
) -> InscripcionResponse:
    creado = inscribir(
        datos.a_datos(),
        PgInscripcionRepository(session),
        partial(crear_link_seguimiento, session),
        enviar_link_de_seguimiento,
    )
    return InscripcionResponse.model_validate(creado)


@router.post(
    "/recuperar-acceso",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RecuperarAccesoResponse,
    summary="Pedir un link nuevo",
    description=(
        "Público. Si hay una preinscripción con ese email, manda un link nuevo de la más "
        "reciente. Responde siempre lo mismo, exista o no el email, para no revelar quién se "
        "inscribió. Los links anteriores siguen andando hasta que vencen."
    ),
    responses={
        422: {
            "description": "El email no es válido",
            **_error(422, "VALIDATION_ERROR", "El valor de email no es válido", "email"),
        },
    },
)
def pedir_link_nuevo(
    datos: RecuperarAccesoRequest, session: Session = Depends(get_session)
) -> RecuperarAccesoResponse:
    recuperar_acceso(
        datos.email,
        PgInscripcionRepository(session),
        partial(crear_link_seguimiento, session),
        enviar_link_de_seguimiento,
    )
    return RecuperarAccesoResponse(mensaje=MENSAJE_RECUPERAR_ACCESO)
