"""Dependencia de las rutas del aspirante (`/seguimiento/{token}`, F5 y F6)."""

from uuid import UUID

from fastapi import Depends
from sqlmodel import Session

from src.inscripcion.infrastructure.links import buscar_legajo_por_token
from src.shared.database import get_session
from src.shared.errors import NoEncontrado

MENSAJE_LINK_INVALIDO = "El link no es válido o venció. Pedí uno nuevo con tu email"


def legajo_id_desde_token(token: str, session: Session = Depends(get_session)) -> UUID:
    """El legajo dueño del link. Uno inexistente o vencido da el mismo 404: no se distingue."""
    legajo_id = buscar_legajo_por_token(session, token)
    if legajo_id is None:
        raise NoEncontrado(MENSAJE_LINK_INVALIDO)
    return legajo_id
