"""
Inyección de dependencias — el "cableado" entre capas del módulo auth.

Igual que el dependencies.py del módulo 03: le decimos a FastAPI cómo
construir cada pieza cuando un endpoint la pide.

    Controller ──► Service ──► Repository ──► Session ──► PostgreSQL

    get_session            → una Session por request (core/database.py)
    get_usuario_repository → recibe la Session, devuelve el repository
    get_auth_service       → recibe el repository, devuelve el service

La regla de oro: cada capa recibe lo que necesita DESDE AFUERA, nunca lo
construye por su cuenta (Inversión de Control). Por eso en los tests se
puede cambiar la Session por la de la base de test sin tocar nada más.

La autenticación de las rutas (get_current_principal, require_role) no
está acá: es de todos los módulos y vive en core/dependencies.py.
"""

from fastapi import Depends
from sqlmodel import Session

from app.auth.repository import UsuarioRepository
from app.auth.service import AuthService
from app.core.database import get_session


def get_usuario_repository(session: Session = Depends(get_session)) -> UsuarioRepository:
    """Construye el repository con la Session del request."""
    return UsuarioRepository(session)


def get_auth_service(
    repository: UsuarioRepository = Depends(get_usuario_repository),
) -> AuthService:
    """Construye el service con su repository."""
    return AuthService(repository)
