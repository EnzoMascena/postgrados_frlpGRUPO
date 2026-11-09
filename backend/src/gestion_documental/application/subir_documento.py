"""Caso de uso: el aspirante sube un PDF a su legajo (US-CORE-003).

Recibe por parámetro el repositorio y las funciones que escriben y borran en disco: no sabe nada
de la base ni del sistema de archivos, y se testea con piezas falsas.
"""

from collections.abc import Callable
from pathlib import PurePath
from typing import Protocol
from uuid import UUID

from src.gestion_documental.domain.documento import DocumentoGuardado
from src.gestion_documental.domain.pdf import (
    MENSAJE_TIPO_NO_CORRESPONDE,
    ArchivoInvalido,
    validar_pdf,
)
from src.gestion_documental.domain.repo import DocumentoRepository
from src.gestion_documental.domain.requisitos import documentos_requeridos
from src.gestion_documental.domain.tipos import TipoDocumento
from src.inscripcion.domain.errores import LegajoNoEditable
from src.legajos.application.obtener_detalle import ESTADOS_EDITABLES
from src.shared.errors import NoEncontrado

MENSAJE_LEGAJO_NO_ENCONTRADO = "No encontramos el legajo"
MENSAJE_LEGAJO_NO_EDITABLE = (
    "Tu legajo ya fue enviado: solo podés subir documentos en borrador o si te lo observaron"
)
NOMBRE_POR_DEFECTO = "documento.pdf"
LARGO_MAXIMO_NOMBRE = 255  # el de la columna nombre_original


class ArchivoEnDisco(Protocol):
    """Lo que devuelve `guardar_pdf` (`PdfGuardado`)."""

    @property
    def path_storage(self) -> str: ...
    @property
    def checksum_sha256(self) -> str: ...
    @property
    def tamanio_bytes(self) -> int: ...


GuardarPdf = Callable[[bytes, UUID, UUID], ArchivoEnDisco]  # contenido, cohorte, legajo
BorrarPdf = Callable[[str], None]  # path_storage


def subir_documento(
    legajo_id: UUID,
    tipo: TipoDocumento,
    nombre_original: str | None,
    contenido: bytes,
    repo: DocumentoRepository,
    guardar_pdf: GuardarPdf,
    borrar_pdf: BorrarPdf,
) -> DocumentoGuardado:
    legajo = repo.legajo(legajo_id)
    if legajo is None:
        raise NoEncontrado(MENSAJE_LEGAJO_NO_ENCONTRADO)
    # El mismo criterio que `puedeEditar` del detalle: solo en BORRADOR u OBSERVADO.
    if legajo.estado not in ESTADOS_EDITABLES:
        raise LegajoNoEditable(MENSAJE_LEGAJO_NO_EDITABLE)
    if tipo not in documentos_requeridos(legajo.solicita_beca, legajo.tiene_titulo_posgrado):
        raise ArchivoInvalido(MENSAJE_TIPO_NO_CORRESPONDE, campo="tipo")
    validar_pdf(contenido)

    archivo = guardar_pdf(contenido, legajo.cohorte_id, legajo.id)
    try:
        documento, path_anterior = repo.guardar_documento(
            legajo.id,
            tipo,
            archivo.path_storage,
            _nombre_seguro(nombre_original),
            archivo.checksum_sha256,
            archivo.tamanio_bytes,
        )
    except Exception:
        borrar_pdf(archivo.path_storage)  # que no quede en disco un archivo sin su fila
        raise
    # El archivo viejo se borra recién ahora: si la base fallaba, la fila seguía apuntándole.
    if path_anterior is not None:
        borrar_pdf(path_anterior)
    return documento


def _nombre_seguro(nombre_original: str | None) -> str:
    """Solo el nombre del archivo (algunos navegadores mandan la ruta entera), con su largo máximo.

    Se usa únicamente para mostrarlo y para el nombre de la descarga: en disco va un UUID.
    """
    nombre = PurePath((nombre_original or "").replace("\\", "/")).name.strip()
    return (nombre or NOMBRE_POR_DEFECTO)[-LARGO_MAXIMO_NOMBRE:]
