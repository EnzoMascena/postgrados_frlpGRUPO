"""Caso de uso: iniciar sesión con email y contraseña.

Recibe por parámetro el repositorio, la función que verifica la contraseña y la que crea el
token: no sabe nada de la base, de bcrypt ni de JWT, y se testea con piezas falsas.
"""

from collections.abc import Callable
from dataclasses import dataclass

from src.autenticacion.domain.repo import UsuarioRepository
from src.autenticacion.domain.usuario import Usuario
from src.shared.errors import NoAutenticado

MENSAJE_LOGIN_INCORRECTO = "Email o contraseña incorrectos"

# Hash bcrypt (12 rondas) de un valor aleatorio que se descartó: no es la contraseña de nadie.
# Si el email no existe se verifica contra este hash igual, para que la respuesta tarde lo mismo
# que con un email registrado y no se pueda adivinar quién tiene usuario midiendo el tiempo.
HASH_DE_RELLENO = "$2b$12$rfBEn7mKNfFYNytJ7lvoPuZQVYY3s5q3Ip1td7qbnFo90JjqQKWLG"


@dataclass(frozen=True)
class SesionIniciada:
    access_token: str
    expira_en: int  # segundos de validez del token
    usuario: Usuario


def iniciar_sesion(
    email: str,
    password: str,
    repo: UsuarioRepository,
    verificar_password: Callable[[str, str], bool],
    crear_token: Callable[[Usuario], tuple[str, int]],
) -> SesionIniciada:
    usuario = repo.buscar_por_email(email.strip().lower())

    if usuario is None:
        verificar_password(password, HASH_DE_RELLENO)
        raise NoAutenticado(MENSAJE_LOGIN_INCORRECTO)

    # La contraseña se verifica también si el usuario está inactivo: así ese caso tarda lo mismo
    # y responde lo mismo que una clave incorrecta.
    password_correcta = verificar_password(password, usuario.password_hash)
    if not password_correcta or not usuario.activo:
        raise NoAutenticado(MENSAJE_LOGIN_INCORRECTO)

    token, expira_en = crear_token(usuario)
    return SesionIniciada(access_token=token, expira_en=expira_en, usuario=usuario)
