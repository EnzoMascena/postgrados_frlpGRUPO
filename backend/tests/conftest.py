"""Fixtures comunes de los tests.

Los tests de integración corren contra una base PostgreSQL de verdad (`postgrado_test`, la de
TEST_DATABASE_URL), no contra mocks. Para que ningún test vea los datos de otro, cada uno corre
dentro de una transacción que se deshace al terminar (rollback por test):

1. `engine` (una vez por corrida): crea la base de test si no existe y arma las tablas.
2. `session` (una por test): abre una conexión, empieza una transacción y arma una `Session`
   que se une a ella con `join_transaction_mode="create_savepoint"`. Cuando el código del test
   (o un repositorio) hace `session.commit()`, solo cierra un SAVEPOINT: la transacción de
   afuera sigue abierta. Al terminar el test se hace rollback de todo y la base queda como estaba.
3. `client` (uno por test): el `TestClient` de la app, con `get_session` reemplazado por esa misma
   `session`. Lo que crea el test con las fábricas lo ve el endpoint, y al revés.

Por eso en los tests se puede (y se debe) hacer `session.commit()` sin miedo a ensuciar la base.
"""

import os
import tempfile

# La configuración se lee una sola vez, al importar `src`: estas variables van antes de cualquier
# import de `src` o de `main`.
os.environ["ENVIRONMENT"] = "testing"
os.environ["STORAGE_PATH"] = tempfile.mkdtemp(prefix="posgrado-storage-")
os.environ.setdefault("JWT_SECRET", "secreto-solo-para-los-tests-de-32-o-mas-caracteres")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from main import app  # noqa: E402
from src.autenticacion.infrastructure.orm_models import UsuarioORM  # noqa: E402
from src.shared.config import settings  # noqa: E402
from src.shared.database import get_session, importar_modelos  # noqa: E402
from src.shared.email.sender import BANDEJA_DE_PRUEBA  # noqa: E402
from src.shared.roles import Rol  # noqa: E402
from tests.fabricas import crear_usuario, headers_de  # noqa: E402


def _crear_base_de_test_si_no_existe() -> None:
    url = make_url(settings.test_database_url)
    # CREATE DATABASE no corre dentro de una transacción: hay que conectarse en AUTOCOMMIT y
    # a otra base (la `postgres`), porque la de test todavía puede no existir.
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conexion:
        existe = conexion.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"), {"nombre": url.database}
        ).scalar()
        if not existe:
            nombre = admin.dialect.identifier_preparer.quote(url.database)
            conexion.execute(text(f"CREATE DATABASE {nombre}"))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    _crear_base_de_test_si_no_existe()
    engine = create_engine(settings.test_database_url)
    importar_modelos()  # sin esto, SQLModel.metadata está vacío y no se crea ninguna tabla
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with engine.connect() as conexion:
        transaccion = conexion.begin()
        with Session(bind=conexion, join_transaction_mode="create_savepoint") as sesion:
            yield sesion
        transaccion.rollback()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    # Se saca solo este override: un test puede haber agregado otros por su cuenta.
    app.dependency_overrides.pop(get_session, None)


# --- Usuarios con sesión iniciada (Luca, L1) ---
# Para llamar a un endpoint protegido: `client.get("/api/v1/legajos", headers=headers_coordinador)`.
# Los dos usuarios tienen la contraseña `CLAVE_DE_PRUEBA` de las fábricas. Para otro rol:
# `headers_de(session, crear_usuario(session, rol=Rol.CPR))`.


@pytest.fixture
def coordinador(session) -> UsuarioORM:
    return crear_usuario(
        session, email="coordinador@example.com", rol=Rol.COORDINADOR, nombre="María González"
    )


@pytest.fixture
def headers_coordinador(session, coordinador) -> dict[str, str]:
    return headers_de(session, coordinador)


@pytest.fixture
def docente(session) -> UsuarioORM:
    return crear_usuario(session, email="docente@example.com", rol=Rol.DOCENTE, nombre="Juan Pérez")


@pytest.fixture
def headers_docente(session, docente) -> dict[str, str]:
    return headers_de(session, docente)


@pytest.fixture
def bandeja():
    """Los emails que mandó el código bajo test: en testing no sale ninguno por SMTP.

    Llega vacía en cada test. Se usa así: `assert bandeja[0].plantilla == "aprobacion.html"`.
    """
    BANDEJA_DE_PRUEBA.clear()
    return BANDEJA_DE_PRUEBA
