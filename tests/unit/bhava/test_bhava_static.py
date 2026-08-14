"""Static / isolation gates (TEST-PLAN §8, SPEC §3/§31).

JRE-005 consumes ONLY the ``jyotish`` public API + stdlib: no
``jyotish.models``, ``astronomy.*``, ``knowledge.*``, ``swisseph``,
network, or interpretation vocabulary in ``src/bhava``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import bhava

SRC = Path(bhava.__file__).resolve().parent

FORBIDDEN_IMPORT_FRAGMENTS = (
    "jyotish.models",
    "jyotish.swisseph",
    "astronomy",
    "knowledge",
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

INTERPRETATION_VOCABULARY = (
    "benefic",
    "malefic",
    "yoga",
    "dasha",
    "gochar",
    "prediction",
    "varga",
    "kundali",
    "muhurta",
    "wealth",
    "marriage",
    "career",
    "fortune",
    "auspicious",
)


def test_public_all_members_importable() -> None:
    for name in bhava.__all__:
        assert hasattr(bhava, name), f"__all__ symbol {name!r} not importable"
    assert len(set(bhava.__all__)) == len(bhava.__all__)  # no duplicates


def test_public_surface_pinned() -> None:
    expected = {
        "BhavaService",
        "load_config",
        "validate",
        "BhavaConfig",
        "HouseAnalysisResult",
        "HouseAnalysis",
        "TransitHouseAnalysis",
        "DerivedHouseFact",
        "PlanetHouseFact",
        "HouseOwnershipFact",
        "RelativeHouseFact",
        "AspectToHouseFact",
        "TransitHouseFact",
        "DerivationBlock",
        "ChartEcho",
        "OccupancyStatus",
        "BoundaryKind",
        "HouseCategory",
        "RelativeHouseFrame",
        "UnplacedBodyBehavior",
        "FactFrame",
        "DerivationId",
        "SIGN_GRID_FRAME_SUPPORTED",
        "GOLDEN_VERSION",
        "shortest_arc_deg",
        "near_cusp",
        "house_categories",
        "relative_house",
        "whole_sign_house",
        "derive_house_analysis",
        "derive_transit_analysis",
        "BhavaError",
        "InvalidAnalysisRequestError",
        "InvalidBhavaConfigError",
        "InconsistentChartError",
        "UnplacedBodyError",
        "UnsupportedReferenceError",
        "result_to_json",
        "result_to_dict",
        "analysis_request_from_dict",
        "transit_request_from_dict",
    }
    assert set(bhava.__all__) == expected


def test_forbidden_imports_absent() -> None:
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert fragment not in text, f"{path.name} imports forbidden: {fragment}"


def test_no_interpretation_vocabulary_in_identifiers() -> None:
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.append(node.name)
            elif isinstance(node, ast.arg):
                names.append(node.arg)
            for name in names:
                lowered = name.lower()
                for word in INTERPRETATION_VOCABULARY:
                    assert word not in lowered, (
                        f"{path.name} uses interpretation identifier {name!r}"
                    )


def test_no_network_imports() -> None:
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import socket" not in text
        assert "import requests" not in text
        assert "import urllib" not in text
        assert "import httpx" not in text
