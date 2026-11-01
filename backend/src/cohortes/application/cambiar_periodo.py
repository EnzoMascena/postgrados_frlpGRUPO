"""Caso de uso: el coordinador abre o cierra la inscripción de una cohorte (US-CORE-009, BR-009).

Que sea coordinador lo controla el router con `require_role`. Acá llegan el repositorio y la
fecha de hoy por parámetro: no sabe nada de la base ni del reloj, y se testea con piezas falsas.
"""

from datetime import date
from uuid import UUID

from src.cohortes.domain.cohorte import Cohorte, cambiar_periodo
from src.cohortes.domain.repo import CohorteRepository
from src.shared.errors import NoEncontrado

MENSAJE_COHORTE_INEXISTENTE = "La cohorte no existe"


def cambiar_periodo_de_inscripcion(
    cohorte_id: UUID,
    abierta: bool,
    proxima_apertura: date | None,
    repo: CohorteRepository,
    hoy: date,
) -> Cohorte:
    cohorte = repo.obtener_cohorte(cohorte_id)
    if cohorte is None:
        raise NoEncontrado(MENSAJE_COHORTE_INEXISTENTE)

    cambiada = cambiar_periodo(cohorte, abierta, proxima_apertura, hoy)
    repo.guardar_periodo(cambiada)
    return cambiada
