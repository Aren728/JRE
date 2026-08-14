"""Rule schema: condition grammar + pinned fact-vocabulary validation + evaluation.

Implements SPEC §6. The fact vocabulary is pinned and versioned
(``FACT_VOCABULARY_VERSION = "1.1.0"``, bumped additively per ADR-012: the
``relative_house`` reference set now spans all nine bodies and four
derived-fact paths were added — ``planet(<BODY>).nature``,
``planet(<BODY>).dignity``, ``planet(<BODY>).combusted`` and
``pair(<A>,<B>).aspect_strength`` — all computed by the JRE-004 facts layer,
never by JRE-003). Conditions bind only to these paths and are schema-
validated at catalog load (never silently "matches nothing").
Evaluation is pure and deterministic against the canonical ``fact_snapshot``
dict (SPEC §6.1): a missing snapshot key makes an atom **False** — never an
exception.

The value sets below are pinned data mirroring the JRE-003/astronomy enums
(``jyotish`` public API exposes most of them; the body/retrograde sets are
pinned here so the layer stays within its import boundary — ADR-007).
Ordered tuples give the deterministic enum order used by ``LT/LTE/GT/GTE``
on enum-ordered strings (SPEC §6.1).

This module imports stdlib only (no ``jyotish``), keeping the schema layer
pure; ``synthesis.py`` is the module that touches JRE-003 objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, cast

from .errors import RuleSchemaError
from .models import (
    ConditionCombiner,
    ConditionOp,
    RuleCondition,
    RuleDomain,
)

FACT_VOCABULARY_VERSION = "1.1.0"

# --------------------------------------------------------------------------- #
# Pinned vocabulary value sets (SPEC §6.2) — ordered tuples give enum order
# --------------------------------------------------------------------------- #

BODY_IDS: tuple[str, ...] = (
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
    "RAHU",
    "KETU",
)
RASHI_IDS: tuple[str, ...] = (
    "MESHA",
    "VRISHABHA",
    "MITHUNA",
    "KARKA",
    "SIMHA",
    "KANYA",
    "TULA",
    "VRISHCHIKA",
    "DHANUSHA",
    "MAKARA",
    "KUMBHA",
    "MEENA",
)
NAKSHATRA_IDS: tuple[str, ...] = (
    "ASHWINI",
    "BHARANI",
    "KRITTIKA",
    "ROHINI",
    "MRIGASHIRA",
    "ARDRA",
    "PUNARVASU",
    "PUSHYA",
    "ASHLESHA",
    "MAGHA",
    "PURVA_PHALGUNI",
    "UTTARA_PHALGUNI",
    "HASTA",
    "CHITRA",
    "SWATI",
    "VISHAKHA",
    "ANURADHA",
    "JYESHTHA",
    "MULA",
    "PURVA_ASHADHA",
    "UTTARA_ASHADHA",
    "SHRAVANA",
    "DHANISHTHA",
    "SHATABHISHA",
    "PURVA_BHADRAPADA",
    "UTTARA_BHADRAPADA",
    "REVATI",
)
RETROGRADE_STATES: tuple[str, ...] = ("DIRECT", "RETROGRADE", "STATIONARY")
ASPECT_KINDS: tuple[str, ...] = (
    "CONJUNCTION",
    "SEMISEXTILE",
    "SEXTILE",
    "SQUARE",
    "TRINE",
    "QUINCUNX",
    "OPPOSITION",
)
TRANSIT_EVENT_KINDS: tuple[str, ...] = (
    "RASHI_INGRESS",
    "RASHI_EGRESS",
    "NAKSHATRA_INGRESS",
    "NAKSHATRA_EGRESS",
    "PADA_INGRESS",
    "PADA_EGRESS",
    "STATION_RETROGRADE",
    "STATION_DIRECT",
)
ECLIPSE_KINDS: tuple[str, ...] = ("SOLAR", "LUNAR")
ECLIPSE_CLASSIFICATIONS: tuple[str, ...] = (
    "TOTAL",
    "PARTIAL",
    "ANNULAR",
    "HYBRID",
    "PENUMBRAL",
)
#: ``relative_house(<BODY>, <REF>)`` reference set — every body plus the
#: lagna/ascendant anchors (ADR-012: extended from the v1.0.0 set so the
#: Phaladīpikā Sakata/Kesari rules can count houses from any graha).
RELATIVE_HOUSE_REFS: tuple[str, ...] = (
    "LAGNA",
    "ASC",
    *BODY_IDS,
)

#: Natural benefic/malefic classification (BPHS ch. 3 v. 11) — value order is
#: the deterministic enum order; ``NEUTRAL`` covers Mercury (benefic unless it
#: joins a malefic, per the same verse).
PLANET_NATURES: tuple[str, ...] = ("BENEFIC", "MALEFIC", "NEUTRAL")

#: Parashari dignity scale (BPHS ch. 3 v. 49-55) — ordered strongest first;
#: ``MULATRIKONA`` is checked before ``OWN`` because the moolatrikona sign is
#: always also an own sign.
DIGNITY_STATES: tuple[str, ...] = (
    "EXALTED",
    "MULATRIKONA",
    "OWN",
    "FRIEND",
    "NEUTRAL",
    "ENEMY",
    "DEBILITATED",
)

#: Classical aspect strength by house position (BPHS ch. 26 v. 2-5).
ASPECT_STRENGTHS: tuple[str, ...] = ("QUARTER", "HALF", "THREE_QUARTER", "FULL")

#: Aspect strength per aspected-house position (BPHS ch. 26 v. 2-5 /
#: Phaladīpikā ch. 2 v. 23): a planet casts a quarter glance on its 3rd/10th,
#: half on the 5th/9th, three-quarters on the 4th/8th and a full glance on
#: the 7th. Mirrors the ``facts`` catalog tables (a conformance test asserts
#: equality); pinned here so the evaluator resolves ``pair(A,B).aspect_strength``
#: directionally from ``relative_houses`` without a registry (ADR-012).
ASPECT_POSITION_STRENGTHS: dict[str, tuple[int, ...]] = {
    "QUARTER": (3, 10),
    "HALF": (5, 9),
    "THREE_QUARTER": (4, 8),
    "FULL": (7,),
}

#: Full-strength special aspects (BPHS ch. 26 v. 2-5): Saturn on the 3rd/10th,
#: Jupiter on the 5th/9th, Mars on the 4th/8th.
SPECIAL_ASPECT_POSITIONS: dict[str, tuple[int, ...]] = {
    "SATURN": (3, 10),
    "JUPITER": (5, 9),
    "MARS": (4, 8),
}

#: value_type -> ordered value tuple (enum-ordered strings support LT/GTE etc.)
_ORDERED_TUPLES: dict[str, tuple[str, ...]] = {
    "rashi": RASHI_IDS,
    "nakshatra": NAKSHATRA_IDS,
    "body": BODY_IDS,
    "retrograde": RETROGRADE_STATES,
    "aspect": ASPECT_KINDS,
    "transit_kind": TRANSIT_EVENT_KINDS,
    "eclipse_kind": ECLIPSE_KINDS,
    "eclipse_classification": ECLIPSE_CLASSIFICATIONS,
    "nature": PLANET_NATURES,
    "dignity": DIGNITY_STATES,
    "aspect_strength": ASPECT_STRENGTHS,
}

#: value_type -> allowed scalar values
_VALUE_SETS: dict[str, frozenset[str]] = {
    name: frozenset(values) for name, values in _ORDERED_TUPLES.items()
}

#: value types that permit ordering ops (numeric or enum-ordered strings).
#: The derived knowledge classifications ``nature``/``dignity``/
#: ``aspect_strength`` are categorical facts (EQ/IN only) even though their
#: value sets are ordered for deterministic display — ordering is not part of
#: their classical semantics (ADR-012).
ORDERED_VALUE_TYPES: frozenset[str] = frozenset(
    {
        "rashi",
        "nakshatra",
        "body",
        "retrograde",
        "aspect",
        "transit_kind",
        "eclipse_kind",
        "eclipse_classification",
        "float",
        "pada",
        "relative_house",
    }
)

# --------------------------------------------------------------------------- #
# Vocabulary path table (SPEC §6.2)
# --------------------------------------------------------------------------- #

#: Template path -> (value_type, multi). ``FACT_VOCABULARY`` is the pinned
#: contract; the parser resolves concrete paths against it.
FACT_VOCABULARY: dict[str, tuple[str, bool]] = {
    "planet(<BODY>).rashi": ("rashi", False),
    "planet(<BODY>).nakshatra": ("nakshatra", False),
    "planet(<BODY>).pada": ("pada", False),
    "planet(<BODY>).degree_in_rashi": ("float", False),
    "planet(<BODY>).retrograde": ("retrograde", False),
    "lagna.rashi": ("rashi", False),
    "lagna.nakshatra": ("nakshatra", False),
    "lagna.pada": ("pada", False),
    "bhava(<N>).house_lord": ("body", False),
    "bhava(<N>).occupants": ("body", True),
    "relative_house(<BODY>, <REF>)": ("relative_house", False),
    "pair(<A>,<B>).conjunction": ("bool", False),
    "pair(<A>,<B>).separation_deg": ("float", False),
    "pair(<A>,<B>).aspects": ("aspect", True),
    "pair(<A>,<B>).aspect_strength": ("aspect_strength", False),
    "planet(<BODY>).nature": ("nature", False),
    "planet(<BODY>).dignity": ("dignity", False),
    "planet(<BODY>).combusted": ("bool", False),
    "transit(<BODY>).kind": ("transit_kind", True),
    "eclipse.kind": ("eclipse_kind", True),
    "eclipse.classification": ("eclipse_classification", True),
}

#: (root, field) -> (value_type, multi, per-arg types). Arg types: "body",
#: "int", "int_or_body", "ref". ``relative_house`` is field-less and allows a
#: 1-arg (REF defaults to LAGNA) or 2-arg form (SPEC §6.2 supersession #10).
_VOCAB: dict[tuple[str, str], tuple[str, bool, tuple[str, ...]]] = {
    ("planet", "rashi"): ("rashi", False, ("body",)),
    ("planet", "nakshatra"): ("nakshatra", False, ("body",)),
    ("planet", "pada"): ("pada", False, ("body",)),
    ("planet", "degree_in_rashi"): ("float", False, ("body",)),
    ("planet", "retrograde"): ("retrograde", False, ("body",)),
    ("lagna", "rashi"): ("rashi", False, ()),
    ("lagna", "nakshatra"): ("nakshatra", False, ()),
    ("lagna", "pada"): ("pada", False, ()),
    ("bhava", "house_lord"): ("body", False, ("int_or_body",)),
    ("bhava", "occupants"): ("body", True, ("int_or_body",)),
    ("relative_house", ""): ("relative_house", False, ("body", "ref")),
    ("pair", "conjunction"): ("bool", False, ("body", "body")),
    ("pair", "separation_deg"): ("float", False, ("body", "body")),
    ("pair", "aspects"): ("aspect", True, ("body", "body")),
    ("pair", "aspect_strength"): ("aspect_strength", False, ("body", "body")),
    ("planet", "nature"): ("nature", False, ("body",)),
    ("planet", "dignity"): ("dignity", False, ("body",)),
    ("planet", "combusted"): ("bool", False, ("body",)),
    ("transit", "kind"): ("transit_kind", True, ("body",)),
    ("eclipse", "kind"): ("eclipse_kind", True, ()),
    ("eclipse", "classification"): ("eclipse_classification", True, ()),
}

#: Domain-section requirements (SPEC §6.4).
DOMAIN_REQUIREMENTS: dict[RuleDomain, tuple[str, ...]] = {
    RuleDomain.KARAKA: ("planets",),
    RuleDomain.BHAVA_MEANING: ("planets",),
    RuleDomain.DRISHTI: ("pairs",),
    RuleDomain.YOGA_DEFINITION: ("planets",),
    RuleDomain.NAKSHATRA_CHARACTER: ("planets",),
    RuleDomain.DASHA_APPLICATION: ("planets",),
    RuleDomain.GOCHAR_SIGNIFICATION: ("transits",),
    RuleDomain.ECLIPSE_SIGNIFICATION: ("eclipses",),
    RuleDomain.GENERAL: ("planets",),
}

_PATH_RE = re.compile(r"^([a-z_]+)(?:\(([^)]*)\))?(?:\.([a-z_]+))?$")


@dataclass(frozen=True)
class PathSpec:
    """A parsed, validated fact-vocabulary path."""

    root: str
    field: str
    args: tuple[object, ...]
    value_type: str
    multi: bool


def parse_path(path: str) -> PathSpec:
    """Parse and validate a fact-vocabulary path; raises ``RuleSchemaError``.

    Grammar (SPEC §6.2): ``root(args...).field``; ``relative_house(...)`` is
    field-less. A malformed path or unknown field is a load-time error.
    """
    match = _PATH_RE.match(path.strip())
    if match is None:
        raise RuleSchemaError(f"malformed vocabulary path: {path!r}")
    root, args_text, field = match.group(1), match.group(2), match.group(3) or ""

    entry = _VOCAB.get((root, field))
    if entry is None:
        raise RuleSchemaError(f"unknown vocabulary path: {path!r}")
    value_type, multi, arg_types = entry

    raw_args: tuple[str, ...] = ()
    if args_text is not None and args_text.strip():
        raw_args = tuple(part.strip() for part in args_text.split(","))
    if arg_types:
        # relative_house may omit REF (defaults to LAGNA — pinned, not inferred)
        allowed_counts = (
            {len(arg_types), len(arg_types) - 1} if root == "relative_house" else {len(arg_types)}
        )
        if len(raw_args) not in allowed_counts:
            raise RuleSchemaError(
                f"wrong argument count in path {path!r}: expected {len(arg_types)}"
            )
    elif len(raw_args) != 0:
        raise RuleSchemaError(f"path {path!r} takes no arguments, got {len(raw_args)}")
    if root == "relative_house" and len(raw_args) == 1:
        raw_args = (raw_args[0], "LAGNA")

    args: list[object] = []
    for index, arg_type in enumerate(arg_types):
        raw = raw_args[index]
        if arg_type == "body":
            if raw not in _VALUE_SETS["body"]:
                raise RuleSchemaError(f"unknown body {raw!r} in path {path!r}")
            args.append(raw)
        elif arg_type == "ref":
            if raw not in RELATIVE_HOUSE_REFS:
                raise RuleSchemaError(f"unknown reference {raw!r} in path {path!r}")
            args.append(raw)
        elif arg_type == "int":
            if not raw.isdigit() or not 1 <= int(raw) <= 12:
                raise RuleSchemaError(f"invalid house number {raw!r} in path {path!r}")
            args.append(int(raw))
        elif arg_type == "int_or_body":
            if raw in _VALUE_SETS["body"]:
                args.append(raw)
            elif raw.isdigit() and 1 <= int(raw) <= 12:
                args.append(int(raw))
            else:
                raise RuleSchemaError(
                    f"invalid bhava argument {raw!r} in path {path!r}: "
                    "expected a house number 1-12 or a body id"
                )
    return PathSpec(root, field, tuple(args), value_type, multi)


# --------------------------------------------------------------------------- #
# Literal validation
# --------------------------------------------------------------------------- #


def _validate_scalar(value_type: str, value: object) -> None:
    """Validate a scalar literal against a vocabulary value type."""
    if value_type == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuleSchemaError(f"literal {value!r} is not numeric for a float path")
        return
    if value_type == "bool":
        if not isinstance(value, bool):
            raise RuleSchemaError(f"literal {value!r} is not a boolean for a bool path")
        return
    if value_type in ("pada", "relative_house"):
        upper = 4 if value_type == "pada" else 12
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= upper:
            raise RuleSchemaError(
                f"literal {value!r} out of range for {value_type} path (1-{upper})"
            )
        return
    if not isinstance(value, str) or value not in _VALUE_SETS[value_type]:
        raise RuleSchemaError(f"literal {value!r} is not a valid {value_type} value")


def _validate_literal(spec: PathSpec, op: ConditionOp, value: object) -> None:
    """Validate a condition atom's literal against the path and operator."""
    if op is ConditionOp.EXISTS:
        if value is not None:
            raise RuleSchemaError("EXISTS is a presence test and requires value null")
        return
    if op in (ConditionOp.IN, ConditionOp.NOT_IN):
        if not isinstance(value, list) or not value:
            raise RuleSchemaError(f"{op.value} requires a non-empty list literal, got {value!r}")
        for item in value:
            _validate_scalar(spec.value_type, item)
        return
    if op in (ConditionOp.LT, ConditionOp.LTE, ConditionOp.GT, ConditionOp.GTE):
        if spec.multi:
            raise RuleSchemaError(
                f"ordering op {op.value} is invalid on multi-value path {spec.root}.{spec.field}"
            )
        if spec.value_type not in ORDERED_VALUE_TYPES:
            raise RuleSchemaError(
                f"ordering op {op.value} requires a numeric or enum-ordered "
                f"path, got {spec.value_type}"
            )
        _validate_scalar(spec.value_type, value)
        return
    # EQ / NEQ: scalar literal (single value on multi paths = membership test)
    _validate_scalar(spec.value_type, value)


