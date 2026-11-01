"""`POST /auth/login` y `GET /auth/me` contra la app real y la base de test."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from src.shared.config import settings
from src.shared.roles import Rol
from tests.fabricas import CLAVE_DE_PRUEBA, crear_usuario

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
CLAVES_DE_ERROR = {"statusCode", "error", "message", "field", "timestamp"}


def login(client, email: str, password: str = CLAVE_DE_PRUEBA):
    return client.post(LOGIN, json={"email": email, "password": password})


# --- POST /auth/login ---


def test_login_correcto_da_200_con_el_cuerpo_del_plan(client, coordinador):
    respuesta = login(client, "coordinador@example.com")

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert set(cuerpo) == {"accessToken", "tokenType", "expiraEn", "usuario"}
    assert cuerpo["tokenType"] == "bearer"
    assert cuerpo["expiraEn"] == 28800
    assert cuerpo["usuario"] == {
        "id": str(coordinador.id),
        "email": "coordinador@example.com",
        "nombre": "María González",
        "rol": "COORDINADOR",
    }


def test_el_token_del_login_sirve_para_llamar_a_auth_me(client, coordinador):
    token = login(client, "coordinador@example.com").json()["accessToken"]

    respuesta = client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "coordinador@example.com"


def test_login_con_el_email_en_mayusculas_y_con_espacios(client, coordinador):
    assert login(client, "  Coordinador@Example.COM ").status_code == 200


def test_login_con_un_email_de_dominio_test_como_el_del_seed(client, session):
    crear_usuario(session, email="admin@fenix.test")

    assert login(client, "admin@fenix.test").status_code == 200


@pytest.mark.parametrize(
    ("email", "password", "activo"),
    [
        ("coordinador@example.com", "OtraClave99!", True),
        ("nadie@example.com", CLAVE_DE_PRUEBA, True),
        ("coordinador@example.com", CLAVE_DE_PRUEBA, False),
    ],
    ids=["clave-incorrecta", "email-inexistente", "usuario-inactivo"],
)
def test_login_fallido_da_401_con_el_mismo_mensaje_en_los_tres_casos(
    client, session, email, password, activo
):
    crear_usuario(session, email="coordinador@example.com", activo=activo)

    respuesta = login(client, email, password)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 401
    assert set(cuerpo) == CLAVES_DE_ERROR
    assert cuerpo["error"] == "UNAUTHORIZED"
    assert cuerpo["message"] == "Email o contraseña incorrectos"
    assert cuerpo["field"] is None


@pytest.mark.parametrize("password", ["a" * 100, "ñ" * 40], ids=["100-ascii", "40-enies"])
def test_login_con_una_contraseña_de_mas_de_72_bytes_da_401_y_no_500(client, coordinador, password):
    assert login(client, "coordinador@example.com", password).status_code == 401
    assert login(client, "nadie@example.com", password).status_code == 401


@pytest.mark.parametrize(
    ("cuerpo", "campo"),
    [
        ({"password": CLAVE_DE_PRUEBA}, "email"),
        ({"email": "coordinador@example.com"}, "password"),
        ({"email": "coordinador@example.com", "password": ""}, "password"),
        ({"email": "coordinador@example.com", "password": "a" * 129}, "password"),
    ],
    ids=["sin-email", "sin-password", "password-vacio", "password-de-129"],
)
def test_login_con_datos_invalidos_da_422_en_el_campo(client, cuerpo, campo):
    respuesta = client.post(LOGIN, json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "VALIDATION_ERROR"
    assert respuesta.json()["field"] == campo


def test_login_es_publico_y_responde_con_los_headers_de_seguridad(client, coordinador):
    respuesta = login(client, "coordinador@example.com")

    assert respuesta.headers["x-content-type-options"] == "nosniff"
    assert respuesta.headers["x-frame-options"] == "DENY"


# --- GET /auth/me ---


def test_me_con_token_devuelve_el_usuario_sin_el_hash(client, coordinador, headers_coordinador):
    respuesta = client.get(ME, headers=headers_coordinador)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": str(coordinador.id),
        "email": "coordinador@example.com",
        "nombre": "María González",
        "rol": "COORDINADOR",
    }


def test_me_sin_token_da_401(client):
    respuesta = client.get(ME)

    assert respuesta.status_code == 401
    assert respuesta.json()["message"] == "Necesitás iniciar sesión para continuar"


def test_me_con_un_token_vencido_da_401(client, coordinador):
    hace_9_horas = datetime.now(UTC) - timedelta(hours=9)
    claims = {
        "sub": str(coordinador.id),
        "email": coordinador.email,
        "rol": "COORDINADOR",
        "iat": hace_9_horas,
        "exp": hace_9_horas + timedelta(hours=8),
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")

    respuesta = client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401
    assert respuesta.json()["message"] == "Tu sesión venció o no es válida. Volvé a iniciar sesión"


def test_me_con_un_docente_da_403(client, headers_docente):
    respuesta = client.get(ME, headers=headers_docente)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "FORBIDDEN"
    assert respuesta.json()["message"] == "No tenés permiso para esta acción"


# --- Swagger ---


def test_swagger_documenta_los_dos_endpoints_con_sus_errores(client):
    esquema = client.get("/api/openapi.json").json()

    login_doc = esquema["paths"][LOGIN]["post"]
    me_doc = esquema["paths"][ME]["get"]
    assert login_doc["tags"] == ["Autenticación"]
    assert {"200", "401", "422"} <= set(login_doc["responses"])
    assert {"200", "401", "403"} <= set(me_doc["responses"])
    # /auth/me pide el token (botón "Authorize" de Swagger); el login no.
    assert me_doc["security"] == [{"HTTPBearer": []}]
    assert "security" not in login_doc


def test_un_rol_sin_permiso_tampoco_entra_aunque_tenga_login(client, session):
    # El login funciona para cualquier usuario activo; lo que se restringe es cada endpoint.
    crear_usuario(session, email="cpr@example.com", rol=Rol.CPR)
    token = login(client, "cpr@example.com").json()["accessToken"]

    assert client.get(ME, headers={"Authorization": f"Bearer {token}"}).status_code == 403
