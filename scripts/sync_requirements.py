#!/usr/bin/env python3
"""Sync requirements.txt with pyproject.toml — single source of truth.

requirements.txt is a GENERATED, byte-exact mirror of the
``[project] dependencies`` list in pyproject.toml. Never edit it by hand.

Usage::

    python scripts/sync_requirements.py           # regenerate requirements.txt
    python scripts/sync_requirements.py --check   # exit 1 if out of sync (CI)

The mirror is intentionally top-level-only (no transitive pinning). If a
fully pinned lockfile is ever needed, introduce pip-compile/uv as a
separate *.lock file — do not widen this file's contract.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

HEADER = """\
# GENERATED FILE — do not edit by hand.
# Exact mirror of pyproject.toml [project] dependencies.
# Regenerate:  python scripts/sync_requirements.py
# CI enforces sync via:  python scripts/sync_requirements.py --check
"""


def read_dependencies() -> list[str]:
    with PYPROJECT_PATH.open("rb") as f:
        deps = tomllib.load(f)["project"]["dependencies"]
    if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
        raise SystemExit("pyproject.toml [project] dependencies must be a list of strings")
    return deps


def render(requirements: list[str]) -> str:
    return HEADER + "\n" + "\n".join(requirements) + "\n"


def main() -> int:
    expected = render(read_dependencies())
    actual = REQUIREMENTS_PATH.read_text() if REQUIREMENTS_PATH.exists() else ""

    if actual == expected:
        print(f"OK: {REQUIREMENTS_PATH.name} is in sync with pyproject.toml")
        return 0

    if "--check" in sys.argv[1:]:
        import difflib

        diff = difflib.unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=str(REQUIREMENTS_PATH),
            tofile=f"{REQUIREMENTS_PATH} (expected)",
        )
        sys.stderr.write("".join(diff))
        sys.stderr.write(
            f"\nERROR: {REQUIREMENTS_PATH.name} is out of sync with pyproject.toml.\n"
            "Run: python scripts/sync_requirements.py\n"
        )
        return 1

    REQUIREMENTS_PATH.write_text(expected)
    print(f"Regenerated {REQUIREMENTS_PATH} from pyproject.toml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
