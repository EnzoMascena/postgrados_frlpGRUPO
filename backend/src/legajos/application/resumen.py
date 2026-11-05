"""Caso de uso: los conteos de las tarjetas del dashboard (US-CORE-007, `GET /legajos/resumen`).

El repositorio devuelve solo los grupos que tienen legajos (un `GROUP BY` no inventa ceros);
acá se completan los 10 estados para que el front no tenga que adivinar qué falta.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.inscripcion.domain.tipos import TipoBeca
from src.legajos.domain.estados import EstadoLegajo


class ResumenRepository(Protocol):
    def contar_por_estado(self, cohorte_id: UUID | None) -> dict[EstadoLegajo, int]:
        """Cuántos legajos hay en cada estado (de la cohorte, o de todas si es `None`)."""
        ...

    def contar_por_beca(self, cohorte_id: UUID | None) -> dict[TipoBeca, int]:
        """Cuántos legajos pidieron cada tipo de beca (de la cohorte, o de todas)."""
        ...


@dataclass(frozen=True)
class ResumenLegajos:
    total: int
    por_estado: dict[EstadoLegajo, int]
    con_beca: int
    beca30: int
    beca100: int


def obtener_resumen(cohorte_id: UUID | None, repo: ResumenRepository) -> ResumenLegajos:
    """Cuenta todos los legajos, también los borradores, igual que el ejemplo del plan §10.

    `con_beca` es la suma de los dos tipos: la base garantiza que quien pide beca tiene tipo
    (`ck_legajos_beca_coherente`), así que no hace falta una tercera consulta.
    """
    contados = repo.contar_por_estado(cohorte_id)
    por_estado = {estado: contados.get(estado, 0) for estado in EstadoLegajo}
    por_beca = repo.contar_por_beca(cohorte_id)
    beca30 = por_beca.get(TipoBeca.TREINTA, 0)
    beca100 = por_beca.get(TipoBeca.CIEN, 0)
    return ResumenLegajos(
        total=sum(por_estado.values()),
        por_estado=por_estado,
        con_beca=beca30 + beca100,
        beca30=beca30,
        beca100=beca100,
    )
