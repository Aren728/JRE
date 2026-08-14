"""Static gate 5: no personal/birth-data concept in ``src/knowledge``.

The layer's only data input is the anonymized ``fact_snapshot`` (SPEC §12.1,
architecture §17); nothing personal is ever stored. Identifiers only —
docstrings may describe the boundary.
"""

from __future__ import annotations

import ast
from pathlib import Path

import knowledge

SRC = Path(knowledge.__file__).resolve().parent

FORBIDDEN_IDENTIFIERS = ("birth", "personal", "name_of", "phone", "email")


def _identifiers(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
    return names


def test_no_birth_or_personal_identifiers():
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name in _identifiers(tree):
            lowered = name.lower()
            for word in FORBIDDEN_IDENTIFIERS:
                assert word not in lowered, f"{path.name} uses a personal-data identifier {name!r}"
