"""Static / isolation gates (normative specification §23-§24).

JRE-008 consumes ONLY the public ``jyotish`` root and the standard
library: no private JRE-003 modules, no ``astronomy``/``knowledge``/
``bhava``/``gochar``/``context`` imports, no ``swisseph``, no network,
no wall-clock/random/environment dependence, and no
prediction/interpretation/strength vocabulary in implementation code.
The ``varga`` module docstring documents the boundary by negation and is
excluded from the vocabulary scan.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import varga

SRC = Path(varga.__file__).resolve().parent

FORBIDDEN_IMPORT_FRAGMENTS = (
    "jyotish.models",
    "jyotish.service",
    "jyotish.transit",
    "jyotish.geometry",
    "jyotish.houses",
    "jyotish.lagna",
    "jyotish.position",
    "jyotish.rashi",
    "jyotish.nakshatra",
    "jyotish.eclipse",
    "jyotish.swisseph",
    "astronomy",
    "knowledge",
    "bhava",
    "gochar",
    "context",
    "swisseph",
    "import socket",
    "from socket",
    "import requests",
    "from requests",
    "import urllib",
    "from urllib",
    "import httpx",
    "from httpx",
)

#: Interpretation / prediction / strength vocabulary (word boundaries;
#: the canonical name "Dwadashamsa" legitimately contains "dasha" but not
#: as a standalone word).
INTERPRETATION_VOCABULARY = (
    r"\bdasha\b",
    r"\bprediction\b",
    r"\byoga\b",
    r"\bbenefic\b",
    r"\bmalefic\b",
    r"\bauspicious\b",
    r"\bforecast\b",
    r"\bkaraka\b",
    r"\bjaimini\b",
    r"\btajika\b",
    r"\bmuhurta\b",
    r"\bprashna\b",
    r"\brectification\b",
    r"\bshadbala\b",
    r"\bavastha\b",
    r"\bashtakavarga\b",
    r"\binterpret\b",
    r"\bstrength\b",
)

#: No wall-clock / random / process / environment data (spec §15, §27).
HYGIENE_FRAGMENTS = (
    "import time",
    "from time",
    "time.time(",
    "time.perf_counter",
    "time.monotonic",
    "time.process_time",
    "import random",
    "from random",
    "random.",
    "getpid",
    "environ",
)


def _module_docstring(text: str) -> str:
    """Strip the leading module docstring (negation documentation)."""
    match = re.match(r'\s*"""(?:.|\n)*?"""', text)
    if match:
        return text[match.end() :]
    return text


def _import_fragments(tree) -> list[str]:
    fragments: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                fragments.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            fragments.append(node.module)
            for alias in node.names:
                if alias.name != "*":
                    fragments.append(f"{node.module}.{alias.name}")
    return fragments


def test_public_all_members_importable() -> None:
    for name in varga.__all__:
        assert hasattr(varga, name), f"__all__ symbol {name!r} not importable"
    assert len(set(varga.__all__)) == len(varga.__all__)


def test_forbidden_imports_absent() -> None:
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fragment in _import_fragments(tree):
            for forbidden in FORBIDDEN_IMPORT_FRAGMENTS:
                assert forbidden not in fragment, (
                    f"{path.name} imports forbidden: {fragment}"
                )
        text = path.read_text(encoding="utf-8")
        for forbidden in ("import swisseph", "from swisseph"):
            assert forbidden not in text, f"{path.name} imports forbidden: {forbidden}"


def test_no_interpretation_vocabulary_in_code() -> None:
    for path in SRC.rglob("*.py"):
        text = _module_docstring(path.read_text(encoding="utf-8"))
        for pattern in INTERPRETATION_VOCABULARY:
            match = re.search(pattern, text)
            assert match is None, (
                f"{path.name} contains interpretation vocabulary {pattern!r} "
                f"at {match.group()!r}"
            )


def test_no_hygiene_dependence() -> None:
    for path in SRC.rglob("*.py"):
        text = _module_docstring(path.read_text(encoding="utf-8"))
        for fragment in HYGIENE_FRAGMENTS:
            assert fragment not in text, f"{path.name} contains {fragment!r}"


def test_d27_absent() -> None:
    assert "D27" not in varga.VARGA_IDS
    assert "D27" not in varga.VARGA_REGISTRY
    for varga_id in varga.VARGA_IDS:
        assert varga_id != "D27"


def test_v1_scope_exact() -> None:
    expected = {
        "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
        "D20", "D24", "D30", "D40", "D45", "D60",
    }
    assert set(varga.VARGA_IDS) == expected
    assert "D1" not in varga.VARGA_IDS
    for varga_id in varga.VARGA_IDS:
        assert varga_id not in {"D5", "D6", "D11", "D13", "D22", "D27"}


def test_version_pinned() -> None:
    assert varga.__version__ == "0.1.0"
    assert varga.VARGA_VERSION == "0.1.0"
    assert varga.VARGA_CATALOG_VERSION == "0.1.0"
