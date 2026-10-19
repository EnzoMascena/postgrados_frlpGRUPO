"""
Tablas `seminarios`, `cursadas`, `clases`, `asistencias` y `accesos_docente`.

Las escribe la planilla docente (Luca), salvo `seminarios`, que la carga el
seed. Gero y Fran las leen para el legajo académico y las estadísticas.

    seminario ──< clase ──< asistencia >── cursada >── legajo
        └──< acceso_docente (el link que genera el coordinador)

Una CURSADA es un estudiante (legajo) en un seminario: ahí van su nota
final y su condición (BR-003). Una ASISTENCIA es esa cursada en una clase.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, UniqueConstraint
from sqlmodel import Field

from app.models.base import TablaBase, check_enum, tipo_enum
from app.models.enums import CondicionCursada


class Seminario(TablaBase, table=True):
    """Una asignatura del posgrado, de una carrera y una cohorte."""

    __tablename__ = "seminarios"

    cohorte_id: uuid.UUID = Field(foreign_key="cohortes.id", index=True)
    carrera_id: uuid.UUID = Field(foreign_key="carreras.id", index=True)
    nombre: str = Field(max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    horas_catedra: int | None = None
    # El semáforo cuenta los obligatorios que adeuda (RF-GRAD-002).
    es_obligatorio: bool = Field(default=True)
    docente_nombre: str = Field(max_length=120)
    docente_email: str | None = Field(default=None, max_length=255)
    # Porcentaje mínimo para no quedar libre (BR-003).
    asistencia_minima: int = Field(default=75)
    # Fecha límite para cargar las notas: de acá salen el vencimiento del
    # Legajo y el recordatorio al docente (RF-DOC-004).
    fecha_limite_actas: date | None = None


class Cursada(TablaBase, table=True):
    """Un estudiante en un seminario: su nota final y su condición."""

    __tablename__ = "cursadas"
    __table_args__ = (
        UniqueConstraint("legajo_id", "seminario_id"),
        # RF-DOC-003: de 1 a 10. El decimal lo limita el tipo NUMERIC(3,1), que
        # REDONDEA: "7.55" se valida antes, en el service (lo rechaza).
        CheckConstraint("nota >= 1 AND nota <= 10", name="nota_rango"),
        check_enum("condicion", CondicionCursada),
    )

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id")
    seminario_id: uuid.UUID = Field(foreign_key="seminarios.id", index=True)
    nota: Decimal | None = Field(default=None, max_digits=3, decimal_places=1)
    condicion: CondicionCursada | None = Field(default=None, sa_type=tipo_enum(CondicionCursada))
    fecha_acta: date | None = None


class Clase(TablaBase, table=True):
    """Una fecha de cursada. Está "dictada" si la fecha ya pasó (BR-002)."""

    __tablename__ = "clases"
    __table_args__ = (UniqueConstraint("seminario_id", "fecha"),)

    seminario_id: uuid.UUID = Field(foreign_key="seminarios.id")
    fecha: date


class Asistencia(TablaBase, table=True):
    """La asistencia de una cursada a una clase. Arranca en Ausente (RF-DOC-002)."""

    __tablename__ = "asistencias"
    __table_args__ = (UniqueConstraint("clase_id", "cursada_id"),)

    clase_id: uuid.UUID = Field(foreign_key="clases.id", ondelete="CASCADE")
    cursada_id: uuid.UUID = Field(foreign_key="cursadas.id", index=True)
    presente: bool = Field(default=False)


class AccesoDocente(TablaBase, table=True):
    """El link de acceso del docente a SU seminario (ASR-002).

    El token del link no se guarda: se guarda su SHA-256. Si se filtrara la
    base, los links no servirían.
    """

    __tablename__ = "accesos_docente"

    seminario_id: uuid.UUID = Field(foreign_key="seminarios.id", index=True)
    token_hash: str = Field(max_length=64, unique=True)
    expira_en: datetime = Field(sa_type=DateTime(timezone=True))
    # Email del coordinador que generó el link.
    creado_por: str | None = Field(default=None, max_length=255)
