"""Lo que el módulo de cohortes necesita de la base, sin decir cómo se guarda. Python puro.

La implementación con SQLModel vive en `infrastructure/pg_repository.py`; en los tests unitarios
se usa una falsa en memoria.
"""

from typing import Protocol
from uuid import UUID

from src.cohortes.domain.cohorte import Carrera, Cohorte


class CohorteRepository(Protocol):
    def listar_cohortes(self) -> list[Cohorte]:
        """Todas las cohortes, de la más nueva a la más vieja."""
        ...

    def listar_carreras_activas(self) -> list[Carrera]:
        """Las carreras activas, por nombre."""
        ...

    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        """La cohorte con ese id, o `None` si no existe."""
        ...

    def guardar_periodo(self, cohorte: Cohorte) -> None:
        """Guarda si la inscripción está abierta y la próxima apertura de una cohorte que existe."""
        ...
