"""`PgUsuarioRepository` contra la base de test (con rollback por test, ver conftest)."""

from uuid import uuid4

import pytest

from src.autenticacion.domain.usuario import Usuario
from src.autenticacion.infrastructure.orm_models import UsuarioORM
from src.autenticacion.infrastructure.pg_repository import PgUsuarioRepository
from src.shared.roles import Rol
from tests.fabricas import crear_usuario


@pytest.fixture
def fila(session) -> UsuarioORM:
    return crear_usuario(session, email="coord@example.com", nombre="María González")


def test_buscar_por_email_devuelve_el_usuario_del_dominio(session, fila):
    usuario = PgUsuarioRepository(session).buscar_por_email("coord@example.com")

    assert usuario == Usuario(
        id=fila.id,
        email="coord@example.com",
        nombre="María González",
        rol=Rol.COORDINADOR,
        activo=True,
        password_hash=fila.password_hash,
    )
    assert isinstance(usuario.rol, Rol)


def test_buscar_por_email_inexistente_devuelve_none(session, fila):
    assert PgUsuarioRepository(session).buscar_por_email("nadie@example.com") is None


def test_obtener_por_id_devuelve_el_usuario(session, fila):
    usuario = PgUsuarioRepository(session).obtener(fila.id)

    assert usuario is not None
    assert usuario.email == "coord@example.com"


def test_obtener_un_id_inexistente_devuelve_none(session, fila):
    assert PgUsuarioRepository(session).obtener(uuid4()) is None


def test_un_usuario_inactivo_se_devuelve_igual_con_activo_falso(session, fila):
    # Quien decide qué hacer con un inactivo es el caso de uso, no el repositorio.
    fila.activo = False
    session.commit()

    assert PgUsuarioRepository(session).buscar_por_email("coord@example.com").activo is False


def test_activos_con_rol_trae_solo_los_activos_de_ese_rol_ordenados_por_email(session, fila):
    crear_usuario(session, email="beta@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="alfa@example.com", rol=Rol.COORDINADOR)
    crear_usuario(session, email="inactivo@example.com", rol=Rol.COORDINADOR, activo=False)
    crear_usuario(session, email="docente@example.com", rol=Rol.DOCENTE)

    usuarios = PgUsuarioRepository(session).activos_con_rol(Rol.COORDINADOR)

    assert [usuario.email for usuario in usuarios] == [
        "alfa@example.com",
        "beta@example.com",
        "coord@example.com",
    ]
    assert all(isinstance(usuario, Usuario) for usuario in usuarios)


def test_activos_con_rol_sin_ninguno_devuelve_lista_vacia(session, fila):
    assert PgUsuarioRepository(session).activos_con_rol(Rol.CPR) == []