def validate_condition(condition: RuleCondition) -> None:
    """Validate a condition tree; raises ``RuleSchemaError`` on any violation."""
    if condition.combiner is None:
        if condition.op is None or condition.path is None:
            raise RuleSchemaError("atom condition requires op and path")
        if condition.children:
            raise RuleSchemaError("atom condition must not have children")
        spec = parse_path(condition.path)
        _validate_literal(spec, condition.op, condition.value)
        return
    if condition.op is not None or condition.path is not None or condition.value is not None:
        raise RuleSchemaError(f"combiner {condition.combiner.value} must not carry op/path/value")
    if not condition.children:
        raise RuleSchemaError(f"combiner {condition.combiner.value} needs children")
    if condition.combiner is ConditionCombiner.NOT and len(condition.children) != 1:
        raise RuleSchemaError("NOT requires exactly one child")
    for child in condition.children:
        validate_condition(child)


# --------------------------------------------------------------------------- #
# Evaluation (SPEC §6.1)
# --------------------------------------------------------------------------- #

_MISSING = object()


def _values_equal(actual: object, literal: object) -> bool:
    """Type-aware value equality (bool never equals a number)."""
    if isinstance(literal, bool) or isinstance(actual, bool):
        return type(actual) is bool and type(literal) is bool and actual == literal
    if isinstance(literal, (int, float)) and isinstance(actual, (int, float)):
        return actual == literal
    return actual == literal


