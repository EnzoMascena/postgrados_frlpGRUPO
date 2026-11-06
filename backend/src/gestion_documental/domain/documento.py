"""Los datos con los que trabajan la subida y la descarga de PDFs. Python puro."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.gestion_documental.domain.tipos import TipoDocumento
from src.legajos.domain.estados import EstadoLegajo


@dataclass(frozen=True)
class LegajoParaDocumentos:
    """Lo que hace falta saber del legajo para aceptar un PDF: dónde va y si le corresponde."""

    id: UUID
    cohorte_id: UUID
    estado: EstadoLegajo
    solicita_beca: bool
    tiene_titulo_posgrado: bool


@dataclass(frozen=True)
class DocumentoGuardado:
    """Una fila de `documentos`. El archivo vive en disco, en `path_storage`."""

    id: UUID
    legajo_id: UUID
    tipo: TipoDocumento
    path_storage: str  # relativo a STORAGE_PATH: uploads/{cohorte}/{legajo}/{uuid}.pdf
    nombre_original: str
    checksum_sha256: str
    tamanio_bytes: int
    fecha_subida: datetime
