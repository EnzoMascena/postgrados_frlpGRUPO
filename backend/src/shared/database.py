"""Conexión con PostgreSQL: un engine para todo el proceso y una sesión por request."""

from collections.abc import Iterator
from importlib import import_module

from sqlmodel import Session, create_engine

from src.shared.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

MODULOS_CON_MODELOS = ("autenticacion", "cohortes", "gestion_documental", "inscripcion", "legajos")


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def importar_modelos() -> None:
    """Registra las tablas de los cinco módulos en `SQLModel.metadata`.

    Las usan Alembic (para comparar contra la base), el conftest (para crear las tablas de test)
    y el seed. Sin importar los `orm_models`, SQLModel no sabe que esas tablas existen.
    """
    for modulo in MODULOS_CON_MODELOS:
        import_module(f"src.{modulo}.infrastructure.orm_models")
