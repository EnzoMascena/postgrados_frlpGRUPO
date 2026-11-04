"""Endpoints del coordinador sobre un legajo: el detalle y el cambio de estado (US-CORE-005).

Las rutas fijas que vienen en L4 y L5 (`/legajos/resumen`, `/legajos/exportar`) se declaran
antes que `/legajos/{legajo_id}`: si no, FastAPI intenta leer "resumen" como un UUID.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO
from src.autenticacion.presentation.dependencies import (
    MENSAJE_SIN_PERMISO,
    actor_desde_usuario,
    require_role,
)
from src.legajos.application.cambiar_estado import MENSAJE_LEGAJO_NO_ENCONTRADO, ServicioEstados
from src.legajos.application.obtener_detalle import obtener_detalle
from src.legajos.domain.estados import MENSAJE_COMENTARIO_OBLIGATORIO
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.dependencies import get_servicio_estados
from src.legajos.presentation.schemas import (
    CambiarEstadoRequest,
    LegajoDetalleCoordinadorResponse,
)
from src.shared.database import get_session
from src.shared.roles import Rol

router = APIRouter(prefix="/legajos", tags=["Legajos"])

solo_coordinador = require_role(Rol.COORDINADOR)


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger, con el formato de ARQUITECTURA §11.2."""
    ejemplo = {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-03T14:20:00Z",
    }
    return {"content": {"application/json": {"example": ejemplo}}}


ERRORES_DE_ACCESO: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Sin token, con un token inválido o vencido, o con un usuario inactivo",
        **_error(401, "UNAUTHORIZED", MENSAJE_TOKEN_INVALIDO),
    },
    403: {
        "description": "El usuario no es coordinador",
        **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
    },
    404: {
        "description": "El legajo no existe",
        **_error(404, "NOT_FOUND", MENSAJE_LEGAJO_NO_ENCONTRADO),
    },
}


def _detalle(legajo_id: UUID, session: Session) -> LegajoDetalleCoordinadorResponse:
    detalle = obtener_detalle(legajo_id, PgLegajoRepository(session), "coordinador")
    return LegajoDetalleCoordinadorResponse.model_validate(detalle)


@router.get(
    "/{legajo_id}",
    response_model=LegajoDetalleCoordinadorResponse,
    summary="Detalle del legajo",
    description=(
        "Coordinador. Todos los datos del legajo con su cohorte y carreras, el checklist de "
        "documentos (los que le corresponden, con los datos del archivo si ya está cargado), "
        "los faltantes, la última observación, el historial de cambios de estado y las "
        "acciones que el coordinador puede hacer ahora (`accionesPermitidas`), que el front "
        "muestra como botones."
    ),
    responses=ERRORES_DE_ACCESO,
)
def ver_detalle(
    legajo_id: UUID,
    _: Usuario = Depends(solo_coordinador),
    session: Session = Depends(get_session),
) -> LegajoDetalleCoordinadorResponse:
    return _detalle(legajo_id, session)


@router.patch(
    "/{legajo_id}/estado",
    response_model=LegajoDetalleCoordinadorResponse,
    summary="Cambiar el estado del legajo",
    description=(
        "Coordinador. Aplica una acción de la máquina de estados (plan §9): REVISAR, OBSERVAR, "
        "APROBAR, RECHAZAR, MATRICULAR o DAR_DE_BAJA. Deja una fila en el historial, manda el "
        "email que corresponda y responde el detalle actualizado. OBSERVAR exige un comentario "
        "de 5 caracteres o más; en RECHAZAR y DAR_DE_BAJA es opcional. APROBAR genera el número "
        "de legajo (`AA-CCC-SSS`)."
    ),
    responses={
        **ERRORES_DE_ACCESO,
        403: {
            "description": (
                "El usuario no es coordinador, o la acción no es del coordinador (ENVIAR y "
                "CORREGIR son del aspirante; VENCER y GRADUAR, del sistema)"
            ),
            **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
        },
        409: {
            "description": "La acción no corresponde al estado actual del legajo",
            **_error(
                409, "TRANSICION_INVALIDA", "No se puede APROBAR un legajo en estado PENDIENTE"
            ),
        },
        422: {
            "description": "OBSERVAR sin comentario suficiente, o una acción que no existe",
            **_error(422, "VALIDATION_ERROR", MENSAJE_COMENTARIO_OBLIGATORIO, "comentario"),
        },
    },
)
def cambiar_estado(
    legajo_id: UUID,
    datos: CambiarEstadoRequest,
    usuario: Usuario = Depends(solo_coordinador),
    servicio: ServicioEstados = Depends(get_servicio_estados),
    session: Session = Depends(get_session),
) -> LegajoDetalleCoordinadorResponse:
    servicio.cambiar(legajo_id, datos.accion, actor_desde_usuario(usuario), datos.comentario)
    return _detalle(legajo_id, session)
