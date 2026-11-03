"""Lo que la inscripción necesita de la base, sin decir cómo se guarda. Python puro.

La implementación con SQLModel vive en `infrastructure/pg_repository.py`; en los tests unitarios
se usa una falsa en memoria.
"""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.cohortes.domain.cohorte import Cohorte
from src.inscripcion.domain.inscripcion import DatosInscripcion, LegajoDelAspirante


class InscripcionRepository(Protocol):
    def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte | None:
        """La cohorte con ese id, o `None` si no existe."""
        ...

    def carreras_activas(self, carrera_ids: Sequence[UUID]) -> set[UUID]:
        """De esos ids, los de las carreras que existen y están activas."""
        ...

    def existe_dni(self, cohorte_id: UUID, dni: str) -> bool: ...

    def existe_email(self, cohorte_id: UUID, email: str) -> bool: ...

    def crear_legajo(self, datos: DatosInscripcion, codigo_seguimiento: str) -> UUID:
        """Guarda el legajo en BORRADOR con sus carreras y devuelve su id.

        Si otro pedido guardó el mismo DNI o email en el medio, levanta `Conflicto`.
        """
        ...

    def buscar_ultimo_por_email(self, email: str) -> LegajoDelAspirante | None:
        """El legajo más reciente con ese email, de cualquier cohorte, o `None`."""
        ...
