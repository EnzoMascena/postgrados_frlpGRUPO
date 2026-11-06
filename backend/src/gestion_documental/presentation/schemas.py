"""Schemas de los documentos (plan §10): JSON en camelCase, atributos en snake_case."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from src.gestion_documental.domain.documento import DocumentoGuardado
from src.gestion_documental.domain.tipos import TipoDocumento
from src.shared.schemas import CamelModel


class DocumentoResponse(CamelModel):
    """La respuesta 201 de la subida. `path_storage` no sale nunca: el disco no se expone."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "documentoId": "9f1c2d3e-4a5b-4c6d-8e7f-0a1b2c3d4e5f",
                    "tipo": "DNI",
                    "nombreOriginal": "dni.pdf",
                    "tamanioBytes": 183412,
                    "checksumSha256": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
                    "fechaSubida": "2026-11-04T14:01:00Z",
                }
            ]
        }
    )

    documento_id: UUID
    tipo: TipoDocumento
    nombre_original: str
    tamanio_bytes: int
    checksum_sha256: str
    fecha_subida: datetime

    @classmethod
    def desde(cls, documento: DocumentoGuardado) -> "DocumentoResponse":
        return cls(
            documento_id=documento.id,
            tipo=documento.tipo,
            nombre_original=documento.nombre_original,
            tamanio_bytes=documento.tamanio_bytes,
            checksum_sha256=documento.checksum_sha256,
            fecha_subida=documento.fecha_subida,
        )
