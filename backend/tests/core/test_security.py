"""Tests de security.py: hash de contraseñas (NFR-S04) y tokens.

Son funciones puras: no necesitan base de datos ni levantar la API.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core import config
from app.core.security import (
    DUMMY_HASH,
    TipoToken,
    crear_token_aspirante,
    crear_token_docente,
    crear_token_usuario,
    decodificar_token,
    generar_token_opaco,
    hash_password,
    hash_token_opaco,
    verify_password,
)

# ── Hash de contraseñas ────────────────────────────────────────────────────


def test_hash_password_usa_bcrypt_con_costo_12():
    # Act
    hasheada = hash_password("Admin1234!")
    # Assert: $2b$ = bcrypt, 12 = costo (NFR-S04 pide 12 o más).
    assert hasheada.startswith("$2b$12$")
    assert "Admin1234!" not in hasheada


def test_el_mismo_password_da_hashes_distintos_por_la_sal():
    assert hash_password("Admin1234!") != hash_password("Admin1234!")


@pytest.mark.parametrize(
    ("intento", "esperado"),
    [("Admin1234!", True), ("admin1234!", False), ("", False), ("Admin1234! ", False)],
)
def test_verify_password_solo_acepta_la_contrasenia_exacta(intento, esperado):
    hasheada = hash_password("Admin1234!")
    assert verify_password(intento, hasheada) is esperado


def test_verify_password_con_mas_de_72_bytes_devuelve_false_sin_lanzar():
    hasheada = hash_password("Admin1234!")
    assert verify_password("x" * 100, hasheada) is False


def test_hash_password_rechaza_mas_de_72_bytes():
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("ñ" * 40)  # 80 bytes en UTF-8


def test_el_hash_senuelo_no_coincide_con_nada_comun():
    assert verify_password("Admin1234!", DUMMY_HASH) is False


# ── JWT ────────────────────────────────────────────────────────────────────


def test_token_de_usuario_lleva_sub_tipo_rol_y_vence_en_8_horas():
    usuario_id = uuid4()
    payload = decodificar_token(crear_token_usuario(usuario_id, "COORDINADOR"))
    assert payload["sub"] == str(usuario_id)
    assert payload["tipo"] == TipoToken.USUARIO
    assert payload["rol"] == "COORDINADOR"
    duracion = payload["exp"] - payload["iat"]
    assert duracion == pytest.approx(config.USUARIO_TOKEN_EXPIRE_MINUTES * 60, abs=5)


def test_token_de_aspirante_lleva_el_legajo_y_vence_en_7_dias():
    legajo_id = uuid4()
    payload = decodificar_token(crear_token_aspirante(legajo_id))
    assert payload["sub"] == str(legajo_id)
    assert payload["tipo"] == TipoToken.ASPIRANTE
    assert "rol" not in payload
    duracion = payload["exp"] - payload["iat"]
    assert duracion == pytest.approx(config.ASPIRANTE_TOKEN_EXPIRE_DAYS * 86400, abs=5)


def test_token_de_docente_lleva_el_seminario_y_el_vencimiento_pedido():
    acceso_id, seminario_id = uuid4(), uuid4()
    expira = datetime.now(UTC) + timedelta(hours=2)
    payload = decodificar_token(crear_token_docente(acceso_id, seminario_id, expira))
    assert payload["sub"] == str(acceso_id)
    assert payload["tipo"] == TipoToken.DOCENTE
    assert payload["seminario_id"] == str(seminario_id)
    assert payload["exp"] == int(expira.timestamp())


def test_un_token_vencido_no_se_acepta():
    vencido = crear_token_docente(uuid4(), uuid4(), datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decodificar_token(vencido)


def test_un_token_firmado_con_otra_clave_no_se_acepta():
    falso = jwt.encode(
        {"sub": str(uuid4()), "tipo": "usuario", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "otra-clave-que-no-es-la-del-servidor-de-32-bytes",
        algorithm="HS256",
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decodificar_token(falso)


def test_un_token_sin_firma_alg_none_no_se_acepta():
    # El "algorithm confusion attack": por eso algorithms=["HS256"] va explícito.
    sin_firma = jwt.encode(
        {"sub": str(uuid4()), "tipo": "usuario", "exp": datetime.now(UTC) + timedelta(hours=1)},
        None,
        algorithm="none",
    )
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(sin_firma)


def test_un_token_sin_el_claim_tipo_no_se_acepta():
    sin_tipo = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(UTC) + timedelta(hours=1)},
        config.SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(jwt.MissingRequiredClaimError):
        decodificar_token(sin_tipo)


# ── Tokens opacos ──────────────────────────────────────────────────────────


def test_el_token_opaco_tiene_32_bytes_y_no_se_repite():
    primero, segundo = generar_token_opaco(), generar_token_opaco()
    assert primero != segundo
    assert len(primero) >= 43  # 32 bytes en base64 URL-safe


def test_el_hash_del_token_opaco_es_sha256_y_estable():
    token = generar_token_opaco()
    assert hash_token_opaco(token) == hash_token_opaco(token)
    assert len(hash_token_opaco(token)) == 64
    assert hash_token_opaco(token) != token
