"""Static/structural gates for the Jyotish coordinate/state layer (JRE-003).

Enforces the Specialist spec's separation-of-concerns contracts:

- public API allow-list (``__all__``),
- the ``swisseph`` binding is confined to ``jyotish/swisseph/``,
- ``models.py`` imports only the standard library + astronomy models (pure
  data) — never providers, never the binding,
- no interpretation vocabulary (yoga/dasha/gochar/benefic/malefic/prediction/
  kundali/...) appears as an identifier anywhere in the package,
- no network imports, no forbidden layer imports.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import jyotish
import jyotish.models

SRC = Path(jyotish.__file__).resolve().parent

EXPECTED_PUBLIC_API = {
    # facade
    "JyotishService",
    "default_house_registry",
    "default_eclipse_registry",
    "get_house_provider",
    "get_eclipse_provider",
    # config
    "JyotishConfig",
    "ZodiacMode",
    "load_config",
    # classification
    "BodyId",
    "RetrogradeState",
    "RashiId",
    "NakshatraId",
    "Pada",
    "DmsValue",
    "PlanetState",
    "derive_planet_state",
    "classify_longitude",
    # catalogs
    "RASHI_CATALOG_VERSION",
    "RASHI_ORDER",
    "rashi_of",
    "degree_in_rashi",
    "sign_lord_of",
    "NAKSHATRA_CATALOG_VERSION",
    "NAKSHATRA_ORDER",
    "nakshatra_of",
    "degree_in_nakshatra",
    "lord_of",
    "pada_of",
    # geometry
    "AspectKind",
    "ApplyingSeparating",
    "AspectRelationship",
    "PairGeometry",
    "ASPECT_IDEAL_ANGLES",
    "angular_separation_deg",
    "normalized_separation_deg",
    "pair_geometry",
    "all_pairs",
    # houses / lagna
    "HouseSystem",
    "HouseCuspProvider",
    "HouseCuspRegistry",
    "HouseCuspResult",
    "HouseProviderMetadata",
    "SWISSEPH_HOUSE_PROVIDER_ID",
    "whole_sign_cusps",
    "compute_bhavas",
    "bhava_containing_longitude",
    "Bhava",
    "LagnaState",
    "derive_lagna",
    "NatalChart",
    "BirthData",
    # transit
    "TransitEventKind",
    "TransitReferencePoint",
    "TransitEvent",
    "TransitThroughHouses",
    "HouseTransitEntry",
    "SearchMetadata",
    "ContinuousTransitEngine",
    "iso_utc_to_jd",
    "jd_to_iso_utc",
    # eclipse
    "EclipseKind",
    "EclipseClassification",
    "EclipseContact",
    "GeographicVisibility",
    "EclipseEvent",
    "EclipseProvider",
    "EclipseRegistry",
    "SWISSEPH_ECLIPSE_PROVIDER_ID",
    # serialization
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "birth_from_dict",
    "planetary_request_from_dict",
    "transit_query_from_dict",
    "eclipse_query_from_dict",
    # errors
    "JyotishError",
    "InvalidBirthDataError",
    "InvalidConfigError",
    "InvalidOrbError",
    "UnsupportedHouseSystemError",
    "UnsupportedReferencePointError",
    "TransitSearchError",
    "EclipseError",
    "ProviderCompatibilityError",
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
    "import interpretations",
    "from interpretations",
    "import predictions",
    "from predictions",
    "import yoga",
    "from yoga",
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

#: Interpretation vocabulary that must NEVER appear in an identifier.
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
)


def _source_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def test_public_api_allow_list():
    assert set(jyotish.__all__) == EXPECTED_PUBLIC_API


def test_models_imports_stdlib_and_astronomy_only():
    tree = ast.parse(Path(jyotish.models.__file__).read_text())
    allowed_roots = {
        "ast",
        "__future__",
        "dataclasses",
        "datetime",
        "enum",
        "typing",
        "types",
        "functools",
        "math",
        "re",
        "pathlib",
        "astronomy",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_roots, f"models.py must not import {alias.name!r}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root in allowed_roots, f"models.py must not import {node.module!r}"


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
