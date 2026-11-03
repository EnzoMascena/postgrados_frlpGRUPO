"""Schemas del login: qué aceptan y qué JSON devuelven (el contrato con el front, plan §10)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.autenticacion.application.iniciar_sesion import SesionIniciada
from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.presentation.schemas import LoginRequest, LoginResponse, UsuarioResponse
from src.shared.roles import Rol


def un_usuario() -> Usuario:
    return Usuario(
        id=uuid4(),
        email="admin@fenix.test",
        nombre="María González",
        rol=Rol.COORDINADOR,
        activo=True,
        password_hash="$2b$12$no-tiene-que-salir",
    )


def test_el_login_acepta_el_email_del_seed_con_dominio_test():
    # Con EmailStr esto daría 422: `.test` es un dominio reservado.
    datos = LoginRequest(email="admin@fenix.test", password="Admin1234!")

    assert datos.email == "admin@fenix.test"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("email", ""),
        ("email", "a" * 256),
        ("password", ""),
        ("password", "a" * 129),
    ],
    ids=["email-vacio", "email-de-256", "password-vacio", "password-de-129"],
)
def test_el_login_rechaza_campos_vacios_o_demasiado_largos(campo, valor):
    datos = {"email": "admin@fenix.test", "password": "Admin1234!", campo: valor}

    with pytest.raises(ValidationError) as error:
        LoginRequest(**datos)

    assert error.value.errors()[0]["loc"] == (campo,)


def test_el_login_acepta_una_contraseña_de_128_caracteres():
    # 128 caracteres pasan el schema; si son más de 72 bytes, `verificar_password` da False (401).
    assert LoginRequest(email="admin@fenix.test", password="a" * 128).password == "a" * 128


def test_la_respuesta_del_login_tiene_el_json_del_plan():
    usuario = un_usuario()
    sesion = SesionIniciada(access_token="eyJ...", expira_en=28800, usuario=usuario)

    cuerpo = LoginResponse.model_validate(sesion).model_dump(mode="json", by_alias=True)

    assert cuerpo == {
        "accessToken": "eyJ...",
        "tokenType": "bearer",
        "expiraEn": 28800,
        "usuario": {
            "id": str(usuario.id),
            "email": "admin@fenix.test",
            "nombre": "María González",
            "rol": "COORDINADOR",
        },
    }


def test_el_usuario_de_la_respuesta_no_lleva_el_hash_ni_activo():
    cuerpo = UsuarioResponse.model_validate(un_usuario()).model_dump(by_alias=True)

    assert set(cuerpo) == {"id", "email", "nombre", "rol"}
