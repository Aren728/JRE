"""Static / isolation gates (TEST-PLAN §6, SPEC §2/§23/§24/§26).

JRE-006 consumes ONLY the public ``jyotish`` + ``bhava`` roots and the
standard library: no ``jyotish.models``/``jyotish.service``/…,
``astronomy.*``, ``knowledge.*``, ``bhava.models``/``bhava.derive``/
``bhava.service``, ``swisseph``, network, or interpretation/eclipse
vocabulary in ``src/gochar`` — including inside ``TYPE_CHECKING`` blocks.
"""

from __future__ import annotations

import ast
from pathlib import Path

import gochar

SRC = Path(gochar.__file__).resolve().parent

FORBIDDEN_IMPORT_FRAGMENTS = (
    "jyotish.models",
    "jyotish.swisseph",
    "jyotish.service",
    "jyotish.transit",
    "jyotish.geometry",
    "jyotish.houses",
    "jyotish.lagna",
    "jyotish.position",
    "jyotish.rashi",
    "jyotish.nakshatra",
    "jyotish.eclipse",
    "bhava.models",
    "bhava.derive",
    "bhava.service",
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
    "dasha",
    "prediction",
    "yoga",
    "benefic",
    "malefic",
    "auspicious",
    "forecast",
    "eclipse",
)

#: Provenance-hygiene scan (SPEC §26.3): no wall-clock / random / process /
#: environment data in provenance construction.
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


def test_public_all_members_importable() -> None:
    for name in gochar.__all__:
        assert hasattr(gochar, name), f"__all__ symbol {name!r} not importable"
    assert len(set(gochar.__all__)) == len(gochar.__all__)  # no duplicates


def test_public_surface_pinned() -> None:
    expected = {
        "GocharService",
        "load_config",
        "validate",
        "GocharConfig",
        "GocharInstantResult",
        "GocharNatalResult",
        "GocharIntervalResult",
        "GocharInstantRequest",
        "GocharNatalRequest",
        "GocharIntervalRequest",
        "GocharProvenance",
        "sort_events",
        "build_provenance",
        "derive_natal_house_series",
        "civil_split",
        "canonical_bodies",
        "GocharError",
        "InvalidGocharConfigError",
        "InvalidGocharRequestError",
        "GocharComputationError",
        "result_to_json",
        "result_to_dict",
        "config_from_dict",
        "instant_request_from_dict",
        "natal_request_from_dict",
        "interval_request_from_dict",
        "schema_for",
        "validate_schema",
        "SCHEMAS",
        "GOLDEN_VERSION",
    }
    assert set(gochar.__all__) == expected


def test_version_pinned() -> None:
    assert gochar.__version__ == "0.2.0"
    assert gochar.GocharConfig().version == "0.2.0"


def _import_fragments(tree) -> list[str]:
    """All import targets as dotted strings (incl. inside functions and
    TYPE_CHECKING blocks). Attribute calls on the public roots (e.g.
    ``bhava.derive_transit_analysis``, ``jyotish.all_pairs``) are NOT
    imports and are not collected."""
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


def test_forbidden_imports_absent() -> None:
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fragment in _import_fragments(tree):
            for forbidden in FORBIDDEN_IMPORT_FRAGMENTS:
                assert forbidden not in fragment, (
                    f"{path.name} imports forbidden: {fragment}"
                )
        # Direct module access to private modules would require an import;
        # the AST import scan above covers it. Also reject raw "import" of
        # a forbidden top-level package anywhere in text (e.g. comments).
        text = path.read_text(encoding="utf-8")
        for forbidden in ("import swisseph", "from swisseph"):
            assert forbidden not in text, f"{path.name} imports forbidden: {forbidden}"


def test_no_type_checking_bypass() -> None:
    """SPEC §2.2: TYPE_CHECKING blocks must not import forbidden modules."""
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "TYPE_CHECKING" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            for test_node in ast.walk(node.test):
                if (
                    isinstance(test_node, ast.Name)
                    and test_node.id == "TYPE_CHECKING"
                ):
                    imports = [
                        n
                        for n in ast.walk(node)
                        if isinstance(n, (ast.Import, ast.ImportFrom))
                    ]
                    for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                        for imp in imports:
                            assert fragment not in ast.unparse(imp), (
                                f"{path.name} TYPE_CHECKING imports forbidden: {fragment}"
                            )


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


def test_provenance_hygiene() -> None:
    """SPEC §26.3: provenance construction must not use wall-clock time,
    randomness, process identity, or environment data. Checked at the AST
    level (imports of time/random/os and calls/attributes on them) so the
    docstrings mentioning the prohibition are not false positives."""
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [alias.name.split(".")[0] for alias in node.names]
                names.append(node.module.split(".")[0])
                for name in names:
                    assert name not in ("time", "random", "os"), (
                        f"{path.name} imports forbidden provenance source {name!r}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in ("time", "random", "os"), (
                        f"{path.name} imports forbidden provenance source {alias.name!r}"
                    )
            elif isinstance(node, ast.Attribute):
                assert node.attr not in ("getpid", "environ"), (
                    f"{path.name} uses {node.attr!r}"
                )
            elif isinstance(node, ast.Name):
                assert node.id not in ("getpid", "environ"), (
                    f"{path.name} uses {node.id!r}"
                )


def test_no_set_dict_iteration_in_ordering_paths() -> None:
    """SPEC §26.5: no set/dict iteration in the ordering paths. The scan is
    scoped to the ordering/derivation modules (derive.py, service.py);
    serialize.py's schema validator may use sets for key-set checks, which
    are not ordering paths."""
    for name in ("derive.py", "service.py"):
        tree = ast.parse((SRC / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in ("set", "dict"), (
                    f"{name} calls {node.func.id}()"
                )


def test_deferral_limitations_machine_testable() -> None:
    """SPEC §25: (1) no generic transit-chart request shape; (2) interval
    events carry only the JRE-003 ``TransitEventKind`` set; (3) no
    aspect-event kind exists anywhere."""
    import gochar.models as models

    # (1) GENERIC results carry no houses/lagna/chart fields.
    generic_fields = set(gochar.GocharInstantResult.__dataclass_fields__)
    assert "birth_snapshot" not in generic_fields
    assert "bhavas" not in generic_fields
    assert "lagna" not in generic_fields
    # The generic request has no chart/location fields.
    req_fields = set(gochar.GocharInstantRequest.__dataclass_fields__)
    assert not {"latitude", "longitude", "house_system"} & req_fields

    # (2) No house-ingress kind beyond the JRE-003 set.
    from jyotish import TransitEventKind

    assert not hasattr(TransitEventKind, "HOUSE_INGRESS")

    # (3) No aspect-event kind anywhere (ADR-029).
    assert not hasattr(TransitEventKind, "ASPECT_EXACT")
    assert "aspect_event" not in models.__dict__


def test_zero_new_enums() -> None:
    """SPEC §6: JRE-006 defines zero new enums — every enum used is imported
    from ``jyotish``/``bhava``."""
    import enum

    import gochar.models as models

    for name, value in vars(models).items():
        if isinstance(value, type) and issubclass(value, enum.Enum):
            assert name in (
                # Re-exported aliases only (imported, never defined).
                "ApplyingSeparating",
                "AspectKind",
                "BodyId",
                "FactFrame",
                "HouseSystem",
                "TransitEventKind",
                "TransitReferencePoint",
            ), f"{name} is a new enum defined by gochar"
