"""
Capa de presentación (Controller) — las rutas HTTP de auth.

    POST /api/v1/auth/login → verifica credenciales y devuelve un JWT
    GET  /api/v1/auth/me    → quién soy (cualquier usuario autenticado)

El controller recibe el request, delega en el service y TRADUCE el
resultado a HTTP. No hashea, no habla con la base y no verifica
contraseñas: solo convierte `Usuario` / `None` en status codes y JSON.

Deny-by-default (módulo 06): toda ruta lleva require_role. El login es una
de las pocas excepciones, porque es justamente donde se consigue el token.
"""

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_auth_service
from app.auth.schemas import LoginRequest, PrincipalRead, TokenResponse
from app.auth.service import AuthService
from app.core.dependencies import require_role
from app.core.errores import ErrorAPI, respuestas
from app.core.principal import Principal
from app.core.security import crear_token_usuario
from app.models.enums import Rol

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión (coordinador o CPR)",
    responses=respuestas(401, 422),
)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Verifica email y contraseña y emite un token que dura 8 horas.

    El 401 tiene SIEMPRE el mismo mensaje: nunca dice "el email no existe"
    ni "la contraseña es incorrecta" por separado, porque eso le confirmaría
    a un atacante qué emails están registrados (user enumeration).
    """
    usuario = service.autenticar(body.email, body.password)
    if usuario is None:
        raise ErrorAPI(
            status.HTTP_401_UNAUTHORIZED,
            "Email o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Como en el módulo 04, el token lo arma el controller: es la "sesión"
    # HTTP. El sub es el id del usuario; el rol va como referencia, porque
    # en cada request se relee de la base (core/dependencies.py).
    return TokenResponse(access_token=crear_token_usuario(usuario.id, usuario.rol))


@router.get(
    "/me",
    response_model=PrincipalRead,
    summary="Quién soy",
    responses=respuestas(401),
)
def me(principal: Principal = Depends(require_role(*Rol))):
    """Devuelve el usuario, aspirante o docente dueño del token.

    No recibe ningún id por la URL: el "quién" sale del TOKEN. El front lo
    usa al recargar la página para recuperar la sesión y armar el menú.
    """
    return PrincipalRead.model_validate(principal)
