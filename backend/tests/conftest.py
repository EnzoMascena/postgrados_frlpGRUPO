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

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, make_url  # noqa: E402
from sqlmodel import Session, SQLModel, text  # noqa: E402

from app.core.config import STORAGE_PATH, TEST_DATABASE_URL  # noqa: E402
from app.core.database import get_session  # noqa: E402
from app.main import app  # noqa: E402


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
