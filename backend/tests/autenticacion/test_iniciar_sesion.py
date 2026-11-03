"""Caso de uso `iniciar_sesion` con piezas falsas: sin base, sin bcrypt y sin JWT."""

from uuid import UUID, uuid4

import pytest

from src.autenticacion.application.iniciar_sesion import (
    HASH_DE_RELLENO,
    MENSAJE_LOGIN_INCORRECTO,
    SesionIniciada,
    iniciar_sesion,
)
from src.autenticacion.domain.usuario import Usuario
from src.shared.errors import NoAutenticado
from src.shared.roles import Rol


class RepoEnMemoria:
    def __init__(self, *usuarios: Usuario) -> None:
        self.usuarios = {usuario.email: usuario for usuario in usuarios}

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self.usuarios.get(email)

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        return next((u for u in self.usuarios.values() if u.id == usuario_id), None)


class VerificadorFalso:
    """El "hash" de una clave es `hash:<clave>`. Anota cada llamada para revisarla después."""

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, str]] = []

    def __call__(self, plano: str, hash_guardado: str) -> bool:
        self.llamadas.append((plano, hash_guardado))
        return hash_guardado == f"hash:{plano}"


def crear_token_falso(usuario: Usuario) -> tuple[str, int]:
    return f"token-de-{usuario.email}", 28800


def un_usuario(activo: bool = True) -> Usuario:
    return Usuario(
        id=uuid4(),
        email="coord@example.com",
        nombre="María González",
        rol=Rol.COORDINADOR,
        activo=activo,
        password_hash="hash:Clave1234!",
    )


def test_login_correcto_devuelve_el_token_su_duracion_y_el_usuario():
    usuario = un_usuario()

    sesion = iniciar_sesion(
        "coord@example.com",
        "Clave1234!",
        RepoEnMemoria(usuario),
        VerificadorFalso(),
        crear_token_falso,
    )

    assert sesion == SesionIniciada(
        access_token="token-de-coord@example.com", expira_en=28800, usuario=usuario
    )


def test_el_email_se_normaliza_antes_de_buscarlo():
    sesion = iniciar_sesion(
        "  Coord@Example.COM ",
        "Clave1234!",
        RepoEnMemoria(un_usuario()),
        VerificadorFalso(),
        crear_token_falso,
    )

    assert sesion.usuario.email == "coord@example.com"


@pytest.mark.parametrize(
    ("email", "password", "activo"),
    [
        ("coord@example.com", "OtraClave99!", True),  # contraseña incorrecta
        ("nadie@example.com", "Clave1234!", True),  # email inexistente
        ("coord@example.com", "Clave1234!", False),  # usuario inactivo
    ],
    ids=["clave-incorrecta", "email-inexistente", "usuario-inactivo"],
)
def test_los_tres_fallos_dan_401_con_el_mismo_mensaje(email, password, activo):
    repo = RepoEnMemoria(un_usuario(activo=activo))

    with pytest.raises(NoAutenticado) as error:
        iniciar_sesion(email, password, repo, VerificadorFalso(), crear_token_falso)

    assert error.value.status_code == 401
    assert error.value.mensaje == MENSAJE_LOGIN_INCORRECTO == "Email o contraseña incorrectos"
    assert error.value.campo is None


def test_con_un_email_inexistente_igual_verifica_contra_el_hash_de_relleno():
    verificador = VerificadorFalso()

    with pytest.raises(NoAutenticado):
        iniciar_sesion(
            "nadie@example.com", "Clave1234!", RepoEnMemoria(), verificador, crear_token_falso
        )

    assert verificador.llamadas == [("Clave1234!", HASH_DE_RELLENO)]


def test_con_un_usuario_inactivo_igual_verifica_la_contraseña():
    verificador = VerificadorFalso()

    with pytest.raises(NoAutenticado):
        iniciar_sesion(
            "coord@example.com",
            "Clave1234!",
            RepoEnMemoria(un_usuario(activo=False)),
            verificador,
            crear_token_falso,
        )

    assert verificador.llamadas == [("Clave1234!", "hash:Clave1234!")]


def test_el_hash_de_relleno_es_bcrypt_con_12_rondas():
    # Si tuviera menos rondas, el email inexistente respondería más rápido y se notaría.
    assert HASH_DE_RELLENO.startswith("$2b$12$")
    assert len(HASH_DE_RELLENO) == 60


def test_si_falla_no_se_crea_ningun_token():
    def crear_token_que_no_se_tiene_que_llamar(usuario: Usuario) -> tuple[str, int]:
        raise AssertionError("no se tenía que crear el token")

    with pytest.raises(NoAutenticado):
        iniciar_sesion(
            "coord@example.com",
            "OtraClave99!",
            RepoEnMemoria(un_usuario()),
            VerificadorFalso(),
            crear_token_que_no_se_tiene_que_llamar,
        )
