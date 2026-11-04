"""Dependencias de FastAPI que arman los casos de uso de legajos. Fran usa `get_servicio_estados`
en su envío y corrección:

    @router.post("/seguimiento/{token}/enviar")
    def enviar(..., servicio: ServicioEstados = Depends(get_servicio_estados)): ...
"""

from fastapi import Depends
from sqlmodel import Session

from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.legajos.application.cambiar_estado import ServicioEstados
from src.legajos.infrastructure.email_notificador import EmailNotificadorLegajos
from src.legajos.infrastructure.pg_repository import PgLegajoRepository
from src.shared.database import get_session


def get_servicio_estados(session: Session = Depends(get_session)) -> ServicioEstados:
    """El servicio con el repositorio de la base y los emails, sobre la sesión del request."""
    repo = PgLegajoRepository(session)
    return ServicioEstados(repo, EmailNotificadorLegajos(repo, PgUsuarioRepository(session)))
