"""
Piezas comunes de todas las tablas.

  - Convención de nombres: índices y constraints con nombres fijos (ix_, uq_,
    ck_, fk_, pk_). Así Alembic genera siempre los mismos y una migración
    futura los puede referenciar sin adivinar.
  - TablaBase: la PK UUID y el created_at que tienen las 13 tablas.
  - tipo_enum() + check_enum(): un enum como VARCHAR (native_enum=False) y su
    CHECK con los valores permitidos, declarado en __table_args__.
  - Fechas y horas con zona horaria (timestamptz), siempre en UTC.

Este archivo se importa ANTES de definir cualquier tabla (lo hacen los
módulos de models/), porque la convención de nombres tiene que estar
puesta cuando se crean los constraints.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, func, text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def ahora_utc() -> datetime:
    """La fecha y hora actual en UTC (con zona horaria)."""
    return datetime.now(UTC)


def tipo_enum(enum: type[StrEnum]) -> SAEnum:
    """El tipo de columna para un enum: VARCHAR(40) que guarda su VALOR.

    Se guarda el valor, no el nombre: TipoCarrera.MAESTRIA queda "Maestria".
    El CHECK va aparte, con check_enum() en __table_args__: si lo creara el
    propio tipo (create_constraint=True), el autogenerate de Alembic lo
    duplica y la migración falla.
    """
    return SAEnum(
        enum,
        native_enum=False,
        create_constraint=False,
        length=40,
        values_callable=lambda miembros: [miembro.value for miembro in miembros],
    )


def check_enum(columna: str, enum: type[StrEnum]) -> CheckConstraint:
    """CHECK (columna IN (...valores...)), llamado ck_<tabla>_<columna>.

    La base rechaza cualquier valor que no sea del enum, aunque venga de un
    INSERT a mano. Si se suma un valor al enum, hay que migrar este CHECK.
    """
    valores = ", ".join("'" + miembro.value.replace("'", "''") + "'" for miembro in enum)
    return CheckConstraint(f"{columna} IN ({valores})", name=columna)


def _timestamp(*, onupdate: bool) -> Any:
    kwargs: dict[str, Any] = {"server_default": func.now()}
    if onupdate:
        kwargs["onupdate"] = ahora_utc
    return Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs=kwargs,
        nullable=False,
    )


def campo_creado() -> Any:
    """Timestamp (UTC) del momento en que se creó la fila."""
    return _timestamp(onupdate=False)


def campo_actualizado() -> Any:
    """Timestamp (UTC) que se renueva solo cada vez que se modifica la fila."""
    return _timestamp(onupdate=True)


def campo_fecha_hora_opcional() -> Any:
    """Timestamp (UTC) de un evento que puede no haber pasado todavía."""
    return Field(default=None, sa_type=DateTime(timezone=True))


class TablaBase(SQLModel):
    """Lo que tienen todas las tablas: PK UUID y fecha de creación (UTC)."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    created_at: datetime = campo_creado()
