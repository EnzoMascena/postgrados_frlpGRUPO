"""
Capa de seguridad — hash de contraseñas, tokens JWT y tokens opacos.

Es el security.py de los módulos 04 y 06, con dos diferencias:

  1. El hash es bcrypt con costo 12, porque lo pide el SRS (NFR-S04). En
     clase se vio Argon2id (lo que trae PasswordHash.recommended()); la
     elección está justificada en el ADR-003 y pendiente con el profe.

  2. Hay TRES tipos de token, porque hay tres formas de entrar al sistema:
       - "usuario":   coordinador o CPR, dura 8 horas. sub = id del usuario.
                      El rol viaja como referencia, pero la autorización lo
                      relee de la base en cada request (lección del 06).
       - "aspirante": sub = id de SU legajo. Es el token de seguimiento.
       - "docente":   sub = id del acceso (el link del coordinador), con el
                      seminario_id. Lo emite el canje del link (módulo de Luca).

Estas funciones NO capturan los errores del JWT: si el token venció o fue
adulterado, jwt.decode lanza y la capa HTTP (core/dependencies.py) lo
traduce a 401. Security no sabe de HTTP (lección del módulo 04).
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import (
    ALGORITHM,
    ASPIRANTE_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    USUARIO_TOKEN_EXPIRE_MINUTES,
)

# ── Hash de contraseñas ────────────────────────────────────────────────────

# NFR-S04: bcrypt con costo 12 o más. Cada +1 duplica el tiempo de un ataque
# de fuerza bruta (y el del login: con 12, unos 0,25 s por intento).
BCRYPT_ROUNDS = 12

# bcrypt solo mira los primeros 72 bytes; bcrypt 5 directamente rechaza más.
_MAX_BYTES_BCRYPT = 72

password_hash = PasswordHash((BcryptHasher(rounds=BCRYPT_ROUNDS),))


def hash_password(password: str) -> str:
    """Convierte una contraseña en un hash irreversible (con sal aleatoria)."""
    if len(password.encode("utf-8")) > _MAX_BYTES_BCRYPT:
        raise ValueError("La contraseña no puede superar los 72 bytes")
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """¿La contraseña coincide con el hash? Devuelve True o False, nunca lanza."""
    if len(plain_password.encode("utf-8")) > _MAX_BYTES_BCRYPT:
        # Ninguna contraseña guardada puede ser tan larga: no coincide. Sin
        # este control, bcrypt lanzaría ValueError y el login daría 500.
        return False
    return password_hash.verify(plain_password, hashed_password)


# Hash "señuelo" anti timing attack (módulo 04): se calcula UNA sola vez.
# Si el email no existe, el login igual verifica contra este hash, así
# tarda lo MISMO que con una contraseña incorrecta y no delata qué emails
# están registrados.
DUMMY_HASH = hash_password("contraseña-señuelo-que-nunca-coincide")


# ── JWT ────────────────────────────────────────────────────────────────────


class TipoToken(StrEnum):
    """Las tres formas de entrar al sistema (claim "tipo" del token)."""

    USUARIO = "usuario"
    ASPIRANTE = "aspirante"
    DOCENTE = "docente"


def _firmar(claims: dict[str, Any], expira: datetime) -> str:
    """Firma el token con HS256 agregando "iat" y "exp".

    El payload está CODIFICADO (base64), no cifrado: cualquiera lo puede
    leer. Nunca va un secreto adentro, solo ids y el tipo.
    """
    payload = {**claims, "iat": datetime.now(UTC), "exp": expira}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def crear_token_usuario(usuario_id: UUID, rol: str) -> str:
    """Token del coordinador o del CPR, válido por 8 horas (sin refresh)."""
    expira = datetime.now(UTC) + timedelta(minutes=USUARIO_TOKEN_EXPIRE_MINUTES)
    return _firmar({"sub": str(usuario_id), "tipo": TipoToken.USUARIO, "rol": rol}, expira)


def crear_token_aspirante(legajo_id: UUID) -> str:
    """Token de seguimiento del aspirante: solo sirve para SU legajo."""
    expira = datetime.now(UTC) + timedelta(days=ASPIRANTE_TOKEN_EXPIRE_DAYS)
    return _firmar({"sub": str(legajo_id), "tipo": TipoToken.ASPIRANTE}, expira)


def crear_token_docente(acceso_id: UUID, seminario_id: UUID, expira_en: datetime) -> str:
    """Token del docente: solo sirve para SU seminario (ASR-002).

    Lo emite el canje del link (POST /docentes/acceso). El vencimiento lo
    elige quien canjea, sin pasar el del link.
    """
    claims = {"sub": str(acceso_id), "tipo": TipoToken.DOCENTE, "seminario_id": str(seminario_id)}
    return _firmar(claims, expira_en)


def decodificar_token(token: str) -> dict[str, Any]:
    """Decodifica y VERIFICA el token. Lanza jwt.InvalidTokenError si no vale.

    ⚠️ `algorithms=[ALGORITHM]` va EXPLÍCITO: si el algoritmo saliera del
    token, un atacante podría mandar uno con "alg": "none" (sin firma) y
    pasar. Así solo se acepta HS256.
    """
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp", "tipo"]},
    )


# ── Tokens opacos (el link del docente) ────────────────────────────────────


def generar_token_opaco() -> str:
    """Token aleatorio de 32 bytes (256 bits), seguro para usar en una URL."""
    return secrets.token_urlsafe(32)


def hash_token_opaco(token: str) -> str:
    """SHA-256 del token. En la base se guarda esto, nunca el token en claro:
    si se filtrara la base, los links no servirían."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
