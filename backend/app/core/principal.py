"""
Principal — QUIÉN hace el request, ya autenticado.

Hay tres formas de entrar al sistema y las tres terminan en un Principal:

  - USUARIO (coordinador o CPR): email y contraseña → token de 8 horas.
  - ASPIRANTE: su token de seguimiento, atado a SU legajo.
  - DOCENTE: el link del coordinador, canjeado por un token atado a SU
    seminario.

get_current_principal (core/dependencies.py) lo arma a partir del token, y
require_role decide si puede usar la ruta.

Es Python puro, sin FastAPI: un service lo puede recibir para decidir sobre
un recurso puntual (por ejemplo, si el aspirante es dueño del documento que
pide) sin enterarse de que existe HTTP.
"""

from dataclasses import dataclass
from uuid import UUID

from app.core.security import TipoToken
from app.models.enums import Rol


@dataclass(frozen=True)
class Principal:
    """El que hace el request. Según el tipo, viene con unos ids u otros."""

    tipo: TipoToken
    rol: Rol
    email: str | None = None
    nombre: str | None = None
    # Solo USUARIO: el id en la tabla usuarios.
    usuario_id: UUID | None = None
    # Solo ASPIRANTE: el único legajo que puede tocar.
    legajo_id: UUID | None = None
    # Solo DOCENTE: el único seminario que puede tocar, y el link que usó.
    seminario_id: UUID | None = None
    acceso_id: UUID | None = None
