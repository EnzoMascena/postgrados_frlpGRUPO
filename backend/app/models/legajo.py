"""
Tablas `legajos`, `documentos` y `auditoria_legajos` — el corazón del sistema.

Quién escribe cada una (PLAN_BACKEND, "Modelo de datos"):
  - legajos: Enzo (alta y borrador), Dolores (estado y número), Gero (semáforo).
  - documentos: Enzo (upload de PDFs).
  - auditoria_legajos: Dolores, y Enzo al enviar.

Un legajo por aspirante y cohorte: el DNI y el email se repiten entre
cohortes, pero no dentro de la misma. La segunda carrera opcional va en
el mismo legajo (BR-001: como máximo 2 carreras en el período).

Los datos del formulario admiten null porque el BORRADOR se guarda a medio
completar. Que estén completos al enviar es una regla de negocio, y vive en
el service (inscripcion), no en la tabla.
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, Text, UniqueConstraint, text
from sqlmodel import Field

from app.models.base import (
    TablaBase,
    campo_actualizado,
    campo_creado,
    campo_fecha_hora_opcional,
    check_enum,
    tipo_enum,
)
from app.models.enums import ComoConocio, EstadoLegajo, Semaforo, TipoBeca, TipoDocumento


class Legajo(TablaBase, table=True):
    """Datos personales, estado del workflow y semáforo de un aspirante."""

    __tablename__ = "legajos"
    __table_args__ = (
        # "Ya existe una preinscripción con este DNI para la cohorte actual".
        UniqueConstraint("cohorte_id", "dni"),
        UniqueConstraint("cohorte_id", "email"),
        # Índices de ARQUITECTURA §8.1 para las búsquedas del Dashboard (NFR-P03).
        Index("ix_legajos_cohorte_id_estado", "cohorte_id", "estado"),
        Index("ix_legajos_semaforo_rojo", "semaforo", postgresql_where=text("semaforo = 'ROJO'")),
        check_enum("estado", EstadoLegajo),
        check_enum("como_conocio", ComoConocio),
        check_enum("tipo_beca", TipoBeca),
        check_enum("semaforo", Semaforo),
    )

    cohorte_id: uuid.UUID = Field(foreign_key="cohortes.id")
    carrera_id: uuid.UUID | None = Field(default=None, foreign_key="carreras.id")
    carrera_secundaria_id: uuid.UUID | None = Field(default=None, foreign_key="carreras.id")

    estado: EstadoLegajo = Field(default=EstadoLegajo.BORRADOR, sa_type=tipo_enum(EstadoLegajo))
    # Se asigna al enviar (BORRADOR → PENDIENTE).
    numero_seguimiento: str | None = Field(default=None, max_length=20, unique=True)
    # Se asigna al aprobar, con formato AÑO-COHORTE-SECUENCIAL: "26-001-045".
    numero_legajo: str | None = Field(default=None, max_length=20, unique=True)

    # ── Datos del formulario (RF-CORE-001) ─────────────────────────────────
    apellido: str | None = Field(default=None, max_length=100)
    nombre: str | None = Field(default=None, max_length=100)
    nacionalidad: str | None = Field(default=None, max_length=60)
    # DNI o pasaporte, sin puntos.
    dni: str = Field(max_length=20, index=True)
    telefono_movil: str | None = Field(default=None, max_length=30)
    telefono_fijo: str | None = Field(default=None, max_length=30)
    email: str = Field(max_length=255, index=True)
    email_alternativo: str | None = Field(default=None, max_length=255)
    domicilio: str | None = Field(default=None, max_length=150)
    ciudad: str | None = Field(default=None, max_length=100)
    provincia: str | None = Field(default=None, max_length=100)
    pais: str | None = Field(default=None, max_length=100)
    titulo_grado: str | None = Field(default=None, max_length=150)
    titulo_posgrado: str | None = Field(default=None, max_length=150)
    como_conocio: ComoConocio | None = Field(default=None, sa_type=tipo_enum(ComoConocio))
    motivacion: str | None = Field(default=None, sa_type=Text)
    solicita_beca: bool = Field(default=False)
    tipo_beca: TipoBeca | None = Field(default=None, sa_type=tipo_enum(TipoBeca))

    # ── Semáforo (RF-GRAD-002): lo calcula el server y se guarda (ASR-003) ──
    semaforo: Semaforo = Field(default=Semaforo.VERDE, sa_type=tipo_enum(Semaforo))
    # True = el coordinador puso VERDE a mano; el recálculo no lo pisa (BR-008).
    semaforo_manual: bool = Field(default=False)

    # ── Fechas del workflow (UTC) ──────────────────────────────────────────
    # Cuándo se envió la inscripción (BORRADOR → PENDIENTE).
    fecha_inscripcion: datetime | None = campo_fecha_hora_opcional()
    # Cuándo pasó a COMPLETADO: la reserva vence a los 30 días (BR-005).
    fecha_completado: datetime | None = campo_fecha_hora_opcional()
    # Cuándo pasó a ACTIVO (matriculado).
    fecha_activacion: datetime | None = campo_fecha_hora_opcional()

    updated_at: datetime = campo_actualizado()


class Documento(TablaBase, table=True):
    """Un PDF del legajo. El archivo está en disco con nombre UUID (ASR-001)."""

    __tablename__ = "documentos"
    __table_args__ = (
        # Una caja por documento: subir de nuevo reemplaza al anterior.
        UniqueConstraint("legajo_id", "tipo"),
        check_enum("tipo", TipoDocumento),
    )

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", ondelete="CASCADE", index=True)
    tipo: TipoDocumento = Field(sa_type=tipo_enum(TipoDocumento))
    # El nombre original solo se guarda para mostrarlo; en disco es un UUID.
    nombre_original: str = Field(max_length=255)
    # Ruta RELATIVA a STORAGE_PATH. Interna: nunca sale por la API.
    path_storage: str = Field(max_length=500)
    checksum_sha256: str = Field(max_length=64)
    tamanio_bytes: int
    # Si se vuelve a subir, el service la actualiza junto con el archivo.
    fecha_subida: datetime = campo_creado()


class AuditoriaLegajo(TablaBase, table=True):
    """Quién hizo qué sobre un legajo y cuándo (created_at).

    Cada cambio de estado deja una fila. También se registran los intentos
    denegados que no cambian el estado (US-C-001): por eso `accion` dice qué
    pasó y los estados pueden quedar en null.
    """

    __tablename__ = "auditoria_legajos"
    __table_args__ = (
        check_enum("estado_anterior", EstadoLegajo),
        check_enum("estado_nuevo", EstadoLegajo),
    )

    legajo_id: uuid.UUID = Field(foreign_key="legajos.id", index=True)
    # Para un cambio de estado, la acción de RF-CORE-003 (AccionLegajo).
    accion: str = Field(max_length=40)
    estado_anterior: EstadoLegajo | None = Field(default=None, sa_type=tipo_enum(EstadoLegajo))
    estado_nuevo: EstadoLegajo | None = Field(default=None, sa_type=tipo_enum(EstadoLegajo))
    comentario: str | None = Field(default=None, sa_type=Text)
    # None = lo hizo el sistema (por ejemplo, el job de vencimiento).
    usuario_email: str | None = Field(default=None, max_length=255)
