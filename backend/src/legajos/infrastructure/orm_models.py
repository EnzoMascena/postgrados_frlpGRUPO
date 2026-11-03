"""Tablas `legajos`, `legajo_carreras` y `auditoria_legajos`."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, Index, Text, UniqueConstraint, func
from sqlmodel import Field, SQLModel

from src.inscripcion.domain.tipos import ComoConocio, TipoBeca
from src.legajos.domain.estados import EstadoLegajo
from src.shared.orm import ahora_utc, columna_fecha, valores_para_check


class LegajoORM(SQLModel, table=True):
    __tablename__ = "legajos"
    __table_args__ = (
        # El DNI y el email son únicos dentro de una cohorte, no en todo el sistema.
        UniqueConstraint("cohorte_id", "dni", name="uq_legajos_cohorte_dni"),
        UniqueConstraint("cohorte_id", "email", name="uq_legajos_cohorte_email"),
        UniqueConstraint("codigo_seguimiento", name="uq_legajos_codigo_seguimiento"),
        UniqueConstraint("numero_legajo", name="uq_legajos_numero_legajo"),
        CheckConstraint(
            f"estado IN ({valores_para_check(EstadoLegajo)})", name="ck_legajos_estado"
        ),
        CheckConstraint(
            f"como_conocio IN ({valores_para_check(ComoConocio)})", name="ck_legajos_como_conocio"
        ),
        CheckConstraint("char_length(motivacion) >= 50", name="ck_legajos_motivacion"),
        CheckConstraint(
            f"tipo_beca IN ({valores_para_check(TipoBeca)})", name="ck_legajos_tipo_beca"
        ),
        # tipo_beca es obligatorio si solicita beca y tiene que ser nulo si no la solicita.
        CheckConstraint(
            "(solicita_beca AND tipo_beca IS NOT NULL) OR (NOT solicita_beca AND tipo_beca IS NULL)",
            name="ck_legajos_beca_coherente",
        ),
        Index("ix_legajos_dni", "dni"),
        Index("ix_legajos_email", "email"),
        Index("ix_legajos_cohorte_estado", "cohorte_id", "estado"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    cohorte_id: uuid.UUID = Field(foreign_key="cohortes.id")
    codigo_seguimiento: str = Field(max_length=8)
    numero_legajo: str | None = Field(default=None, max_length=20)
    estado: str = Field(default=EstadoLegajo.BORRADOR.value, max_length=30)

    apellido: str = Field(max_length=100)
    nombre: str = Field(max_length=100)
    nacionalidad: str = Field(max_length=100)
    dni: str = Field(max_length=20)
    telefono_movil: str = Field(max_length=30)
    telefono_fijo: str | None = Field(default=None, max_length=30)
    email: str = Field(max_length=255)
    email_alternativo: str | None = Field(default=None, max_length=255)
    domicilio: str = Field(max_length=255)
    ciudad: str = Field(max_length=100)
    provincia: str = Field(max_length=100)
    pais: str = Field(max_length=100)
    titulo_grado: str = Field(max_length=255)
    titulo_posgrado: str | None = Field(default=None, max_length=255)
    como_conocio: str = Field(max_length=30)
    motivacion: str = Field(sa_column=Column(Text, nullable=False))

    solicita_beca: bool = False
    tipo_beca: str | None = Field(default=None, max_length=10)

    fecha_inscripcion: datetime | None = Field(default=None, sa_column=columna_fecha(nullable=True))
    fecha_aprobacion: datetime | None = Field(default=None, sa_column=columna_fecha(nullable=True))
    fecha_activacion: datetime | None = Field(default=None, sa_column=columna_fecha(nullable=True))
    created_at: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=ahora_utc,
        sa_column=columna_fecha(server_default=func.now(), onupdate=func.now()),
    )


class LegajoCarreraORM(SQLModel, table=True):
    """Las carreras que eligió el aspirante: hasta dos, con `orden` 1 o 2 (BR-001, ADR-006)."""

    __tablename__ = "legajo_carreras"
    __table_args__ = (
        UniqueConstraint("legajo_id", "carrera_id", name="uq_legajo_carreras_legajo_carrera"),
        CheckConstraint("orden IN (1, 2)", name="ck_legajo_carreras_orden"),
    )

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", primary_key=True, ondelete="CASCADE")
    orden: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": False})
    carrera_id: uuid.UUID = Field(foreign_key="carreras.id")


class AuditoriaLegajoORM(SQLModel, table=True):
    """Una fila por cada cambio de estado. `usuario_email` es nulo si lo hizo el sistema."""

    __tablename__ = "auditoria_legajos"
    __table_args__ = (Index("ix_auditoria_legajos_legajo_id", "legajo_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    legajo_id: uuid.UUID = Field(foreign_key="legajos.id")
    accion: str = Field(max_length=30)
    estado_anterior: str | None = Field(default=None, max_length=30)
    estado_nuevo: str = Field(max_length=30)
    comentario: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    rol: str = Field(max_length=30)
    usuario_email: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
