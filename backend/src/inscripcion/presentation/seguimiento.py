"""Endpoints del aspirante con su link de seguimiento (ADR-005): ver su legajo (F5), editar sus
datos y enviarlo a revisión (F6)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.gestion_documental.infrastructure.pg_repository import PgDocumentoRepository
from src.inscripcion.application.editar_legajo import MENSAJE_LEGAJO_NO_EDITABLE, editar_legajo
from src.inscripcion.application.enviar_legajo import enviar_legajo
from src.inscripcion.infrastructure.pg_repository import PgInscripcionRepository
from src.inscripcion.presentation.dependencies import MENSAJE_LINK_INVALIDO, legajo_id_desde_token
from src.inscripcion.presentation.schemas import DatosLegajoRequest
from src.legajos.application.cambiar_estado import ServicioEstados
from src.legajos.application.obtener_detalle import obtener_detalle
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.dependencies import get_servicio_estados
from src.legajos.presentation.schemas import LegajoDetalleAspiranteResponse
from src.shared.database import get_session

router = APIRouter(prefix="/seguimiento", tags=["Seguimiento del aspirante"])


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger, con el formato de ARQUITECTURA §11.2."""
    ejemplo = {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-06T14:20:00Z",
    }
    return {"content": {"application/json": {"example": ejemplo}}}


LINK_INVALIDO: dict[int | str, dict[str, Any]] = {
    404: {
        "description": "El link no existe o venció",
        **_error(404, "NOT_FOUND", MENSAJE_LINK_INVALIDO),
    },
}


def _detalle(legajo_id: UUID, session: Session) -> LegajoDetalleAspiranteResponse:
    detalle = obtener_detalle(legajo_id, PgLegajoRepository(session), "aspirante")
    return LegajoDetalleAspiranteResponse.model_validate(detalle)


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
    return _detalle(legajo_id, session)


@router.put(
    "/{token}",
    response_model=LegajoDetalleAspiranteResponse,
    summary="Editar mis datos",
    description=(
        "Aspirante, con el token de su link. El mismo cuerpo que `POST /legajos` sin "
        "`cohorteId` (la cohorte no se cambia) y las mismas reglas, incluido el período abierto. "
        "El DNI y el email no pueden repetirse en la cohorte, sin contar al propio legajo. Solo "
        "en BORRADOR u OBSERVADO. Responde el detalle actualizado."
    ),
    responses={
        **LINK_INVALIDO,
        409: {
            "description": (
                "El legajo ya no está en BORRADOR ni en OBSERVADO (`LEGAJO_NO_EDITABLE`), la "
                "inscripción de la cohorte está cerrada (`PERIODO_CERRADO`), o el DNI o el email "
                "ya están en otro legajo de la cohorte (`CONFLICT`, con `field`)"
            ),
            **_error(409, "LEGAJO_NO_EDITABLE", MENSAJE_LEGAJO_NO_EDITABLE),
        },
        422: {
            "description": "Un campo no cumple su regla (las mismas que en `POST /legajos`)",
            **_error(422, "VALIDATION_ERROR", "El DNI tiene que tener 7 u 8 dígitos", "dni"),
        },
    },
)
def editar_mi_legajo(
    datos: DatosLegajoRequest,
    legajo_id: UUID = Depends(legajo_id_desde_token),
    session: Session = Depends(get_session),
) -> LegajoDetalleAspiranteResponse:
    editar_legajo(legajo_id, datos.a_datos_de_cohorte, PgInscripcionRepository(session))
    return _detalle(legajo_id, session)


@router.post(
    "/{token}/enviar",
    response_model=LegajoDetalleAspiranteResponse,
    summary="Enviar mi legajo a revisión",
    description=(
        "Aspirante, con el token de su link. Sin cuerpo. En BORRADOR hace ENVIAR y en OBSERVADO "
        "hace CORREGIR: el legajo pasa a PENDIENTE, queda en el historial y llega el email de "
        "confirmación. Si falta un documento obligatorio no cambia nada y responde 422 "
        "`DOCUMENTOS_FALTANTES` con los nombres de los que faltan."
    ),
    responses={
        **LINK_INVALIDO,
        409: {
            "description": "El legajo no está en BORRADOR ni en OBSERVADO",
            **_error(
                409, "TRANSICION_INVALIDA", "No se puede ENVIAR un legajo en estado PENDIENTE"
            ),
        },
        422: {
            "description": "Falta algún documento obligatorio",
            **_error(
                422,
                "DOCUMENTOS_FALTANTES",
                "Faltan documentos obligatorios: Copia del título de grado",
            ),
        },
    },
)
def enviar_mi_legajo(
    legajo_id: UUID = Depends(legajo_id_desde_token),
    servicio: ServicioEstados = Depends(get_servicio_estados),
    session: Session = Depends(get_session),
) -> LegajoDetalleAspiranteResponse:
    enviar_legajo(legajo_id, PgDocumentoRepository(session), servicio.cambiar)
    return _detalle(legajo_id, session)
