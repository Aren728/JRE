# db driver runtime wiring placeholder
import os

def _resolve_db_url():
    from os import environ
    return environ.get("DATABASE_URL")
