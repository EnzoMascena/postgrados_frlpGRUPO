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

    def activos_con_rol(self, rol: Rol) -> list[Usuario]:
        """Los usuarios activos con ese rol, por email. Lo usa el email de VENCER (L3).

        No está en `UsuarioRepository` porque el login no lo necesita: lo usa directo la
        infraestructura de legajos, que ya sabe que hay una base.
        """
        filas = self.session.exec(
            select(UsuarioORM)
            .where(UsuarioORM.rol == rol.value, UsuarioORM.activo)
            .order_by(UsuarioORM.email)
        ).all()
        return [_a_dominio(fila) for fila in filas]


def _a_dominio(fila: UsuarioORM) -> Usuario:
    return Usuario(
        id=fila.id,
        email=fila.email,
        nombre=fila.nombre,
        rol=Rol(fila.rol),
        activo=fila.activo,
        password_hash=fila.password_hash,
    )
