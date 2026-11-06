"""Los PDFs en disco (ADR-002).

Cada archivo va a `{STORAGE_PATH}/uploads/{cohorte_id}/{legajo_id}/{uuid}.pdf`: el nombre es un
UUID nuevo, nunca el que eligió el aspirante, y `STORAGE_PATH` no lo sirve ninguna URL. Los PDFs
solo salen por los endpoints de descarga, que controlan quién los pide.
"""

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.shared.config import settings


@dataclass(frozen=True)
class PdfGuardado:
    path_storage: str  # relativo a STORAGE_PATH, con "/": así se guarda en la base
    checksum_sha256: str
    tamanio_bytes: int


def _raiz() -> Path:
    return Path(settings.storage_path).resolve()


def guardar_pdf(contenido: bytes, cohorte_id: UUID, legajo_id: UUID) -> PdfGuardado:
    """Escribe el PDF (ya validado) en disco y devuelve dónde quedó, su SHA-256 y su tamaño."""
    relativo = Path("uploads", str(cohorte_id), str(legajo_id), f"{uuid.uuid4()}.pdf")
    destino = _raiz() / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return PdfGuardado(
        path_storage=relativo.as_posix(),
        checksum_sha256=hashlib.sha256(contenido).hexdigest(),
        tamanio_bytes=len(contenido),
    )


def ruta_del_pdf(path_storage: str) -> Path:
    """La ruta absoluta del archivo. Nunca sale de STORAGE_PATH, aunque la base diga otra cosa."""
    raiz = _raiz()
    ruta = (raiz / path_storage).resolve()
    if not ruta.is_relative_to(raiz):
        raise ValueError(f"La ruta {path_storage!r} sale de STORAGE_PATH")
    return ruta


def borrar_pdf(path_storage: str) -> None:
    """Borra el archivo; si ya no estaba, no pasa nada."""
    ruta_del_pdf(path_storage).unlink(missing_ok=True)