def _compare(actual: object, literal: object, op: ConditionOp, value_type: str) -> bool:
    """Ordering comparison; unknown/missing values compare as False."""
    if value_type == "float":
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return False
        left, right = float(cast(Any, actual)), float(cast(Any, literal))
    elif value_type in ("pada", "relative_house"):
        if isinstance(actual, bool) or not isinstance(actual, int):
            return False
        left, right = actual, cast(int, literal)
    else:
        order = _ORDERED_TUPLES[value_type]
        if actual not in order or not isinstance(literal, str) or literal not in order:
            return False
        left, right = order.index(actual), order.index(literal)
    if op is ConditionOp.LT:
        return left < right
    if op is ConditionOp.LTE:
        return left <= right
    if op is ConditionOp.GT:
        return left > right
    return left >= right


def _list_contains(actual: object, literal: object) -> bool:
    """Multi-value membership: does the list contain the literal value?"""
    if not isinstance(actual, list):
        return False
    return any(_values_equal(item, literal) for item in actual)


def _any_literal_in_list(actual: object, literals: list[object]) -> bool:
    """Multi-value ``IN``: is any literal present in the list?"""
    if not isinstance(actual, list):
        return False
    return any(_values_equal(item, literal) for item in actual for literal in literals)


def _resolve_relative_house(snapshot: dict[str, Any], body: str, ref: str) -> object:
    section = snapshot.get("relative_houses")
    if not isinstance(section, dict):
        return _MISSING
    ref_map = section.get(ref)
    if isinstance(ref_map, dict):
        return ref_map.get(body, _MISSING)
    if ref == "LAGNA":  # flat {body: house} form is a LAGNA-reference snapshot
        return section.get(body, _MISSING)
    return _MISSING


