"""Cohortes, carreras y la regla del período de inscripción (US-CORE-009). Python puro."""

from dataclasses import dataclass, replace
from datetime import date
from uuid import UUID

from src.cohortes.domain.tipos import TipoCarrera
from src.shared.errors import ErrorDeValidacion


@dataclass(frozen=True)
class Carrera:
    id: UUID
    nombre: str
    tipo: TipoCarrera


@dataclass(frozen=True)
class Cohorte:
    id: UUID
    anio: int
    numero: int
    nombre: str
    inscripcion_abierta: bool
    fecha_inicio: date | None
    proxima_apertura: date | None


def cambiar_periodo(
    cohorte: Cohorte, abierta: bool, proxima_apertura: date | None, hoy: date
) -> Cohorte:
    """Abre o cierra la inscripción de la cohorte y devuelve la cohorte ya cambiada.

    Abierta no lleva próxima apertura. Cerrada puede llevar una, de hoy en adelante.
    """
    if abierta:
        return replace(cohorte, inscripcion_abierta=True, proxima_apertura=None)
    if proxima_apertura is not None and proxima_apertura < hoy:
        raise ErrorDeValidacion(
            "La próxima apertura no puede ser una fecha pasada", campo="proximaApertura"
        )
    return replace(cohorte, inscripcion_abierta=False, proxima_apertura=proxima_apertura)
