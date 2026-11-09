"""Caso de uso: vencer las reservas de vacante cumplidas (US-CORE-010, BR-005).

De los legajos COMPLETADO, pasa a VENCIDO los que ya tienen 30 días o más desde `fecha_aprobacion`.
La regla es la de Luca (`reserva_vencida`) y el cambio pasa por `ServicioEstados`, como cualquier
otro: así queda la auditoría (rol SISTEMA, sin email de usuario) y cada coordinador activo recibe
el aviso. Lo corren la tarea diaria y el comando manual (`infrastructure/job_vencimiento.py`).
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple
from uuid import UUID

from src.legajos.application.cambiar_estado import ServicioEstados
from src.legajos.domain.entidades import Legajo
from src.legajos.domain.estados import Accion, TransicionInvalida
from src.legajos.domain.vencimiento import reserva_vencida
from src.shared.errors import NoEncontrado
from src.shared.roles import Actor, Rol

logger = logging.getLogger(__name__)

SISTEMA = Actor(Rol.SISTEMA)


class ReservaAprobada(NamedTuple):
    """Un legajo COMPLETADO y desde cuándo tiene la vacante reservada."""

    legajo_id: UUID
    fecha_aprobacion: datetime


@dataclass(frozen=True)
class ResultadoVencimiento:
    revisadas: int  # los COMPLETADO que se miraron
    vencidos: list[Legajo]  # los que pasaron a VENCIDO, con su número de legajo


def vencer_reservas(
    reservas: list[ReservaAprobada], servicio: ServicioEstados, ahora: datetime
) -> ResultadoVencimiento:
    """Vence las reservas cumplidas a `ahora` (con zona horaria) y devuelve qué pasó.

    Es idempotente: un legajo vencido deja de ser COMPLETADO y la próxima corrida ya no lo trae.
    Si un legajo cambió de estado entre la consulta y el cambio (por ejemplo, lo matricularon), se
    saltea y se sigue con los demás. Cualquier otro error corta la corrida: los legajos ya vencidos
    quedan guardados (cada cambio tiene su commit) y el resto lo toma la corrida siguiente.
    """
    vencidos = []
    for reserva in reservas:
        if not reserva_vencida(reserva.fecha_aprobacion, ahora):
            continue
        try:
            vencidos.append(servicio.cambiar(reserva.legajo_id, Accion.VENCER, SISTEMA))
        except (TransicionInvalida, NoEncontrado) as error:
            logger.warning("No se venció el legajo %s: %s", reserva.legajo_id, error)
    return ResultadoVencimiento(revisadas=len(reservas), vencidos=vencidos)
