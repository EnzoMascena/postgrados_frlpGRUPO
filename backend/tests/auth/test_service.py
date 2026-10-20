"""Tests del AuthService con un repository FALSO: sin base de datos.

Es la ventaja de que el service reciba el repository desde afuera (módulo
03): en el test le pasamos uno de mentira y probamos solo las reglas.
"""

import pytest

from app.auth import service as modulo_service
from app.auth.service import AuthService
from app.core.security import DUMMY_HASH, hash_password
from app.models import Usuario
from app.models.enums import RolUsuario

HASH_ADMIN = hash_password("Admin1234!")


class RepositorioFalso:
    """Imita a UsuarioRepository con un diccionario en memoria."""

    def __init__(self, *usuarios: Usuario):
        self.por_email = {usuario.email: usuario for usuario in usuarios}
        self.buscados: list[str] = []

    def get_by_email(self, email: str) -> Usuario | None:
        self.buscados.append(email)
        return self.por_email.get(email)


def _admin(activo: bool = True) -> Usuario:
    return Usuario(
        email="admin@fenix.test",
        nombre="María González",
        password_hash=HASH_ADMIN,
        rol=RolUsuario.COORDINADOR,
        activo=activo,
    )


def test_con_credenciales_validas_devuelve_el_usuario():
    # Arrange
    admin = _admin()
    service = AuthService(RepositorioFalso(admin))
    # Act
    resultado = service.autenticar("admin@fenix.test", "Admin1234!")
    # Assert
    assert resultado is admin


def test_normaliza_el_email_antes_de_buscar():
    repositorio = RepositorioFalso(_admin())
    resultado = AuthService(repositorio).autenticar("  Admin@FENIX.test ", "Admin1234!")
    assert resultado is not None
    assert repositorio.buscados == ["admin@fenix.test"]


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("admin@fenix.test", "otra-clave"),  # contraseña incorrecta
        ("nadie@fenix.test", "Admin1234!"),  # email que no existe
        ("admin@fenix.test", "x" * 200),  # más de 72 bytes: no rompe
    ],
)
def test_credenciales_invalidas_devuelven_none(email, password):
    assert AuthService(RepositorioFalso(_admin())).autenticar(email, password) is None


def test_un_usuario_desactivado_no_entra_aunque_la_clave_sea_correcta():
    service = AuthService(RepositorioFalso(_admin(activo=False)))
    assert service.autenticar("admin@fenix.test", "Admin1234!") is None


def test_si_el_email_no_existe_igual_verifica_contra_el_hash_senuelo(monkeypatch):
    # Timing attack: "email inexistente" tiene que pagar el costo de bcrypt.
    verificados: list[str] = []

    def verify_espia(plano: str, hasheado: str) -> bool:
        verificados.append(hasheado)
        return False

    monkeypatch.setattr(modulo_service, "verify_password", verify_espia)
    AuthService(RepositorioFalso()).autenticar("nadie@fenix.test", "Admin1234!")
    assert verificados == [DUMMY_HASH]
