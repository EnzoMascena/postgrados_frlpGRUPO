"""Tabla `tokens_seguimiento`: los links con los que el aspirante vuelve a su legajo."""

import uuid
from datetime import datetime

from sqlalchemy import UniqueConstraint, func
from sqlmodel import Field, SQLModel

from src.shared.orm import ahora_utc, columna_fecha


class TokenSeguimientoORM(SQLModel, table=True):
    """Se guarda el hash SHA-256 del token, nunca el token: el link no se puede reconstruir."""

    __tablename__ = "tokens_seguimiento"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_tokens_seguimiento_token_hash"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", ondelete="CASCADE")
    token_hash: str = Field(max_length=64)
    expira_en: datetime = Field(sa_column=columna_fecha())
    created_at: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
