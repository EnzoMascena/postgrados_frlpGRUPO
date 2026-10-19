"""
Dependencias de AUTENTICACIÓN y AUTORIZACIÓN — protegen TODAS las rutas.

Es el dependencies.py del módulo 06, extendido a nuestros tres tipos de
token:

  1. get_current_principal → AUTENTICACIÓN: ¿quién sos?
       Decodifica el token y carga desde la base al usuario, al legajo del
       aspirante o al acceso del docente. Token ausente, inválido, vencido
       o que apunta a algo que ya no existe → 401.
       El rol del usuario se relee de la base en CADA request (lección del
       06): si un coordinador deja de serlo, el cambio vale ya, no cuando
       venza el token.

  2. require_role(*roles) → AUTORIZACIÓN por rol.
       Autenticado pero sin el rol → 403. Es el deny-by-default: TODA ruta
       lo lleva, salvo el login, el health y las públicas de inscripción.

  3. require_legajo_propio / require_seminario_propio → AUTORIZACIÓN sobre
       el objeto (el IDOR del módulo 06): un aspirante solo toca SU legajo y
       un docente solo SU seminario (ASR-002). Se chequea UNA vez, acá, y no
       en cada endpoint.

    Uso en un controller:
        @router.get("/legajos/{legajo_id}/borrador")
        def ver_borrador(
            legajo_id: UUID,
            principal: Principal = Depends(require_legajo_propio(Rol.ASPIRANTE)),
            service: InscripcionService = Depends(get_inscripcion_service),
        ): ...

401 o 403 (pregunta típica de la defensa):
  - 401 Unauthorized: no sabemos quién sos (sin token o token inválido).
  - 403 Forbidden: sabemos quién sos, pero no podés hacer esto.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlmodel import Session

from app.core.database import get_session
from app.core.errores import ErrorAPI
from app.core.principal import Principal
from app.core.security import TipoToken, decodificar_token
from app.models import AccesoDocente, Legajo, Seminario, Usuario
from app.models.enums import Rol

# auto_error=False: si falta el header respondemos NUESTRO 401 (con el formato
# §11.2), en vez del 403 que FastAPI devuelve por defecto.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="El token de /auth/login, del link de seguimiento o del acceso docente.",
)


def _no_autenticado() -> ErrorAPI:
    # Una sola respuesta para todos los casos: token mal firmado, vencido o
    # de algo que ya no existe. Diferenciarlos le daría pistas a un atacante.
    return ErrorAPI(
        status.HTTP_401_UNAUTHORIZED,
        "Credenciales inválidas o vencidas. Volvé a iniciar sesión.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── 1 · Autenticación ──────────────────────────────────────────────────────


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> Principal:
    """Quién sos: decodifica el token y carga el principal desde la base."""
    if credentials is None:
        raise _no_autenticado()

    try:
        # decodificar_token verifica la firma, la expiración y los claims.
        payload = decodificar_token(credentials.credentials)
        tipo = TipoToken(payload["tipo"])
        sub = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise _no_autenticado() from None

    principal = _cargar_principal(session, tipo, sub, payload)
    if principal is None:
        # Token bien firmado, pero el usuario, el legajo o el acceso ya no vale.
        raise _no_autenticado()
    return principal


def _cargar_principal(
    session: Session, tipo: TipoToken, sub: UUID, payload: dict[str, Any]
) -> Principal | None:
    """Busca en la base lo que el token dice ser. None si ya no vale.

    Son lecturas por clave primaria, sin reglas de negocio, como el
    get_current_user del módulo 04.
    """
    if tipo is TipoToken.USUARIO:
        usuario = session.get(Usuario, sub)
        if usuario is None or not usuario.activo:
            return None
        # El rol sale de la BASE, no del token: el claim "rol" es solo referencia.
        return Principal(
            tipo=tipo,
            rol=Rol(usuario.rol),
            email=usuario.email,
            nombre=usuario.nombre,
            usuario_id=usuario.id,
        )

    if tipo is TipoToken.ASPIRANTE:
        legajo = session.get(Legajo, sub)
        if legajo is None:
            return None
        nombre = ", ".join(parte for parte in (legajo.apellido, legajo.nombre) if parte)
        return Principal(
            tipo=tipo,
            rol=Rol.ASPIRANTE,
            email=legajo.email,
            nombre=nombre or None,
            legajo_id=legajo.id,
        )

    # TipoToken.DOCENTE: el token vale mientras su acceso exista y no venza.
    try:
        seminario_id = UUID(payload["seminario_id"])
    except (KeyError, ValueError):
        return None
    acceso = session.get(AccesoDocente, sub)
    if (
        acceso is None
        or acceso.seminario_id != seminario_id
        or acceso.expira_en <= datetime.now(UTC)
    ):
        return None
    seminario = session.get(Seminario, seminario_id)
    return Principal(
        tipo=tipo,
        rol=Rol.DOCENTE,
        email=seminario.docente_email if seminario else None,
        nombre=seminario.docente_nombre if seminario else None,
        seminario_id=seminario_id,
        acceso_id=acceso.id,
    )


# ── 2 · Autorización por rol ───────────────────────────────────────────────


def require_role(*roles: Rol) -> Callable[..., Principal]:
    """Factory de dependencia: exige alguno de los `roles` (o 403).

    Devuelve el Principal, así el endpoint sabe quién llamó.
    """
    permitidos = frozenset(roles)

    def verificar_rol(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.rol not in permitidos:
            raise ErrorAPI(
                status.HTTP_403_FORBIDDEN,
                "No tenés permiso para realizar esta operación.",
            )
        return principal

    # La matriz de autorización de los tests lee esto para probar cada ruta.
    verificar_rol.roles_permitidos = permitidos  # type: ignore[attr-defined]
    return verificar_rol


# ── 3 · Autorización sobre el objeto (IDOR, ASR-002) ───────────────────────


def require_legajo_propio(*roles: Rol) -> Callable[..., Principal]:
    """require_role + si es un ASPIRANTE, el {legajo_id} de la ruta es el suyo.

    Los demás roles permitidos (por ejemplo, el coordinador) pasan: ven
    cualquier legajo. La ruta tiene que llamar al parámetro `legajo_id`.
    """
    verificar_rol = require_role(*roles)

    def verificar_legajo(
        legajo_id: UUID, principal: Principal = Depends(verificar_rol)
    ) -> Principal:
        if principal.rol is Rol.ASPIRANTE and principal.legajo_id != legajo_id:
            raise ErrorAPI(status.HTTP_403_FORBIDDEN, "Solo podés acceder a tu propio legajo.")
        return principal

    verificar_legajo.roles_permitidos = verificar_rol.roles_permitidos  # type: ignore[attr-defined]
    return verificar_legajo


def require_seminario_propio(*roles: Rol) -> Callable[..., Principal]:
    """require_role + si es un DOCENTE, el {seminario_id} de la ruta es el suyo.

    Es el guard de ASR-002: el docente del seminario 88 que pide el 99
    recibe 403. La ruta tiene que llamar al parámetro `seminario_id`.
    """
    verificar_rol = require_role(*roles)

    def verificar_seminario(
        seminario_id: UUID, principal: Principal = Depends(verificar_rol)
    ) -> Principal:
        if principal.rol is Rol.DOCENTE and principal.seminario_id != seminario_id:
            raise ErrorAPI(status.HTTP_403_FORBIDDEN, "Solo podés acceder a tu propio seminario.")
        return principal

    verificar_seminario.roles_permitidos = verificar_rol.roles_permitidos  # type: ignore[attr-defined]
    return verificar_seminario
