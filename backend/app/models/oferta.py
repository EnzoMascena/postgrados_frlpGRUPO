"""
Tablas `carreras` y `cohortes` — la oferta académica.

Las carga el seed. Dolores abre y cierra el período de inscripción de una
cohorte (BR-009); el resto de los módulos solo las lee.
"""

from datetime import date

from sqlmodel import Field

from app.models.base import TablaBase, check_enum, tipo_enum
from app.models.enums import TipoCarrera


class Carrera(TablaBase, table=True):
    """Una carrera de posgrado. El tipo define la duración y el semáforo."""

    __tablename__ = "carreras"
    __table_args__ = (check_enum("tipo", TipoCarrera),)

    nombre: str = Field(max_length=150, unique=True)
    # El nombre que muestran las tablas del front ("Esp. Ing. Sistemas").
    nombre_corto: str = Field(max_length=60)
    tipo: TipoCarrera = Field(sa_type=tipo_enum(TipoCarrera))


class Cohorte(TablaBase, table=True):
    """El grupo que empieza el mismo año (ej.: "Cohorte 2026")."""

    __tablename__ = "cohortes"

    anio: int = Field(unique=True)
    nombre: str = Field(max_length=50, unique=True)
    # Solo el coordinador la abre o la cierra (BR-009).
    inscripcion_abierta: bool = Field(default=False)
    fecha_inicio: date | None = None
