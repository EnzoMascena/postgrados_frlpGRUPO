"""Endpoints del coordinador sobre los legajos: la búsqueda y el resumen del dashboard
(US-CORE-007), y el detalle y el cambio de estado de uno (US-CORE-005).

Las rutas fijas (`/legajos/resumen` y, en L5, `/legajos/exportar`) se declaran antes que
`/legajos/{legajo_id}`: FastAPI prueba las rutas en orden, y si no, intenta leer "resumen" como
un UUID y contesta 422.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO
from src.autenticacion.presentation.dependencies import (
    MENSAJE_SIN_PERMISO,
    actor_desde_usuario,
    require_role,
)
from src.legajos.application.buscar_legajos import (
    MENSAJE_APELLIDO_CORTO,
    FiltrosBusqueda,
    buscar_legajos,
)
from src.legajos.application.cambiar_estado import MENSAJE_LEGAJO_NO_ENCONTRADO, ServicioEstados
from src.legajos.application.obtener_detalle import obtener_detalle
from src.legajos.application.resumen import obtener_resumen
from src.legajos.domain.estados import MENSAJE_COMENTARIO_OBLIGATORIO, EstadoLegajo
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.legajos.presentation.dependencies import get_servicio_estados
from src.legajos.presentation.schemas import (
    CambiarEstadoRequest,
    LegajoDetalleCoordinadorResponse,
    PaginaLegajosResponse,
    ResumenLegajosResponse,
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


ERRORES_DE_SESION: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Sin token, con un token inválido o vencido, o con un usuario inactivo",
        **_error(401, "UNAUTHORIZED", MENSAJE_TOKEN_INVALIDO),
    },
    403: {
        "description": "El usuario no es coordinador",
        **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
    },
}

ERRORES_DE_ACCESO: dict[int | str, dict[str, Any]] = {
    **ERRORES_DE_SESION,
    404: {
        "description": "El legajo no existe",
        **_error(404, "NOT_FOUND", MENSAJE_LEGAJO_NO_ENCONTRADO),
    },
}


# --- Rutas fijas: antes que /{legajo_id} ---


@router.get(
    "",
    response_model=PaginaLegajosResponse,
    summary="Buscar legajos",
    description=(
        "Coordinador. El listado del dashboard, de a una página y con los más nuevos primero. "
        "`q` con solo dígitos busca el DNI exacto; si no, una parte del apellido sin distinguir "
        "mayúsculas, con 3 letras como mínimo. `estado`, `cohorte`, `carrera` y `beca` se "
        "combinan con `q`. `total` es la cantidad sin paginar. `documentosCargados` cuenta solo "
        "los documentos que le corresponden al aspirante."
    ),
    responses={
        **ERRORES_DE_SESION,
        422: {
            "description": (
                "`q` con letras y menos de 3 caracteres, o un parámetro con un valor que no "
                "corresponde (`page` menor que 1, `size` fuera de 1 a 100, un estado que no "
                "existe, un id que no es UUID)"
            ),
            **_error(422, "VALIDATION_ERROR", MENSAJE_APELLIDO_CORTO, "q"),
        },
    },
)
def buscar(
    q: str | None = Query(
        None,
        max_length=100,
        description="DNI exacto (solo dígitos) o parte del apellido (3 letras o más)",
        examples=["rodr"],
    ),
    estado: EstadoLegajo | None = Query(None, description="Un solo estado"),
    cohorte: UUID | None = Query(None, description="Id de la cohorte"),
    carrera: UUID | None = Query(None, description="Id de la carrera, en 1ª o 2ª opción"),
    beca: bool | None = Query(None, description="`true` solo los que pidieron beca"),
    page: int = Query(1, ge=1, description="Página, desde 1"),
    size: int = Query(20, ge=1, le=100, description="Legajos por página, de 1 a 100"),
    _: Usuario = Depends(solo_coordinador),
    session: Session = Depends(get_session),
) -> PaginaLegajosResponse:
    filtros = FiltrosBusqueda(
        q=q,
        estado=estado,
        cohorte_id=cohorte,
        carrera_id=carrera,
        beca=beca,
        page=page,
        size=size,
    )
    pagina = buscar_legajos(filtros, PgLegajoRepository(session))
    return PaginaLegajosResponse.model_validate(pagina)


@router.get(
    "/resumen",
    response_model=ResumenLegajosResponse,
    summary="Resumen para el dashboard",
    description=(
        "Coordinador. Los conteos de las tarjetas: el total, cuántos hay en cada uno de los 10 "
        "estados (con 0 en los que no tienen ninguno) y cuántos pidieron beca, de cada tipo. "
        "Sin `cohorte`, cuenta todas."
    ),
    responses={
        **ERRORES_DE_SESION,
        422: {
            "description": "`cohorte` no es un UUID",
            **_error(422, "VALIDATION_ERROR", "Input should be a valid UUID", "cohorte"),
        },
    },
)
def resumen(
    cohorte: UUID | None = Query(None, description="Id de la cohorte; sin él, todas"),
    _: Usuario = Depends(solo_coordinador),
    session: Session = Depends(get_session),
) -> ResumenLegajosResponse:
    return ResumenLegajosResponse.model_validate(
        obtener_resumen(cohorte, PgLegajoRepository(session))
    )


# --- Un legajo ---


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
