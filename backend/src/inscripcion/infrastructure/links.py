"""Links de seguimiento del aspirante (ADR-005).

El token es aleatorio (32 bytes) y en la base se guarda solo su SHA-256: si alguien lee la tabla,
no puede armar ningún link. Por eso cada email de link genera un token nuevo.
"""

import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from sqlmodel import Session, select

from src.inscripcion.infrastructure.orm_models import TokenSeguimientoORM
from src.shared.config import settings
from src.shared.orm import ahora_utc


def hashear_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def crear_link_seguimiento(session: Session, legajo_id: UUID) -> str:
    """Crea un token nuevo para el legajo y lo devuelve en claro, la única vez que existe así."""
    token = secrets.token_urlsafe(32)
    session.add(
        TokenSeguimientoORM(
            legajo_id=legajo_id,
            token_hash=hashear_token(token),
            expira_en=ahora_utc() + timedelta(days=settings.token_seguimiento_dias),
        )
    )
    session.commit()
    return token


def link_de(token: str) -> str:
    """La URL que va en el email: la pantalla de seguimiento del front."""
    return f"{settings.frontend_url}/seguimiento/{token}"


def buscar_legajo_por_token(session: Session, token: str) -> UUID | None:
    """El legajo del token, o `None` si el token no existe o ya venció."""
    consulta = select(TokenSeguimientoORM).where(
        TokenSeguimientoORM.token_hash == hashear_token(token)
    )
    fila = session.exec(consulta).first()
    if fila is None or fila.expira_en <= ahora_utc():
        return None
    return fila.legajo_id
