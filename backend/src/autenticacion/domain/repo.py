"""Lo que el login necesita de la base, sin decir cómo se guarda. Python puro.

La implementación con SQLModel vive en `infrastructure/pg_repository.py`; en los tests unitarios
se usa una falsa en memoria. Cualquier clase con estos dos métodos sirve (es un `Protocol`).
"""

from typing import Protocol
from uuid import UUID

from src.autenticacion.domain.usuario import Usuario


class UsuarioRepository(Protocol):
    def buscar_por_email(self, email: str) -> Usuario | None:
        """Devuelve el usuario con ese email (ya normalizado), o `None` si no existe."""
        ...

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        """Devuelve el usuario con ese id, o `None` si no existe."""
        ...
