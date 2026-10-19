"""
Capa de datos (Repository) — acceso a la tabla `usuarios`.

La lección del módulo 03: el repository NO sabe de HTTP ni de reglas de
negocio. Solo habla con la base. Si no encuentra, devuelve None, y el que
decide qué significa eso (401, 404, 409) es la capa de arriba.

Fijate que tampoco normaliza el email: eso es una regla ("los emails no
distinguen mayúsculas") y vive en el service. Acá se busca tal cual llega.
"""

from sqlmodel import Session, select

from app.models import Usuario


class UsuarioRepository:
    """Consultas sobre los usuarios del sistema."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Usuario | None:
        """El usuario con ese email, o None si no existe.

        `.first()` y no `.all()`: queremos UNO o ninguno (el email es único).
        """
        statement = select(Usuario).where(Usuario.email == email)
        return self.session.exec(statement).first()
