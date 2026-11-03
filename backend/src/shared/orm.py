"""Ayudas para escribir los modelos ORM de todos los módulos."""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def columna_fecha(nullable: bool = False, **opciones: Any) -> Column:
    """Una fecha con zona horaria: se guarda en UTC (`timestamptz`)."""
    return Column(DateTime(timezone=True), nullable=nullable, **opciones)


def valores_para_check(valores: Iterable[str]) -> str:
    """La lista de un `CHECK (columna IN (...))`, armada desde un enum.

    Así los valores permitidos se escriben una sola vez, en el enum del dominio.
    """
    return ", ".join(f"'{valor}'" for valor in valores)
