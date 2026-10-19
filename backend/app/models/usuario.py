"""
Tabla `usuarios` — quienes entran con email y contraseña.

Solo el coordinador y el CPR tienen usuario (RolUsuario). El docente entra
con el link del coordinador y el aspirante con su token de seguimiento.

La lección del módulo 04: no existe una columna `password`. Se guarda el
hash (bcrypt, costo 12) y el texto plano nunca llega a la base.
"""

from sqlmodel import Field

from app.models.base import TablaBase, check_enum, tipo_enum
from app.models.enums import RolUsuario


class Usuario(TablaBase, table=True):
    """Coordinador o CPR. El rol se relee de acá en cada request (módulo 06)."""

    __tablename__ = "usuarios"
    __table_args__ = (check_enum("rol", RolUsuario),)

    # Se guarda normalizado (minúsculas, sin espacios): el login también normaliza.
    email: str = Field(max_length=255, unique=True, index=True)
    nombre: str = Field(max_length=120)
    password_hash: str = Field(max_length=255)
    rol: RolUsuario = Field(sa_type=tipo_enum(RolUsuario))
    # Un usuario inactivo no puede entrar, aunque su token todavía no venza.
    activo: bool = Field(default=True)
