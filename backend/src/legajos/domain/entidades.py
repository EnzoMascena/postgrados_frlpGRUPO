"""El legajo y su registro de auditoría, tal como los ve `ServicioEstados` (US-CORE-005). Python puro.

`Legajo` trae solo lo que necesitan las transiciones y los emails, no las 30 columnas de la tabla:
el detalle completo lo arma `obtener_detalle` (L3) leyendo la base. El repositorio convierte la
fila de `legajos` en este objeto y lo vuelve a guardar después del cambio.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple
from uuid import UUID

from src.legajos.domain.estados import Accion, EstadoLegajo
from src.shared.roles import Rol


@dataclass
class Legajo:
    """No es `frozen`: `ServicioEstados.cambiar` le cambia el estado y las fechas antes de guardarlo."""

    id: UUID
    cohorte_id: UUID
    estado: EstadoLegajo
    numero_legajo: str | None
    codigo_seguimiento: str
    nombre: str
    apellido: str
    email: str
    fecha_inscripcion: datetime | None = None
    fecha_aprobacion: datetime | None = None
    fecha_activacion: datetime | None = None


@dataclass(frozen=True)
class RegistroAuditoria:
    """Una fila de `auditoria_legajos`: quién hizo qué acción, cuándo y de qué estado a cuál.

    `usuario_email` es `None` cuando la acción la hizo el sistema (VENCER) o el aspirante, que no
    tiene usuario: en esos casos queda solo el `rol`.
    """

    legajo_id: UUID
    accion: Accion
    estado_anterior: EstadoLegajo
    estado_nuevo: EstadoLegajo
    comentario: str | None
    rol: Rol
    usuario_email: str | None
    fecha: datetime


class DatosCohorte(NamedTuple):
    """Lo que hace falta de la cohorte para el número de legajo y los emails."""

    anio: int
    numero: int
    nombre: str
