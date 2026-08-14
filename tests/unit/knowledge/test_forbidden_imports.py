"""Static gate 2: no forbidden layer/network imports (SPEC §18, ADR-007).

``knowledge`` may import only stdlib and the ``jyotish`` public API (the
package root), never ``astronomy``/``swisseph``/interpretation layers, and
never network modules. ``models.py`` is stdlib-only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import knowledge

SRC = Path(knowledge.__file__).resolve().parent

FORBIDDEN_LAYER_IMPORTS = (
    "import astronomy",
    "from astronomy",
    "import swisseph",
    "from swisseph",
    "import inference",
    "from inference",
    "import astrology",
    "from astrology",
    "import transits",
    "from transits",
    "import dasha",
    "from dasha",
    "import calculations",
    "from calculations",
    "import gochar",
    "from gochar",
    "import rules",
    "from rules",
)

FORBIDDEN_NETWORK_IMPORTS = (
    "import socket",
    "from socket",
    "import requests",
    "from requests",
    "import urllib",
    "from urllib",
    "import httpx",
    "from httpx",
)

ALLOWED_STDLIB_ROOTS = {
    "ast",
    "dataclasses",
    "enum",
    "hashlib",
    "json",
    "logging",
    "pathlib",
    "re",
    "tomllib",
    "typing",
    "__future__",
}


def _source_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def test_no_forbidden_layer_imports():
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_LAYER_IMPORTS:
            assert fragment not in text, f"{path.name} imports forbidden layer: {fragment}"


def test_no_network_imports():
    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_NETWORK_IMPORTS:
            assert fragment not in text, f"{path.name} imports network: {fragment}"


def test_models_imports_stdlib_only():
    tree = ast.parse((SRC / "models.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in ALLOWED_STDLIB_ROOTS, f"models.py must not import {alias.name!r}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root in ALLOWED_STDLIB_ROOTS, f"models.py must not import {node.module!r}"


def test_knowledge_imports_jyotish_public_api_only():
    """Only ``from jyotish import ...`` / ``import jyotish`` (never submodules)."""
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "jyotish":
                        assert alias.name == "jyotish", (
                            f"{path.name} must import jyotish's public root only"
                        )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".")[0] == "jyotish"
            ):
                assert node.module == "jyotish", (
                    f"{path.name} must import jyotish's public root only"
                )
