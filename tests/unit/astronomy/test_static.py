"""Static/structural gates for the astronomical core.

These tests scan the source tree to enforce:

- the public API allow-list (``__all__``),
- one-way module boundaries (no imports from other JRE layers, no network),
- no astrological interpretation vocabulary anywhere in ``src/astronomy``.
"""

import ast
import re
from pathlib import Path

import astronomy
import astronomy.models

SRC = Path(astronomy.__file__).resolve().parent

EXPECTED_PUBLIC_API = {
    "AstronomicalService",
    "EphemerisRequest",
    "EphemerisResult",
    "CalculationConfig",
    "BodyId",
    "BodyPosition",
    "ProviderMetadata",
    "ProviderRun",
    "RetrogradeState",
    "Ayanamsa",
    "EphemerisMode",
    "PositionType",
    "NodeType",
    "EphemerisProvider",
    "ProviderRegistry",
    "default_registry",
    "get_provider",
    "EphemerisError",
    "InvalidTimestampError",
    "InvalidCoordinatesError",
    "UnsupportedProviderError",
    "EphemerisDataError",
    "result_to_json",
    "result_to_dict",
    "request_from_dict",
    "config_from_dict",
}

FORBIDDEN_LAYER_IMPORTS = (
    "import astrology",
    "from astrology",
    "import knowledge",
    "from knowledge",
    "import transits",
    "from transits",
    "import dasha",
    "from dasha",
    "import calculations",
    "from calculations",
    "import inference",
    "from inference",
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

INTERPRETATION_VOCABULARY = (
    "rashi",
    "nakshatra",
    "bhava",
    "yoga",
    "dasha",
    "gochar",
    "benefic",
    "malefic",
    "prediction",
    "varga",
    "kundali",
)


def _source_files():
    return sorted(SRC.rglob("*.py"))


def test_public_api_allow_list():
    assert set(astronomy.__all__) == EXPECTED_PUBLIC_API


def test_models_imports_stdlib_only():
    tree = ast.parse(astronomy.models.__file__ and Path(astronomy.models.__file__).read_text())
    stdlib = {
        "ast",
        "__future__",  # from __future__ import annotations (used by models.py)
        "dataclasses",
        "datetime",
        "enum",
        "typing",
        "types",
        "functools",
        "math",
        "re",
        "pathlib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in stdlib, f"models.py must not import {alias.name!r}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root in stdlib, f"models.py must not import {node.module!r}"


def test_no_forbidden_layer_imports():
    for path in _source_files():
        text = path.read_text()
        for fragment in FORBIDDEN_LAYER_IMPORTS:
            assert fragment not in text, f"{path.name} imports forbidden layer: {fragment}"


def test_no_network_imports():
    for path in _source_files():
        text = path.read_text()
        for fragment in FORBIDDEN_NETWORK_IMPORTS:
            assert fragment not in text, f"{path.name} imports network: {fragment}"


def test_no_interpretation_vocabulary_in_identifiers():
    for path in _source_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.append(node.name)
            elif isinstance(node, ast.arg):
                names.append(node.arg)
            for name in names:
                lowered = name.lower()
                for word in INTERPRETATION_VOCABULARY:
                    message = f"{path.name} uses interpretation identifier {name!r}"
                    assert word not in lowered, message


def test_swisseph_binding_confined_to_adapter():
    adapter_dir = SRC / "swisseph"
    for path in _source_files():
        if path.parent == adapter_dir or path.name == "__init__.py":
            continue
        text = path.read_text()
        if re.search(r"^\s*(import swisseph|from swisseph)", text, re.MULTILINE):
            raise AssertionError(f"{path.name} must not import the swisseph binding")
