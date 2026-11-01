"""Tokens JWT: se crean, se vuelven a leer y se rechazan si vencieron o no los firmamos nosotros."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.jwt_tokens import (
    MENSAJE_TOKEN_INVALIDO,
    crear_token,
    decodificar_token,
)
from src.shared.config import settings
from src.shared.errors import NoAutenticado
from src.shared.roles import Rol


@pytest.fixture
def usuario() -> Usuario:
    return Usuario(
        id=uuid4(),
        email="coord@example.com",
        nombre="María González",
        rol=Rol.COORDINADOR,
        activo=True,
        password_hash="no-importa-en-estos-tests",
    )


def claims_de(usuario: Usuario, **cambios) -> dict:
    ahora = datetime.now(UTC)
    claims = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "rol": usuario.rol.value,
        "iat": ahora,
        "exp": ahora + timedelta(hours=1),
    }
    claims.update(cambios)
    return {clave: valor for clave, valor in claims.items() if valor is not None}


def assert_rechazado(token: str) -> None:
    with pytest.raises(NoAutenticado) as error:
        decodificar_token(token)
    assert error.value.status_code == 401
    assert error.value.mensaje == MENSAJE_TOKEN_INVALIDO


def test_el_token_se_vuelve_a_leer_con_los_datos_del_usuario(usuario):
    token, _ = crear_token(usuario)

    claims = decodificar_token(token)

    assert claims["sub"] == str(usuario.id)
    assert claims["email"] == "coord@example.com"
    assert claims["rol"] == "COORDINADOR"


def test_el_token_dura_lo_que_dice_la_configuracion_8_horas_por_defecto(usuario):
    token, expira_en = crear_token(usuario)

    claims = decodificar_token(token)

    assert expira_en == settings.jwt_expira_minutos * 60 == 28800
    assert claims["exp"] - claims["iat"] == expira_en


def test_el_token_no_lleva_la_contraseña_ni_su_hash(usuario):
    token, _ = crear_token(usuario)

    # El payload de un JWT se puede leer sin la clave: solo la firma es secreta.
    payload = jwt.decode(token, options={"verify_signature": False})

    assert set(payload) == {"sub", "email", "rol", "iat", "exp"}


def test_un_token_vencido_da_401(usuario):
    hace_9_horas = datetime.now(UTC) - timedelta(hours=9)
    token = jwt.encode(
        claims_de(usuario, iat=hace_9_horas, exp=hace_9_horas + timedelta(hours=8)),
        settings.jwt_secret,
        algorithm="HS256",
    )

    assert_rechazado(token)


def test_un_token_firmado_con_otra_clave_da_401(usuario):
    token = jwt.encode(
        claims_de(usuario), "otra-clave-que-no-es-la-nuestra-de-32-o-mas", algorithm="HS256"
    )

    assert_rechazado(token)


def test_un_token_sin_firma_alg_none_da_401(usuario):
    token = jwt.encode(claims_de(usuario), None, algorithm="none")

    assert_rechazado(token)


def test_un_token_sin_vencimiento_da_401(usuario):
    token = jwt.encode(claims_de(usuario, exp=None), settings.jwt_secret, algorithm="HS256")

    assert_rechazado(token)


@pytest.mark.parametrize("token", ["", "no-es-un-jwt", "a.b.c"])
def test_algo_que_no_es_un_jwt_da_401(token):
    assert_rechazado(token)
