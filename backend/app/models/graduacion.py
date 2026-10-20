"""
Tablas `trabajos_finales` y `tutorias` — el seguimiento hacia la graduación.

Las escribe el legajo académico (Gero). Solo el CPR crea o modifica el
trabajo final (BR-004); las tutorías las registra el coordinador.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Text
from sqlmodel import Field

from app.models.base import TablaBase, campo_actualizado, check_enum, tipo_enum
from app.models.enums import TipoTrabajoFinal


class TrabajoFinal(TablaBase, table=True):
    """El TFI o la tesis de un legajo (RF-GRAD-001). Uno por legajo."""

    __tablename__ = "trabajos_finales"
    __table_args__ = (check_enum("tipo", TipoTrabajoFinal),)

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", unique=True)
    tipo: TipoTrabajoFinal = Field(
        default=TipoTrabajoFinal.TFI, sa_type=tipo_enum(TipoTrabajoFinal)
    )
    titulo: str = Field(max_length=255)
    director: str | None = Field(default=None, max_length=150)
    codirector: str | None = Field(default=None, max_length=150)
    fecha_aprobacion_cpr: date | None = None
    numero_resolucion: str | None = Field(default=None, max_length=50)
    updated_at: datetime = campo_actualizado()


class Tutoria(TablaBase, table=True):
    """Una reunión de seguimiento con el director del trabajo final."""

    __tablename__ = "tutorias"

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", index=True)
    fecha: date
    titulo: str = Field(max_length=150)
    detalle: str = Field(sa_type=Text)
