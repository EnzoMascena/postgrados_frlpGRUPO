"""Tablas `carreras` y `cohortes`."""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlmodel import Field, SQLModel

from src.cohortes.domain.tipos import TipoCarrera
from src.shared.orm import ahora_utc, columna_fecha, valores_para_check


class CarreraORM(SQLModel, table=True):
    __tablename__ = "carreras"
    __table_args__ = (
        UniqueConstraint("nombre", name="uq_carreras_nombre"),
        CheckConstraint(f"tipo IN ({valores_para_check(TipoCarrera)})", name="ck_carreras_tipo"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(max_length=200)
    tipo: str = Field(max_length=30)
    activa: bool = True


class CohorteORM(SQLModel, table=True):
    __tablename__ = "cohortes"
    __table_args__ = (
        UniqueConstraint("nombre", name="uq_cohortes_nombre"),
        UniqueConstraint("anio", "numero", name="uq_cohortes_anio_numero"),
        CheckConstraint("numero BETWEEN 1 AND 999", name="ck_cohortes_numero"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    anio: int
    numero: int
    nombre: str = Field(max_length=50)
    inscripcion_abierta: bool = False
    fecha_inicio: date | None = None
    proxima_apertura: date | None = None
    created_at: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
