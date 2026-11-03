"""Hash de contraseñas con bcrypt real. Cada hash tarda unos 250 ms: a propósito, son pocos."""

import pytest

from src.autenticacion.application.iniciar_sesion import HASH_DE_RELLENO
from src.autenticacion.infrastructure.hashing import hashear_password, verificar_password
from src.shared.errors import ErrorDeValidacion


def test_el_hash_es_bcrypt_con_12_rondas_y_no_contiene_la_contraseña():
    hash_guardado = hashear_password("Clave1234!")

    assert hash_guardado.startswith("$2b$12$")
    assert "Clave1234!" not in hash_guardado


def test_la_contraseña_correcta_verifica_y_una_incorrecta_no():
    hash_guardado = hashear_password("Clave1234!")

    assert verificar_password("Clave1234!", hash_guardado) is True
    assert verificar_password("clave1234!", hash_guardado) is False


def test_la_misma_contraseña_da_hashes_distintos_por_la_sal():
    assert hashear_password("Clave1234!") != hashear_password("Clave1234!")


def test_el_hash_de_relleno_del_login_es_valido_y_no_coincide_con_una_clave_comun():
    # Si no fuera un hash bcrypt válido, verificar contra él fallaría o no tardaría lo mismo.
    assert verificar_password("Clave1234!", HASH_DE_RELLENO) is False


# bcrypt mira hasta 72 bytes en UTF-8. "ñ" ocupa 2 bytes: 40 "ñ" son 40 caracteres pero 80 bytes.
CLAVES_DE_MAS_DE_72_BYTES = pytest.mark.parametrize(
    "plano", ["a" * 73, "a" * 1000, "ñ" * 40], ids=["73-ascii", "1000-ascii", "40-enies-80-bytes"]
)


def test_una_contraseña_de_72_bytes_justos_se_hashea_y_verifica():
    plano = "a" * 70 + "ñ"  # 70 + 2 = 72 bytes

    assert verificar_password(plano, hashear_password(plano)) is True


@CLAVES_DE_MAS_DE_72_BYTES
def test_verificar_una_contraseña_de_mas_de_72_bytes_da_falso_sin_error(plano):
    hash_guardado = hashear_password("Clave1234!")

    assert verificar_password(plano, hash_guardado) is False
    assert verificar_password(plano, HASH_DE_RELLENO) is False


@CLAVES_DE_MAS_DE_72_BYTES
def test_hashear_una_contraseña_de_mas_de_72_bytes_da_error_de_validacion(plano):
    with pytest.raises(ErrorDeValidacion) as error:
        hashear_password(plano)

    assert error.value.status_code == 422
    assert error.value.campo == "password"
    assert error.value.mensaje == "La contraseña puede tener hasta 72 bytes"
