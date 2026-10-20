"""
Capa de infraestructura — la conexión a PostgreSQL.

Igual que el database.py del módulo 03: acá vive el ENGINE (se crea UNA
sola vez) y la dependencia `get_session`, que abre una Session por request
y la cierra al terminar. Ninguna otra capa importa el driver: piden una
sesión y listo.

Diferencia con la cátedra: el esquema NO se crea con create_all(). Lo
maneja Alembic (alembic/versions/), así cada cambio de tablas queda
versionado en Git. La app nunca crea ni altera tablas; solo la base de
test usa create_all() (tests/conftest.py).
"""

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from app.core.config import DATABASE_URL

# pool_pre_ping: si una conexión del pool se cortó (por ejemplo, se reinició
# el contenedor de postgres), la descarta y abre otra en vez de fallar.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Una Session nueva por cada request. Se cierra sola al terminar."""
    with Session(engine) as session:
        yield session
