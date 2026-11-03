"""`UsuarioRepository` con SQLModel: lee la tabla `usuarios` y devuelve el `Usuario` del dominio."""

from uuid import UUID

from sqlmodel import Session, select

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.shared.roles import Rol


class PgUsuarioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar_por_email(self, email: str) -> Usuario | None:
        # El caso de uso ya pasó el email a minúsculas, y en la tabla se guarda así.
        fila = self.session.exec(select(UsuarioORM).where(UsuarioORM.email == email)).first()
        return _a_dominio(fila) if fila else None

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        fila = self.session.get(UsuarioORM, usuario_id)
        return _a_dominio(fila) if fila else None


def _a_dominio(fila: UsuarioORM) -> Usuario:
    return Usuario(
        id=fila.id,
        email=fila.email,
        nombre=fila.nombre,
        rol=Rol(fila.rol),
        activo=fila.activo,
        password_hash=fila.password_hash,
    )
