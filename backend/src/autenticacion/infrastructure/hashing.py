"""Hash de contraseñas con bcrypt de 12 rondas (NFR-S04), usando pwdlib.

`hashear_password` lo usa también el seed (Loli) para crear el coordinador de prueba.
"""

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

_password_hash = PasswordHash((BcryptHasher(rounds=12),))


def hashear_password(plano: str) -> str:
    """Devuelve algo como `$2b$12$<sal><hash>`: cada llamada usa una sal nueva."""
    return _password_hash.hash(plano)


def verificar_password(plano: str, hash_guardado: str) -> bool:
    return _password_hash.verify(plano, hash_guardado)
