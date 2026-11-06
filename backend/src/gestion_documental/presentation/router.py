"""Endpoints de los PDFs (US-CORE-003): la subida y la descarga del aspirante (con su link) y
la descarga del coordinador. Ninguna URL sirve el disco directamente (ADR-002)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO
from src.autenticacion.presentation.dependencies import MENSAJE_SIN_PERMISO, require_role
from src.gestion_documental.application.obtener_documento import (
    MENSAJE_DOCUMENTO_NO_ENCONTRADO,
    obtener_documento,
)
from src.gestion_documental.application.subir_documento import (
    MENSAJE_LEGAJO_NO_EDITABLE,
    subir_documento,
)
from src.gestion_documental.domain.documento import DocumentoGuardado
from src.gestion_documental.domain.pdf import MENSAJE_NO_ES_PDF
from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES, TipoDocumento
from src.gestion_documental.infrastructure.almacenamiento import (
    borrar_pdf,
    guardar_pdf,
    ruta_del_pdf,
)
from src.gestion_documental.infrastructure.pg_repository import PgDocumentoRepository
from src.gestion_documental.presentation.schemas import DocumentoResponse
from src.inscripcion.presentation.dependencies import MENSAJE_LINK_INVALIDO, legajo_id_desde_token
from src.shared.database import get_session
from src.shared.errors import NoEncontrado
from src.shared.roles import Rol

router = APIRouter(tags=["Documentos"])


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger, con el formato de ARQUITECTURA §11.2."""
    ejemplo = {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-04T14:20:00Z",
    }
    return {"content": {"application/json": {"example": ejemplo}}}


RESPUESTA_PDF: dict[int | str, dict[str, Any]] = {
    200: {"description": "El PDF", "content": {"application/pdf": {}}},
}
LINK_INVALIDO: dict[int | str, dict[str, Any]] = {
    404: {
        "description": "El link no existe o venció, o el documento no es de ese legajo",
        **_error(404, "NOT_FOUND", MENSAJE_LINK_INVALIDO),
    },
}


def _pdf(documento: DocumentoGuardado) -> FileResponse:
    ruta = ruta_del_pdf(documento.path_storage)
    if not ruta.is_file():
        raise NoEncontrado(MENSAJE_DOCUMENTO_NO_ENCONTRADO)
    # inline: el navegador lo muestra (vista previa) en vez de bajarlo. no-store: un PDF con
    # datos personales no queda en la caché del navegador ni de un proxy. El nosniff lo pone
    # el middleware de headers de seguridad.
    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=documento.nombre_original,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )


@router.post(
    "/seguimiento/{token}/documentos",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentoResponse,
    summary="Subir un PDF",
    description=(
        "Aspirante, con el token de su link. `multipart/form-data` con `tipo` y `archivo`. "
        "Solo PDF de verdad (se miran los primeros bytes, no la extensión) y de hasta 5 MB, de un "
        "tipo que le corresponda a ese legajo, y solo en BORRADOR u OBSERVADO. Si ya había uno "
        "de ese tipo, lo reemplaza. En disco se guarda con un nombre UUID y su SHA-256 (ADR-002)."
    ),
    responses={
        **LINK_INVALIDO,
        409: {
            "description": "El legajo ya no está en BORRADOR ni en OBSERVADO",
            **_error(409, "LEGAJO_NO_EDITABLE", MENSAJE_LEGAJO_NO_EDITABLE),
        },
        422: {
            "description": (
                "No es un PDF, supera 5 MB o el tipo no le corresponde al legajo "
                "(`ARCHIVO_INVALIDO`), o falta `tipo` o `archivo` (`VALIDATION_ERROR`)"
            ),
            **_error(422, "ARCHIVO_INVALIDO", MENSAJE_NO_ES_PDF, "archivo"),
        },
    },
)
def subir(
    tipo: TipoDocumento = Form(),
    archivo: UploadFile = File(),
    legajo_id: UUID = Depends(legajo_id_desde_token),
    session: Session = Depends(get_session),
) -> DocumentoResponse:
    # Se lee como mucho un byte más que el máximo: alcanza para saber que se pasa, sin cargar
    # en memoria un archivo enorme.
    contenido = archivo.file.read(TAMANIO_MAXIMO_BYTES + 1)
    documento = subir_documento(
        legajo_id,
        tipo,
        archivo.filename,
        contenido,
        PgDocumentoRepository(session),
        guardar_pdf,
        borrar_pdf,
    )
    return DocumentoResponse.desde(documento)


@router.get(
    "/seguimiento/{token}/documentos/{documento_id}/download",
    response_class=FileResponse,
    summary="Descargar uno de mis PDFs",
    description=(
        "Aspirante, con el token de su link. Solo los documentos de su propio legajo: uno de "
        "otro legajo da el mismo 404 que uno que no existe (NFR-S02)."
    ),
    responses={**RESPUESTA_PDF, **LINK_INVALIDO},
)
def descargar_como_aspirante(
    documento_id: UUID,
    legajo_id: UUID = Depends(legajo_id_desde_token),
    session: Session = Depends(get_session),
) -> FileResponse:
    return _pdf(obtener_documento(documento_id, PgDocumentoRepository(session), legajo_id))


@router.get(
    "/documentos/{documento_id}/download",
    response_class=FileResponse,
    dependencies=[Depends(require_role(Rol.COORDINADOR))],
    summary="Descargar un PDF (coordinador)",
    description="Coordinador. Cualquier documento de cualquier legajo.",
    responses={
        **RESPUESTA_PDF,
        401: {
            "description": "Sin token, con un token inválido o vencido, o con un usuario inactivo",
            **_error(401, "UNAUTHORIZED", MENSAJE_TOKEN_INVALIDO),
        },
        403: {
            "description": "El usuario no es coordinador",
            **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
        },
        404: {
            "description": "El documento no existe",
            **_error(404, "NOT_FOUND", MENSAJE_DOCUMENTO_NO_ENCONTRADO),
        },
    },
)
def descargar_como_coordinador(
    documento_id: UUID, session: Session = Depends(get_session)
) -> FileResponse:
    return _pdf(obtener_documento(documento_id, PgDocumentoRepository(session)))
