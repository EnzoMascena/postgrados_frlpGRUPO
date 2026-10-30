"""Hash de contraseñas con bcrypt real. Cada hash tarda unos 250 ms: a propósito, son pocos."""

from src.autenticacion.application.iniciar_sesion import HASH_DE_RELLENO
from src.autenticacion.infrastructure.hashing import hashear_password, verificar_password


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