def _aspect_strength_from_snapshot(
    snapshot: dict[str, Any], aspecter: str, aspected: str
) -> object:
    """Directional classical aspect strength: ``aspecter``'s glance on
    ``aspected``, derived from the snapshot's ``relative_houses`` (ADR-012).

    ``pair(A,B).aspect_strength`` is *directional* (A aspects B), so it cannot
    be stored on the order-insensitive ``pairs`` entries; it is computed here
    from the house of B from A plus the pinned doctrine. Returns ``_MISSING``
    when the house or an aspect is absent (the atom then reads **False**).
    """
    relative = snapshot.get("relative_houses")
    if not isinstance(relative, dict):
        return _MISSING
    ref_map = relative.get(aspecter)
    if not isinstance(ref_map, dict):
        return _MISSING
    house = ref_map.get(aspected)
    if not isinstance(house, int):
        return _MISSING
    if aspecter in SPECIAL_ASPECT_POSITIONS and house in SPECIAL_ASPECT_POSITIONS[aspecter]:
        return "FULL"
    for strength, positions in ASPECT_POSITION_STRENGTHS.items():
        if house in positions:
            return strength
    return _MISSING


def _resolve_path(spec: PathSpec, snapshot: dict[str, Any]) -> object:
    """Resolve a validated path against the canonical fact snapshot."""
    root, field, args = spec.root, spec.field, spec.args
    if root == "planet":
        section = snapshot.get("planets")
        if not isinstance(section, list):
            return _MISSING
        for entry in section:
            if isinstance(entry, dict) and entry.get("body") == args[0]:
                return entry.get(field, _MISSING)
        return _MISSING
    if root == "lagna":
        section = snapshot.get("lagna")
        if not isinstance(section, dict):
            return _MISSING
        return section.get(field, _MISSING)
    if root == "bhava":
        section = snapshot.get("bhavas")
        if not isinstance(section, list):
            return _MISSING
        target: object = args[0]
        for entry in section:
            if not isinstance(entry, dict):
                continue
            if isinstance(target, int):
                if entry.get("house_number") == target:
                    return entry.get(field, _MISSING)
            else:
                occupants = entry.get("occupants")
                if isinstance(occupants, list) and target in occupants:
                    return entry.get(field, _MISSING)
        return _MISSING
    if root == "relative_house":
        return _resolve_relative_house(snapshot, cast(str, args[0]), cast(str, args[1]))
    if root == "pair":
        section = snapshot.get("pairs")
        if not isinstance(section, list):
            return _MISSING
        first, second = cast(str, args[0]), cast(str, args[1])
        for entry in section:
            if not isinstance(entry, dict):
                continue
            pair = {entry.get("first"), entry.get("second")}
            if pair == {first, second}:
                if field == "aspect_strength":
                    return _aspect_strength_from_snapshot(snapshot, first, second)
                return entry.get(field, _MISSING)
        return _MISSING
    if root == "transit":
        section = snapshot.get("transits")
        if not isinstance(section, dict):
            return _MISSING
        return section.get(cast(str, args[0]), _MISSING)
    if root == "eclipse":
        section = snapshot.get("eclipses")
        if not isinstance(section, dict):
            return _MISSING
        return section.get(field, _MISSING)
    return _MISSING


