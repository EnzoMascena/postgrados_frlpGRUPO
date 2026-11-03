"""El usuario que inicia sesión (coordinador, docente, CPR o admin). Python puro."""

from dataclasses import dataclass
from uuid import UUID

from src.shared.roles import Rol


@dataclass(frozen=True)
class Usuario:
    id: UUID
    email: str
    nombre: str
    rol: Rol
    activo: bool
    # Nunca la contraseña en texto plano: solo el hash de bcrypt.
    password_hash: str
