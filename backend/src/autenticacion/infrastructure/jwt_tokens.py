"""Tokens de acceso JWT (ADR-003): HS256, firmados con `JWT_SECRET`, válidos `JWT_EXPIRA_MINUTOS`.

El token lleva `sub` (id del usuario), `email`, `rol`, `iat` y `exp`. No hay refresh token: cuando
vence, el usuario vuelve a iniciar sesión.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.autenticacion.domain.usuario import Usuario
from src.shared.config import settings
from src.shared.errors import NoAutenticado

ALGORITMO = "HS256"
MENSAJE_TOKEN_INVALIDO = "Tu sesión venció o no es válida. Volvé a iniciar sesión"


def crear_token(usuario: Usuario) -> tuple[str, int]:
    """Devuelve el token y cuántos segundos es válido (lo que el front recibe como `expiraEn`)."""
    ahora = datetime.now(UTC)
    validez = timedelta(minutes=settings.jwt_expira_minutos)
    claims = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "rol": usuario.rol.value,
        "iat": ahora,
        "exp": ahora + validez,
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITMO)
    return token, int(validez.total_seconds())


def decodificar_token(token: str) -> dict[str, Any]:
    """Verifica la firma y el vencimiento y devuelve los claims, o levanta `NoAutenticado`."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            # Fijar el algoritmo evita que acepte un token con "alg": "none" u otro algoritmo.
            algorithms=[ALGORITMO],
            options={"require": ["sub", "email", "rol", "iat", "exp"]},
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as error:
        raise NoAutenticado(MENSAJE_TOKEN_INVALIDO) from error