def evaluate_atom(condition: RuleCondition, snapshot: dict[str, Any]) -> bool:
    """Evaluate one validated atom against the snapshot (SPEC §6.1)."""
    assert condition.path is not None and condition.op is not None
    spec = parse_path(condition.path)
    actual = _resolve_path(spec, snapshot)
    if actual is _MISSING:
        return False
    op = condition.op
    if op is ConditionOp.EXISTS:
        if spec.multi:
            return isinstance(actual, list) and len(actual) > 0
        return actual is not None
    if op is ConditionOp.EQ:
        return (
            _list_contains(actual, condition.value)
            if spec.multi
            else _values_equal(actual, condition.value)
        )
    if op is ConditionOp.NEQ:
        return (
            not _list_contains(actual, condition.value)
            if spec.multi
            else not _values_equal(actual, condition.value)
        )
    if op is ConditionOp.IN:
        literals = cast(list[object], condition.value)
        if spec.multi:
            return _any_literal_in_list(actual, literals)
        return any(_values_equal(actual, literal) for literal in literals)
    if op is ConditionOp.NOT_IN:
        literals = cast(list[object], condition.value)
        if spec.multi:
            return not _any_literal_in_list(actual, literals)
        return not any(_values_equal(actual, literal) for literal in literals)
    return _compare(actual, condition.value, op, spec.value_type)


