"""Tests de integración de auth: la API de punta a punta, con la base de test.

POST /api/v1/auth/login y GET /api/v1/auth/me, como los usa el front.
"""

import pytest

from app.core.security import decodificar_token
from app.models.enums import Rol

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


def _login(client, email: str, password: str):
    return client.post(LOGIN, json={"email": email, "password": password})


# ── POST /auth/login ───────────────────────────────────────────────────────


def test_login_correcto_devuelve_un_token_de_usuario(client, coordinador, clave_de_test):
    # Act: email con dominio .test (email-validator lo rechazaría).
    respuesta = _login(client, "coordinador@fenix.test", clave_de_test)
    # Assert
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tokenType"] == "bearer"
    payload = decodificar_token(cuerpo["accessToken"])
    assert payload["sub"] == str(coordinador.id)
    assert payload["tipo"] == "usuario"
    assert payload["rol"] == "COORDINADOR"


def test_el_login_no_distingue_mayusculas_en_el_email(client, coordinador, clave_de_test):
    assert _login(client, " Coordinador@FENIX.test", clave_de_test).status_code == 200


def test_email_inexistente_y_clave_incorrecta_dan_la_misma_respuesta(
    client, coordinador, clave_de_test
):
    # User enumeration: mismo status y mismo mensaje en los dos casos.
    clave_mal = _login(client, "coordinador@fenix.test", "otra-clave")
    email_mal = _login(client, "nadie@fenix.test", clave_de_test)
    for respuesta in (clave_mal, email_mal):
        assert respuesta.status_code == 401
        assert respuesta.headers["www-authenticate"] == "Bearer"
        assert respuesta.json()["message"] == "Email o contraseña incorrectos."
        assert respuesta.json()["field"] is None


def test_una_clave_de_mas_de_72_bytes_da_401_y_no_500(client, coordinador):
    assert _login(client, "coordinador@fenix.test", "ñ" * 60).status_code == 401


def test_un_usuario_desactivado_no_puede_iniciar_sesion(
    client, session, coordinador, clave_de_test
):
    coordinador.activo = False
    session.add(coordinador)
    session.commit()
    assert _login(client, "coordinador@fenix.test", clave_de_test).status_code == 401


@pytest.mark.parametrize(
    ("body", "campo"),
    [({"password": "x"}, "email"), ({"email": "a@b.test"}, "password"), ({}, "email")],
)
def test_login_sin_campos_obligatorios_da_422_en_espanol(client, body, campo):
    respuesta = client.post(LOGIN, json=body)
    assert respuesta.status_code == 422
    assert respuesta.json()["field"] == campo
    assert respuesta.json()["message"] == "Este campo es obligatorio."


# ── GET /auth/me ───────────────────────────────────────────────────────────


def test_me_sin_token_da_401(client):
    respuesta = client.get(ME)
    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "UNAUTHORIZED"


def test_me_con_un_token_adulterado_da_401(client, tokens):
    adulterado = tokens[Rol.COORDINADOR][:-2] + "xx"
    respuesta = client.get(ME, headers={"Authorization": f"Bearer {adulterado}"})
    assert respuesta.status_code == 401


def test_me_del_coordinador_devuelve_sus_datos_en_camel_case(client, coordinador, headers_por_rol):
    respuesta = client.get(ME, headers=headers_por_rol[Rol.COORDINADOR])
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "tipo": "usuario",
        "rol": "COORDINADOR",
        "email": "coordinador@fenix.test",
        "nombre": "María González",
        "usuarioId": str(coordinador.id),
        "legajoId": None,
        "seminarioId": None,
    }


def test_me_del_aspirante_devuelve_su_legajo(client, legajo, headers_por_rol):
    cuerpo = client.get(ME, headers=headers_por_rol[Rol.ASPIRANTE]).json()
    assert cuerpo["tipo"] == "aspirante"
    assert cuerpo["rol"] == "ASPIRANTE"
    assert cuerpo["legajoId"] == str(legajo.id)
    assert cuerpo["nombre"] == "Rodríguez, Ana Laura"


def test_me_del_docente_devuelve_su_seminario(client, seminario, headers_por_rol):
    cuerpo = client.get(ME, headers=headers_por_rol[Rol.DOCENTE]).json()
    assert cuerpo["rol"] == "DOCENTE"
    assert cuerpo["seminarioId"] == str(seminario.id)
    assert cuerpo["nombre"] == "Ing. Rodríguez, Ana"


def test_el_token_del_login_sirve_para_me(client, cpr, clave_de_test):
    token = _login(client, "cpr-test@fenix.test", clave_de_test).json()["accessToken"]
    respuesta = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "CPR"
