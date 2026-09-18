"""Guard: requirements.txt must stay an exact mirror of pyproject.toml.

Cheap, always-on enforcement that runs with the normal test suite, so drift
is caught locally and in every CI job — not only in the dedicated workflow
step that calls scripts/sync_requirements.py --check.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _PROJECT_ROOT / "scripts" / "sync_requirements.py"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_requirements", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_requirements_txt_matches_pyproject_dependencies():
    """requirements.txt must be byte-identical to the generated mirror."""
    sync = _load_sync_module()
    expected = sync.render(sync.read_dependencies())

    requirements_path = _PROJECT_ROOT / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt is missing — run: python scripts/sync_requirements.py"

    actual = requirements_path.read_text()
    assert actual == expected, (
        "requirements.txt is out of sync with pyproject.toml.\n"
        "Run: python scripts/sync_requirements.py"
    )


def test_mirror_includes_core_ci_packages():
    """The core packages the staging CI flow relies on must be present."""
    sync = _load_sync_module()
    expected = sync.render(sync.read_dependencies())

    for pkg in (
        "sqlalchemy>=2.0.0",
        "psycopg[binary]>=3.1.0",
        "alembic>=1.13.0",
        "pysweph>=2.10.3.5,<3.0.0",
    ):
        assert pkg in expected, f"pyproject.toml dependencies must include {pkg}"
