"""Lo que la gestión documental necesita de la base, sin decir cómo se guarda. Python puro.

La implementación con SQLModel vive en `infrastructure/pg_repository.py`; en los tests unitarios
se usa una falsa en memoria.
"""

from typing import Protocol
from uuid import UUID

from src.gestion_documental.domain.documento import DocumentoGuardado, LegajoParaDocumentos
from src.gestion_documental.domain.tipos import TipoDocumento


class DocumentoRepository(Protocol):
    def legajo(self, legajo_id: UUID) -> LegajoParaDocumentos | None:
        """Los datos del legajo que importan para subir un PDF, o `None` si no existe."""
        ...

    def documento(self, documento_id: UUID) -> DocumentoGuardado | None:
        """El documento con ese id, de cualquier legajo, o `None` si no existe."""
        ...

    def guardar_documento(
        self,
        legajo_id: UUID,
        tipo: TipoDocumento,
        path_storage: str,
        nombre_original: str,
        checksum_sha256: str,
        tamanio_bytes: int,
    ) -> tuple[DocumentoGuardado, str | None]:
        """Guarda el documento de ese tipo, reemplazando al anterior si había uno.

        Devuelve el documento guardado y el `path_storage` del archivo reemplazado (o `None`),
        para que quien llama lo borre del disco recién cuando la base ya cambió.
        """
        ...
