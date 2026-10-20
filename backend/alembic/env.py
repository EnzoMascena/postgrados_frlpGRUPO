"""
Entorno de Alembic: a qué base se conecta y contra qué modelos compara.

  - La URL sale de app/core/config.py (DATABASE_URL), no de alembic.ini: un
    solo lugar para la configuración y nada de credenciales en el repo.
  - target_metadata = SQLModel.metadata con las 13 tablas de app.models: es
    lo que `alembic revision --autogenerate` compara contra la base.
  - compare_type=True: también detecta cambios de tipo (VARCHAR(100) → 150).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app import models  # noqa: F401  (importarlo registra las 13 tablas)
from app.core.config import DATABASE_URL

config = context.config
# configparser interpreta los "%": se escapan por si la clave tiene alguno.
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Modo offline: genera el SQL sin conectarse (alembic upgrade head --sql)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo normal: se conecta a la base y aplica las migraciones."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
