"""
Guardado seguro de PDFs (ASR-001, RF-CORE-002, ARQUITECTURA §9).

Reglas no negociables:

  - El archivo vive en STORAGE_PATH, FUERA de cualquier carpeta pública: no
    existe ninguna URL que apunte a él. Solo se lee desde
    GET /api/v1/documentos/{id}/download, que verifica permisos.
  - El nombre en disco es un UUID generado acá, nunca el nombre original.
  - El tipo se verifica por los MAGIC BYTES (%PDF al principio), no por la
    extensión ni por el Content-Type: esos los manda el cliente y se pueden
    falsear.
  - Hasta 5 MB. Se lee por bloques (ASR-004): si se pasa del límite, se
    corta ahí, sin cargar el archivo entero en memoria.
  - Se guarda su SHA-256: así se detecta si alguien lo altera en disco.

    STORAGE_PATH/uploads/{cohorte_id}/{legajo_id}/{uuid}.pdf

Es Python puro: recibe un archivo binario (el `UploadFile.file` de FastAPI
o un io.BytesIO en los tests) y lanza ArchivoInvalido con el mensaje exacto
del SRS. El service decide qué hacer y el controller elige el status.
"""

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.core import config
from app.core.excepciones import ArchivoInvalido

MAGIC_PDF = b"%PDF"
_BLOQUE = 64 * 1024

# Los mensajes exactos de RF-CORE-002.
MENSAJE_NO_ES_PDF = "Solo se aceptan archivos en formato PDF"
MENSAJE_MUY_GRANDE = "El archivo es demasiado grande. Máximo permitido: 5MB"


@dataclass(frozen=True)
class PdfGuardado:
    """Lo que el repository guarda en la tabla documentos."""

    path_storage: str  # Relativa a STORAGE_PATH: es lo que va a la base.
    checksum_sha256: str
    tamanio_bytes: int


def _raiz() -> Path:
    return Path(config.STORAGE_PATH).resolve()


def guardar_pdf(
    archivo: BinaryIO, cohorte_id: UUID, legajo_id: UUID, *, campo: str | None = None
) -> PdfGuardado:
    """Valida y guarda el PDF con nombre UUID. Lanza ArchivoInvalido si no sirve.

    `campo` es el nombre del campo del formulario, para que el error se
    muestre al lado de su caja.
    """
    carpeta_relativa = Path("uploads") / str(cohorte_id) / str(legajo_id)
    carpeta = _raiz() / carpeta_relativa
    carpeta.mkdir(parents=True, exist_ok=True)

    nombre = f"{uuid.uuid4()}.pdf"
    destino = carpeta / nombre
    # Se escribe en un temporal y recién al final se renombra: nunca queda un
    # PDF a medio escribir con su nombre definitivo.
    temporal = carpeta / f".{nombre}.parcial"
    sha256 = hashlib.sha256()
    tamanio = 0

    try:
        with temporal.open("wb") as salida:
            bloque = archivo.read(_BLOQUE)
            if not bloque.startswith(MAGIC_PDF):
                raise ArchivoInvalido(MENSAJE_NO_ES_PDF, campo=campo)
            while bloque:
                tamanio += len(bloque)
                if tamanio > config.MAX_PDF_BYTES:
                    raise ArchivoInvalido(MENSAJE_MUY_GRANDE, campo=campo)
                sha256.update(bloque)
                salida.write(bloque)
                bloque = archivo.read(_BLOQUE)
        temporal.replace(destino)
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise

    return PdfGuardado(
        path_storage=str(carpeta_relativa / nombre),
        checksum_sha256=sha256.hexdigest(),
        tamanio_bytes=tamanio,
    )


def ruta_del_pdf(path_storage: str) -> Path:
    """La ruta absoluta del PDF, verificando que esté DENTRO de STORAGE_PATH.

    Defensa en profundidad contra el path traversal: aunque alguien lograra
    meter "../../etc/passwd" en la base, nunca se lee nada fuera del
    almacenamiento.
    """
    raiz = _raiz()
    ruta = (raiz / path_storage).resolve()
    if not ruta.is_relative_to(raiz):
        raise ValueError(f"Ruta fuera del almacenamiento de PDFs: {path_storage!r}")
    return ruta


def borrar_pdf(path_storage: str) -> None:
    """Borra el PDF del disco (por ejemplo, cuando el aspirante lo reemplaza)."""
    ruta_del_pdf(path_storage).unlink(missing_ok=True)
