"""Conexión con PostgreSQL: un engine para todo el proceso y una sesión por request."""

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from src.shared.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
