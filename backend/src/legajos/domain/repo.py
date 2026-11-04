"""Lo que `ServicioEstados` necesita de la base, sin decir cómo se guarda. Python puro.

La implementación con SQLModel (`PgLegajoRepository`) vive en `infrastructure/pg_repository.py`;
en los tests unitarios se usa una falsa en memoria. Cualquier clase con estos métodos sirve.
"""

from typing import Protocol
from uuid import UUID

from src.legajos.domain.entidades import DatosCohorte, Legajo, RegistroAuditoria


class LegajoRepository(Protocol):
    def obtener(self, legajo_id: UUID) -> Legajo | None:
        """Devuelve el legajo con ese id, o `None` si no existe."""
        ...

    def siguiente_secuencial(self, cohorte_id: UUID) -> int:
        """El secuencial del próximo número de legajo de la cohorte: el mayor ya usado más 1.

        No es la cantidad de legajos de la cohorte: así no choca con los números del seed ni con
        los de legajos que después vencieron. Bloquea la fila de la cohorte (`FOR UPDATE`) hasta
        el `commit` de `guardar_cambio`, para que dos aprobaciones a la vez no tomen el mismo.
        """
        ...

    def datos_cohorte(self, cohorte_id: UUID) -> DatosCohorte:
        """Año, número y nombre de la cohorte (para el número de legajo y los emails)."""
        ...

    def nombres_carreras(self, legajo_id: UUID) -> list[str]:
        """Los nombres de las carreras que eligió el aspirante, en su orden (1 y 2)."""
        ...

    def guardar_cambio(self, legajo: Legajo, registro: RegistroAuditoria) -> None:
        """Guarda el legajo y su fila de auditoría juntos, con un solo `commit`."""
        ...
