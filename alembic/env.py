import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Make the src/ tree importable so `jrs.*` resolves even without an
# editable install (complements alembic.ini's prepend_sys_path = .).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alembic import context
from sqlalchemy import engine_from_config, pool

# 1. Import Base AND the models so both register on the same metadata.
#
#    Use the canonical `jrs.*` package path — importing via `src.jrs.*`
#    (the old form here) creates a *second* module instance with its own
#    empty Base.metadata, so autogenerate would see no tables.
from jrs.db.base import Base
import jrs.db.models  # noqa: F401  — registers ChartCalculation on Base.metadata

config = context.config

# Override sqlalchemy.url with environment variable if present
if db_url := os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

# 2. Set target_metadata to your Base.metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
