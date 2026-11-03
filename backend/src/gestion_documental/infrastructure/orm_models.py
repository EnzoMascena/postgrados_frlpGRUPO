"""Tabla `documentos`: los PDFs de cada legajo (el archivo vive en disco, acá solo sus datos)."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, func
from sqlmodel import Field, SQLModel

from src.gestion_documental.domain.tipos import TAMANIO_MAXIMO_BYTES, TipoDocumento
from src.shared.orm import ahora_utc, columna_fecha, valores_para_check


class DocumentoORM(SQLModel, table=True):
    __tablename__ = "documentos"
    __table_args__ = (
        # Subir otro documento del mismo tipo lo reemplaza: nunca hay dos.
        UniqueConstraint("legajo_id", "tipo", name="uq_documentos_legajo_tipo"),
        CheckConstraint(
            f"tipo IN ({valores_para_check(TipoDocumento)})", name="ck_documentos_tipo"
        ),
        CheckConstraint(
            f"tamanio_bytes BETWEEN 1 AND {TAMANIO_MAXIMO_BYTES}", name="ck_documentos_tamanio"
        ),
        Index("ix_documentos_legajo_id", "legajo_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", ondelete="CASCADE")
    tipo: str = Field(max_length=50)
    path_storage: str = Field(max_length=500)
    nombre_original: str = Field(max_length=255)
    checksum_sha256: str = Field(max_length=64)
    tamanio_bytes: int
    fecha_subida: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