def evaluate(condition: RuleCondition, snapshot: dict[str, Any]) -> bool:
    """Evaluate a condition tree against the snapshot — pure, deterministic."""
    if condition.combiner is None:
        return evaluate_atom(condition, snapshot)
    if condition.combiner is ConditionCombiner.ALL:
        return all(evaluate(child, snapshot) for child in condition.children)
    if condition.combiner is ConditionCombiner.ANY:
        return any(evaluate(child, snapshot) for child in condition.children)
    return not evaluate(condition.children[0], snapshot)


# --------------------------------------------------------------------------- #
# Domain-section requirements (SPEC §6.4)
# --------------------------------------------------------------------------- #


def _section_present(snapshot: dict[str, Any], section: str) -> bool:
    value = snapshot.get(section)
    if section in ("planets", "pairs"):
        return isinstance(value, list) and len(value) > 0
    if section == "transits":
        return isinstance(value, dict) and len(value) > 0
    if section == "eclipses":
        if not isinstance(value, dict):
            return False
        kinds = value.get("kinds")
        classifications = value.get("classifications")
        return (isinstance(kinds, list) and len(kinds) > 0) or (
            isinstance(classifications, list) and len(classifications) > 0
        )
    return value is not None


def missing_sections(snapshot: dict[str, Any], domains: set[RuleDomain]) -> list[str]:
    """Sections required by ``domains`` that the snapshot lacks (deterministic)."""
    required: list[str] = []
    for domain in sorted(domains, key=lambda item: item.value):
        for section in DOMAIN_REQUIREMENTS[domain]:
            if section not in required and not _section_present(snapshot, section):
                required.append(section)
    return required
