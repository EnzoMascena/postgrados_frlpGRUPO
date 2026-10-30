"""Tabla `usuarios`: quienes entran con email y contraseña. Los aspirantes no tienen usuario."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlmodel import Field, SQLModel

from src.shared.orm import ahora_utc, columna_fecha, valores_para_check
from src.shared.roles import Rol

# El aspirante entra con un link y SISTEMA es quien corre las tareas: ninguno tiene usuario.
ROLES_CON_USUARIO = [rol for rol in Rol if rol not in (Rol.ASPIRANTE, Rol.SISTEMA)]


class UsuarioORM(SQLModel, table=True):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuarios_email"),
        CheckConstraint(
            f"rol IN ({valores_para_check(ROLES_CON_USUARIO)})", name="ck_usuarios_rol"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    rol: str = Field(max_length=30)
    activo: bool = True
    created_at: datetime = Field(
        default_factory=ahora_utc, sa_column=columna_fecha(server_default=func.now())
    )
