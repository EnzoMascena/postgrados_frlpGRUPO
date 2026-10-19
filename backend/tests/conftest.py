"""
Fixtures compartidas por todos los tests del backend.

  - Base de datos APARTE (postgrado_test): se crea sola si no existe, en el
    mismo servidor que la de desarrollo. Las tablas se crean con
    create_all() SOLO acá: en la app, el esquema lo maneja Alembic.
  - Rollback por test: cada test corre dentro de una transacción que se
    deshace al final. Ningún test ve los datos de otro, y el orden en que
    corren no importa.
  - get_session reemplazado: la app usa la Session del test, así lo que el
    test inserta lo ve la API, y lo que la API escribe se deshace después.
  - TestClient: le pega a la API como lo haría el front, sin levantar
    uvicorn.

Los tests de funciones puras (reglas.py, security.py) no piden ninguna de
estas fixtures: corren sin base de datos.
"""

import os
import shutil
import tempfile

# Antes de importar la app: config.py lee el entorno UNA vez al importarse.
os.environ["ENVIRONMENT"] = "testing"
os.environ["STORAGE_PATH"] = tempfile.mkdtemp(prefix="posgrado-test-storage-")

from collections.abc import Iterator  # noqa: E402
from datetime import UTC, date, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, make_url  # noqa: E402
from sqlmodel import Session, SQLModel, text  # noqa: E402

from app.core.config import STORAGE_PATH, TEST_DATABASE_URL  # noqa: E402
from app.core.database import get_session  # noqa: E402
from app.core.security import (  # noqa: E402
    crear_token_aspirante,
    crear_token_docente,
    crear_token_usuario,
    generar_token_opaco,
    hash_password,
    hash_token_opaco,
)
from app.main import app  # noqa: E402

# Importar app.models registra las 13 tablas en SQLModel.metadata (create_all).
from app.models import AccesoDocente, Carrera, Cohorte, Legajo, Seminario, Usuario  # noqa: E402
from app.models.enums import Rol, RolUsuario, TipoCarrera  # noqa: E402

# La contraseña de los usuarios de test.
CLAVE_DE_TEST = "Clave1234!"


def _crear_base_si_no_existe(url: str) -> None:
    """Crea la base de test en el servidor si todavía no existe."""
    destino = make_url(url)
    admin = create_engine(destino.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conexion:
        existe = conexion.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
            {"nombre": destino.database},
        ).scalar()
        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{destino.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def _limpiar_storage() -> Iterator[None]:
    """Borra la carpeta temporal de PDFs al terminar la corrida."""
    yield
    shutil.rmtree(STORAGE_PATH, ignore_errors=True)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """El engine de la base de test, con las tablas recién creadas."""
    _crear_base_si_no_existe(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Una Session dentro de una transacción que se deshace al final del test.

    join_transaction_mode="create_savepoint": los commit() del código bajo
    test se convierten en SAVEPOINTs, y el rollback del final deshace TODO.
    """
    conexion = engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaccion.rollback()
    conexion.close()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """TestClient de la app, usando la Session del test en cada request."""
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


# ── Datos base: la oferta académica ────────────────────────────────────────


def _guardar(session: Session, fila):
    session.add(fila)
    session.commit()
    session.refresh(fila)
    return fila


@pytest.fixture
def cohorte(session: Session) -> Cohorte:
    """La cohorte 2026, con la inscripción abierta."""
    return _guardar(
        session,
        Cohorte(
            anio=2026,
            nombre="Cohorte 2026",
            inscripcion_abierta=True,
            fecha_inicio=date(2026, 4, 1),
        ),
    )


@pytest.fixture
def carrera(session: Session) -> Carrera:
    """Una especialización (730 días para el semáforo)."""
    return _guardar(
        session,
        Carrera(
            nombre="Especialización en Ingeniería en Sistemas",
            nombre_corto="Esp. Ing. Sistemas",
            tipo=TipoCarrera.ESPECIALIZACION,
        ),
    )


@pytest.fixture
def seminario(session: Session, cohorte: Cohorte, carrera: Carrera) -> Seminario:
    """Un seminario de la cohorte 2026, con su docente."""
    return _guardar(
        session,
        Seminario(
            cohorte_id=cohorte.id,
            carrera_id=carrera.id,
            nombre="Gestión de Proyectos de Software",
            docente_nombre="Ing. Rodríguez, Ana",
            docente_email="a.rodriguez@frlp.utn.edu.ar",
            fecha_limite_actas=date(2026, 11, 30),
        ),
    )


# ── Un principal por rol, con su token ─────────────────────────────────────


@pytest.fixture(scope="session")
def hash_de_test() -> str:
    """El hash de CLAVE_DE_TEST, calculado una sola vez (bcrypt es lento a propósito)."""
    return hash_password(CLAVE_DE_TEST)


@pytest.fixture
def coordinador(session: Session, hash_de_test: str) -> Usuario:
    return _guardar(
        session,
        Usuario(
            email="coordinador@fenix.test",
            nombre="María González",
            password_hash=hash_de_test,
            rol=RolUsuario.COORDINADOR,
        ),
    )


@pytest.fixture
def cpr(session: Session, hash_de_test: str) -> Usuario:
    return _guardar(
        session,
        Usuario(
            email="cpr-test@fenix.test",
            nombre="Laura Martínez",
            password_hash=hash_de_test,
            rol=RolUsuario.CPR,
        ),
    )


@pytest.fixture
def legajo(session: Session, cohorte: Cohorte, carrera: Carrera) -> Legajo:
    """El borrador de un aspirante: es el único legajo que puede tocar su token."""
    return _guardar(
        session,
        Legajo(
            cohorte_id=cohorte.id,
            carrera_id=carrera.id,
            dni="30456789",
            email="ana.rodriguez@example.com",
            apellido="Rodríguez",
            nombre="Ana Laura",
        ),
    )


@pytest.fixture
def acceso_docente(session: Session, seminario: Seminario) -> AccesoDocente:
    """Un link de docente vigente para `seminario`."""
    return _guardar(
        session,
        AccesoDocente(
            seminario_id=seminario.id,
            token_hash=hash_token_opaco(generar_token_opaco()),
            expira_en=datetime.now(UTC) + timedelta(days=30),
            creado_por="coordinador@fenix.test",
        ),
    )


@pytest.fixture
def tokens(
    coordinador: Usuario, cpr: Usuario, legajo: Legajo, acceso_docente: AccesoDocente
) -> dict[Rol, str]:
    """Un token válido por rol."""
    return {
        Rol.COORDINADOR: crear_token_usuario(coordinador.id, coordinador.rol),
        Rol.CPR: crear_token_usuario(cpr.id, cpr.rol),
        Rol.ASPIRANTE: crear_token_aspirante(legajo.id),
        Rol.DOCENTE: crear_token_docente(
            acceso_docente.id, acceso_docente.seminario_id, acceso_docente.expira_en
        ),
    }


@pytest.fixture
def headers_por_rol(tokens: dict[Rol, str]) -> dict[Rol, dict[str, str]]:
    """El header Authorization listo para cada rol: client.get(url, headers=...)."""
    return {rol: {"Authorization": f"Bearer {token}"} for rol, token in tokens.items()}
