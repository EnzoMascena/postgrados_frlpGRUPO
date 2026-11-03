"""Dependencias de FastAPI para proteger endpoints. Las usan todos los módulos:

    @router.get("/legajos")
    def listar(usuario: Usuario = Depends(require_role(Rol.COORDINADOR))): ...

Sin token, con un token inválido o vencido, o con un usuario que ya no existe o está inactivo → 401.
Con un rol que no corresponde → 403.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO, decodificar_token
from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.shared.database import get_session
from src.shared.errors import NoAutenticado, SinPermiso
from src.shared.roles import Actor, Rol

MENSAJE_SIN_TOKEN = "Necesitás iniciar sesión para continuar"
MENSAJE_SIN_PERMISO = "No tenés permiso para esta acción"

# Con auto_error=True, HTTPBearer responde su propio 403 en inglés y con otro formato.
# Así, si falta el header devuelve None y levantamos nuestro 401.
bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> Usuario:
    if credenciales is None:
        raise NoAutenticado(MENSAJE_SIN_TOKEN)

    claims = decodificar_token(credenciales.credentials)
    try:
        usuario_id = UUID(claims["sub"])
    except ValueError as error:
        raise NoAutenticado(MENSAJE_TOKEN_INVALIDO) from error

    # El usuario se lee de la base en cada request: si lo desactivan o le cambian el rol,
    # su token deja de servir para lo que ya no puede hacer, sin esperar las 8 horas.
    usuario = PgUsuarioRepository(session).obtener(usuario_id)
    if usuario is None or not usuario.activo:
        raise NoAutenticado(MENSAJE_TOKEN_INVALIDO)
    return usuario


def require_role(*roles: Rol) -> Callable[..., Usuario]:
    """Devuelve una dependencia que deja pasar solo a los usuarios con alguno de esos roles."""

    def dependencia(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles:
            raise SinPermiso(MENSAJE_SIN_PERMISO)
        return usuario

    return dependencia


def actor_desde_usuario(usuario: Usuario) -> Actor:
    """Quién hace la acción, para la auditoría de `ServicioEstados` (L3)."""
    return Actor(rol=usuario.rol, email=usuario.email)
