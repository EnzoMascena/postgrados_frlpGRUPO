"""Endpoints de autenticación: `POST /auth/login` (público) y `GET /auth/me` (coordinador)."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.autenticacion.application.iniciar_sesion import MENSAJE_LOGIN_INCORRECTO, iniciar_sesion
from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.hashing import verificar_password
from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO, crear_token
from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.autenticacion.presentation.dependencies import MENSAJE_SIN_PERMISO, require_role
from src.autenticacion.presentation.schemas import LoginRequest, LoginResponse, UsuarioResponse
from src.shared.database import get_session
from src.shared.roles import Rol

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _error(status: int, codigo: str, mensaje: str, campo: str | None = None) -> dict[str, Any]:
    """Un error de ejemplo para Swagger, con el formato de ARQUITECTURA §11.2."""
    ejemplo = {
        "statusCode": status,
        "error": codigo,
        "message": mensaje,
        "field": campo,
        "timestamp": "2026-11-01T14:20:00Z",
    }
    return {"content": {"application/json": {"example": ejemplo}}}


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión",
    description=(
        "Público. Recibe email y contraseña y devuelve un JWT válido por 8 horas (`expiraEn`, "
        "en segundos) junto con el usuario. El token va en `Authorization: Bearer <accessToken>` "
        "en los endpoints protegidos. Email inexistente, contraseña incorrecta o usuario inactivo "
        "responden el mismo 401, para no revelar cuál de los tres falló."
    ),
    responses={
        401: {
            "description": "Email o contraseña incorrectos",
            **_error(401, "UNAUTHORIZED", MENSAJE_LOGIN_INCORRECTO),
        },
        422: {
            "description": "Falta el email o la contraseña, o son demasiado largos",
            **_error(422, "VALIDATION_ERROR", "El campo password es obligatorio", "password"),
        },
    },
)
def login(datos: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    sesion = iniciar_sesion(
        datos.email, datos.password, PgUsuarioRepository(session), verificar_password, crear_token
    )
    return LoginResponse.model_validate(sesion)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Usuario de la sesión",
    description=(
        "Coordinador. Devuelve el usuario dueño del token. El front lo usa al recargar la página "
        "para saber si la sesión guardada sigue sirviendo."
    ),
    responses={
        401: {
            "description": "Sin token, con un token inválido o vencido, o con un usuario inactivo",
            **_error(401, "UNAUTHORIZED", MENSAJE_TOKEN_INVALIDO),
        },
        403: {
            "description": "El usuario no es coordinador",
            **_error(403, "FORBIDDEN", MENSAJE_SIN_PERMISO),
        },
    },
)
def me(usuario: Usuario = Depends(require_role(Rol.COORDINADOR))) -> UsuarioResponse:
    return UsuarioResponse.model_validate(usuario)
