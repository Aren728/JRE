"""Static / isolation gates (TEST-PLAN §6, SPEC §2/§3/§15/§16/§23/§24).

JRE-007 consumes ONLY the public ``jyotish`` + ``bhava`` + ``gochar``
roots and the standard library: no private lower-layer modules,
``astronomy.*``, ``knowledge.*``, ``swisseph``, network, or
interpretation/future-domain vocabulary in ``src/context`` — including
inside ``TYPE_CHECKING`` blocks. Eclipse is an *echo* of JRE-003 facts
(ADR-006/027), so the eclipse identifiers are permitted here. V1 defines
zero new enums except the context-specific lifecycle/capability states
(``CapabilityState``, ``FactKind``) and carries no candidate-generation
surface.
"""

from __future__ import annotations

import ast
from pathlib import Path

import context

SRC = Path(context.__file__).resolve().parent

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
    "gochar.models",
    "gochar.derive",
    "gochar.service",
    "gochar.serialize",
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

#: Interpretation + future-domain vocabulary (SPEC §3): JRE-007 must not
#: implement any of these. Eclipse is deliberately absent — JRE-007 echoes
#: JRE-003 eclipse facts (ADR-006/027).
INTERPRETATION_VOCABULARY = (
    "dasha",
    "prediction",
    "yoga",
    "benefic",
    "malefic",
    "auspicious",
    "forecast",
    "varga",
    "avastha",
    "bala",
    "ashtakavarga",
    "karaka",
    "jaimini",
    "tajika",
    "muhurta",
    "prashna",
    "rectification",
    "shadbala",
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
    for name in context.__all__:
        assert hasattr(context, name), f"__all__ symbol {name!r} not importable"
    assert len(set(context.__all__)) == len(context.__all__)  # no duplicates


def test_public_surface_pinned() -> None:
    expected = {
        "ContextService",
        "load_config",
        "validate",
        "ContextConfig",
        "CanonicalContext",
        "CanonicalFactSnapshot",
        "FactEnvelope",
        "FactKind",
        "CapabilityManifest",
        "CapabilityState",
        "CanonicalProvenance",
        "ProvenanceStage",
        "ContextRequest",
        "ContextInstantRequest",
        "ContextNatalRequest",
        "ContextIntervalRequest",
        "ContextEclipseRequest",
        "CAPABILITY_VERSION",
        "CAPABILITY_IDS",
        "CAPABILITIES",
        "CapabilityDescriptor",
        "check_capability",
        "assemble_snapshot",
        "chart_identity",
        "build_provenance",
        "civil_split",
        "canonical_bodies",
        "compute_deterministic_id",
        "ContextError",
        "InvalidContextConfigError",
        "InvalidContextRequestError",
        "ContextComputationError",
        "result_to_json",
        "result_to_dict",
        "config_from_dict",
        "context_request_from_dict",
        "instant_request_from_dict",
        "natal_request_from_dict",
        "interval_request_from_dict",
        "eclipse_request_from_dict",
        "schema_for",
        "validate_schema",
        "SCHEMAS",
        "CONTEXT_VERSION",
        "GOLDEN_VERSION",
        "TIME_PRECISION_VALUES",
        "PROVENANCE_STAGES",
    }
    assert set(context.__all__) == expected


def test_version_pinned() -> None:
    assert context.__version__ == "0.1.0"
    assert context.ContextConfig().version == "0.1.0"
    assert context.ContextConfig().snapshot_version == "0.1.0"


def _import_fragments(tree) -> list[str]:
    """All import targets as dotted strings (incl. inside functions and
    TYPE_CHECKING blocks). Attribute calls on the public roots (e.g.
    ``jyotish.all_pairs``, ``bhava.derive_house_analysis``) are NOT
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
                if isinstance(test_node, ast.Name) and test_node.id == "TYPE_CHECKING":
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
    level (imports of time/random/os and calls/attributes on them)."""
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
    scoped to the ordering/derivation modules (derive.py, service.py)."""
    for name in ("derive.py", "service.py"):
        tree = ast.parse((SRC / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in ("set", "dict"), (
                    f"{name} calls {node.func.id}()"
                )


def test_deferral_limitations_machine_testable() -> None:
    """SPEC §25: (1) the snapshot carries only echo sections — no
    varga/dasha/bala/ashtakavarga/avastha/karaka fields; (2) eclipse is an
    echo of the JRE-003 ``EclipseEvent`` type only, never a new engine;
    (3) no rule-match/synthesis results are embedded; (4) V1 accepts only
    point-valued ``BirthData`` — no candidate/uncertainty fields."""
    import context.models as models

    fields = set(context.CanonicalFactSnapshot.__dataclass_fields__)
    # (1) no future-domain computed fields.
    for forbidden in (
        "varga",
        "dasha",
        "shadbala",
        "bhava_bala",
        "ashtakavarga",
        "avastha",
        "karaka",
        "muhurta",
        "tajika",
        "jaimini",
        "prashna",
    ):
        assert forbidden not in fields, f"snapshot embeds future-domain field {forbidden!r}"
    # (2) eclipse section typed as the JRE-003 echo only.
    assert "eclipses" in fields
    assert not hasattr(models, "EclipseProvider")
    assert not hasattr(models, "find_eclipses")
    # (3) no rule-match / synthesis result types embedded.
    assert "matched_rules" not in fields
    assert "synthesis" not in " ".join(fields).lower()
    assert not hasattr(models, "SynthesisResult")
    # (4) V1: no candidate / uncertainty structures anywhere on the surface.
    for name in fields:
        assert "candidate" not in name.lower()
    assert "uncertainty" not in " ".join(fields).lower()
    assert not hasattr(models, "UncertaintyMetadata")
    assert not hasattr(models, "SNAPSHOT_SECTIONS")
    for symbol in context.__all__:
        assert "candidate" not in symbol.lower()


def test_zero_new_enums() -> None:
    """SPEC §6: JRE-007 defines zero new enums except the context-specific
    lifecycle/capability states (``CapabilityState``, ``FactKind``). Every
    astronomical enum is imported from ``jyotish``/``bhava``/``gochar``."""
    import enum

    import context.models as models

    for name, value in vars(models).items():
        if isinstance(value, type) and issubclass(value, enum.Enum):
            assert name in (
                # Context-specific lifecycle/capability states (V1 spec).
                "CapabilityState",
                "FactKind",
                # Stdlib / lower-layer re-exported aliases (imported, never defined).
                "StrEnum",
                "BodyId",
                "EclipseKind",
                "HouseSystem",
            ), f"{name} is a new enum defined by context"
