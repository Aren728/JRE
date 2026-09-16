import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# 1. Import your SQLAlchemy Base / Models here
# Adjust the import path to match your model registry location
from src.jrs.db.base import Base  # or wherever your Base/models are declared

config = context.config

# Override sqlalchemy.url with environment variable if present
if db_url := os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

# 2. Set target_metadata to your Base.metadata
target_metadata = Base.metadata
