"""`get_current_user`, `require_role` y `actor_desde_usuario` en una app mínima.

La app tiene los manejadores de errores reales y la `session` de test (con rollback): los
usuarios se insertan directo con el ORM mientras no estén las fábricas (tests/fabricas.py).
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.jwt_tokens import MENSAJE_TOKEN_INVALIDO, crear_token
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.autenticacion.presentation.dependencies import (
    MENSAJE_SIN_PERMISO,
    MENSAJE_SIN_TOKEN,
    actor_desde_usuario,
    get_current_user,
    require_role,
)
from src.shared.config import settings
from src.shared.database import get_session
from src.shared.error_handlers import registrar_manejadores_de_errores
from src.shared.roles import Actor, Rol


@pytest.fixture
def cliente(session):
    app = FastAPI()
    registrar_manejadores_de_errores(app)

    @app.get("/yo")
    def yo(usuario: Usuario = Depends(get_current_user)):
        return {"email": usuario.email}

    @app.get("/solo-coordinador")
    def solo_coordinador(usuario: Usuario = Depends(require_role(Rol.COORDINADOR))):
        return {"email": usuario.email}

    @app.get("/coordinador-o-docente")
    def coordinador_o_docente(
        usuario: Usuario = Depends(require_role(Rol.COORDINADOR, Rol.DOCENTE)),
    ):
        return {"rol": usuario.rol}

    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def insertar_usuario(session, rol: Rol, activo: bool = True) -> Usuario:
    fila = UsuarioORM(
        email=f"{rol.lower()}-{uuid4().hex[:6]}@example.com",
        nombre="Usuario de prueba",
        password_hash="$2b$12$no-se-usa-en-estos-tests",
        rol=rol.value,
        activo=activo,
    )
    session.add(fila)
    session.commit()
    return PgUsuarioRepository(session).obtener(fila.id)


def headers_de(usuario: Usuario) -> dict[str, str]:
    token, _ = crear_token(usuario)
    return {"Authorization": f"Bearer {token}"}


def firmar(claims: dict) -> dict[str, str]:
    token = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def assert_401(respuesta, mensaje: str) -> None:
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "UNAUTHORIZED"
    assert respuesta.json()["message"] == mensaje


def test_con_un_token_valido_devuelve_el_usuario(cliente, session):
    coordinador = insertar_usuario(session, Rol.COORDINADOR)

    respuesta = cliente.get("/yo", headers=headers_de(coordinador))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"email": coordinador.email}


def test_sin_header_da_401_en_el_formato_del_plan(cliente):
    assert_401(cliente.get("/yo"), MENSAJE_SIN_TOKEN)


def test_con_otro_esquema_que_no_es_bearer_da_401(cliente):
    respuesta = cliente.get("/yo", headers={"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="})

    assert_401(respuesta, MENSAJE_SIN_TOKEN)


def test_con_un_token_basura_da_401(cliente):
    assert_401(
        cliente.get("/yo", headers={"Authorization": "Bearer no-es-un-jwt"}), MENSAJE_TOKEN_INVALIDO
    )


def test_con_un_token_vencido_da_401(cliente, session):
    coordinador = insertar_usuario(session, Rol.COORDINADOR)
    hace_9_horas = datetime.now(UTC) - timedelta(hours=9)
    claims = {
        "sub": str(coordinador.id),
        "email": coordinador.email,
        "rol": "COORDINADOR",
        "iat": hace_9_horas,
        "exp": hace_9_horas + timedelta(hours=8),
    }

    assert_401(cliente.get("/yo", headers=firmar(claims)), MENSAJE_TOKEN_INVALIDO)


def test_con_un_sub_que_no_es_un_uuid_da_401(cliente):
    ahora = datetime.now(UTC)
    claims = {
        "sub": "no-es-un-uuid",
        "email": "x@example.com",
        "rol": "COORDINADOR",
        "iat": ahora,
        "exp": ahora + timedelta(hours=1),
    }

    assert_401(cliente.get("/yo", headers=firmar(claims)), MENSAJE_TOKEN_INVALIDO)


def test_si_el_usuario_ya_no_existe_da_401(cliente):
    fantasma = Usuario(uuid4(), "fantasma@example.com", "Nadie", Rol.COORDINADOR, True, "x")

    assert_401(cliente.get("/yo", headers=headers_de(fantasma)), MENSAJE_TOKEN_INVALIDO)


def test_si_desactivan_al_usuario_su_token_deja_de_servir(cliente, session):
    coordinador = insertar_usuario(session, Rol.COORDINADOR)
    headers = headers_de(coordinador)
    session.get(UsuarioORM, coordinador.id).activo = False
    session.commit()

    assert_401(cliente.get("/yo", headers=headers), MENSAJE_TOKEN_INVALIDO)


def test_require_role_deja_pasar_al_rol_pedido(cliente, session):
    coordinador = insertar_usuario(session, Rol.COORDINADOR)

    respuesta = cliente.get("/solo-coordinador", headers=headers_de(coordinador))

    assert respuesta.status_code == 200


def test_require_role_con_otro_rol_da_403(cliente, session):
    docente = insertar_usuario(session, Rol.DOCENTE)

    respuesta = cliente.get("/solo-coordinador", headers=headers_de(docente))

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"
    assert respuesta.json()["message"] == MENSAJE_SIN_PERMISO


def test_require_role_sin_token_da_401_y_no_403(cliente):
    assert_401(cliente.get("/solo-coordinador"), MENSAJE_SIN_TOKEN)


@pytest.mark.parametrize(
    ("rol", "status"),
    [(Rol.COORDINADOR, 200), (Rol.DOCENTE, 200), (Rol.CPR, 403), (Rol.ADMIN, 403)],
)
def test_require_role_con_varios_roles_acepta_cualquiera_de_ellos(cliente, session, rol, status):
    usuario = insertar_usuario(session, rol)

    assert cliente.get("/coordinador-o-docente", headers=headers_de(usuario)).status_code == status


def test_el_rol_sale_de_la_base_y_no_del_token(cliente, session):
    # Aunque el token diga COORDINADOR (firmado con nuestra clave), el usuario es docente.
    docente = insertar_usuario(session, Rol.DOCENTE)
    ahora = datetime.now(UTC)
    claims = {
        "sub": str(docente.id),
        "email": docente.email,
        "rol": "COORDINADOR",
        "iat": ahora,
        "exp": ahora + timedelta(hours=1),
    }

    assert cliente.get("/solo-coordinador", headers=firmar(claims)).status_code == 403


def test_actor_desde_usuario_lleva_el_rol_y_el_email():
    usuario = Usuario(uuid4(), "coord@example.com", "María", Rol.COORDINADOR, True, "x")

    assert actor_desde_usuario(usuario) == Actor(rol=Rol.COORDINADOR, email="coord@example.com")
