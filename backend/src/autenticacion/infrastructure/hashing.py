"""Hash de contraseñas con bcrypt de 12 rondas (NFR-S04), usando pwdlib.

`hashear_password` lo usa también el seed (Loli) para crear el coordinador de prueba.

bcrypt solo mira los primeros 72 bytes de la contraseña, y desde bcrypt 5.0 una más larga levanta
`ValueError` (que llegaría al front como un 500). Se cuentan bytes en UTF-8, no caracteres:
una "ñ" ocupa 2 bytes y un emoji 4, así que un `max_length` en el schema no alcanza.
"""

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from src.shared.errors import ErrorDeValidacion

MAXIMO_BYTES_BCRYPT = 72

_password_hash = PasswordHash((BcryptHasher(rounds=12),))


def _supera_el_maximo(plano: str) -> bool:
    return len(plano.encode("utf-8")) > MAXIMO_BYTES_BCRYPT


def hashear_password(plano: str) -> str:
    """Devuelve algo como `$2b$12$<sal><hash>`: cada llamada usa una sal nueva."""
    # No se corta en silencio: dos claves con los mismos primeros 72 bytes servirían igual.
    if _supera_el_maximo(plano):
        raise ErrorDeValidacion(
            f"La contraseña puede tener hasta {MAXIMO_BYTES_BCRYPT} bytes", campo="password"
        )
    return _password_hash.hash(plano)


def verificar_password(plano: str, hash_guardado: str) -> bool:
    # Una clave de más de 72 bytes nunca puede ser la correcta: `hashear_password` no deja
    # guardarla. Se responde False sin llamar a bcrypt, exista o no el usuario.
    if _supera_el_maximo(plano):
        return False
    return _password_hash.verify(plano, hash_guardado)
