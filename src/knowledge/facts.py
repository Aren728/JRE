"""Classical facts layer (FACT_VOCABULARY v1.1.0, ADR-012).

The derived-fact paths added in v1.1.0 — ``planet(<BODY>).nature``,
``planet(<BODY>).dignity``, ``planet(<BODY>).combusted`` and
``pair(<A>,<B>).aspect_strength`` — are *knowledge facts*: classical tables
carried as versioned, checksummed, provenance-pinned data in
``datasets/knowledge/facts/facts.json`` plus a pure derivation step that
consumes JRE-003 public outputs already present in a normalized snapshot
(planet rashis, Sun-separation pairs, relative houses).

Boundary (ADR-012): JRE-003 performs no benefic/malefic, dignity, combustion
or classical-drishti computation (its ``__init__`` forbids them). Everything
here is derived *from* JRE-003 outputs by JRE-004, so ``src/jyotish`` is
untouched. This module imports stdlib only (like ``schema.py``), keeping the
knowledge layer within its import boundary (ADR-007); ``synthesis.py`` is the
module that touches JRE-003 objects.

Determinism: the derivation is a pure function of the snapshot dict and the
immutable ``FactsRegistry``; a missing input (e.g. no ``SUN``-separation pair)
leaves the derived field absent, and a missing fact makes the consuming rule
atom **False** — never an exception and never a wrongly-fired rule.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import CatalogIntegrityError, RuleSchemaError
from .models import ProvenanceRef, read_catalog_file

#: Version of the authored facts catalog (ADR-012).
FACTS_CATALOG_VERSION = "1.0.0"

DEFAULT_FACTS_PATH: Path = Path("datasets/knowledge/facts/facts.json")

_FACT_IDS = frozenset(
    {
        "nature",
        "exaltation",
        "debilitation",
        "own_signs",
        "moolatrikona",
        "combustion_degrees",
        "natural_friendship",
        "rashi_lords",
        "aspect_strength_positions",
        "special_aspects",
    }
)


@dataclass(frozen=True)
class FactsRegistry:
    """Immutable parsed classical tables with their provenance (ADR-012)."""

    natures: dict[str, str]
    exaltation: dict[str, str]
    debilitation: dict[str, str]
    own_signs: dict[str, tuple[str, ...]]
    moolatrikona: dict[str, str]
    combustion_degrees: dict[str, dict[str, float]]
    friendship: dict[str, dict[str, tuple[str, ...]]]
    rashi_lords: dict[str, str]
    aspect_strength_positions: dict[str, tuple[int, ...]]
    special_aspects: dict[str, tuple[int, ...]]
    provenance: dict[str, ProvenanceRef]
    catalog_version: str


# --------------------------------------------------------------------------- #
# Catalog loading
# --------------------------------------------------------------------------- #


def _parse_table(values: Any, fact_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(values, dict):
        raise RuleSchemaError(f"facts entry {fact_id!r}: table must be an object")
    return values


def load_facts(
    path: str | Path | None = None,
    *,
    verify_checksums: bool = True,
    pin: str | None = None,
) -> FactsRegistry:
    """Load and validate the authored facts catalog (checksummed, versioned).

    ``pin`` is an exact-match version pin; mismatch raises
    ``CatalogIntegrityError``. Every fact entry must carry full provenance
    (source/chapter/verse/edition) and a recognized ``fact_id``.
    """
    catalog_path = Path(path) if path is not None else DEFAULT_FACTS_PATH
    try:
        document, digest = read_catalog_file(catalog_path)
    except OSError as exc:
        raise CatalogIntegrityError(f"cannot read catalog {catalog_path}: {exc}") from exc
    except ValueError as exc:
        raise CatalogIntegrityError(f"invalid JSON in catalog {catalog_path}: {exc}") from exc

    if verify_checksums:
        expected = document.get("checksum_sha256")
        if expected != digest:
            raise CatalogIntegrityError(
                f"checksum mismatch for {catalog_path}: expected {expected!r}, got {digest!r}"
            )
    catalog_id = document.get("catalog_id")
    if catalog_id != "facts":
        raise CatalogIntegrityError(
            f"catalog_id mismatch in {catalog_path}: expected 'facts', got {catalog_id!r}"
        )
    version = str(document.get("catalog_version", FACTS_CATALOG_VERSION))
    if pin is not None and version != pin:
        raise CatalogIntegrityError(
            f"version-pin mismatch for {catalog_path}: expected {pin!r}, got {version!r}"
        )

    entries = document.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise CatalogIntegrityError(f"catalog {catalog_path} has no fact entries")

    tables: dict[str, dict[str, Any]] = {}
    provenance: dict[str, ProvenanceRef] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuleSchemaError(f"facts entry must be an object, got {entry!r}")
        fact_id = entry.get("fact_id")
        if fact_id not in _FACT_IDS:
            raise RuleSchemaError(f"unknown fact_id {fact_id!r}")
        if fact_id in tables:
            raise RuleSchemaError(f"duplicate fact_id {fact_id!r}")
        tables[fact_id] = _parse_table(entry.get("values"), fact_id, entry)
        provenance[fact_id] = _ref_from_entry(fact_id, entry)

    def _body_table(fact_id: str) -> dict[str, str]:
        return {str(k): str(v) for k, v in tables[fact_id].items()}

    def _own_signs() -> dict[str, tuple[str, ...]]:
        return {
            str(k): tuple(str(item) for item in v)
            for k, v in tables["own_signs"].items()
        }

    def _combustion() -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for body, raw in tables["combustion_degrees"].items():
            if not isinstance(raw, dict):
                raise RuleSchemaError(
                    f"combustion_degrees[{body!r}] must be an object with direct/retrograde"
                )
            result[str(body)] = {
                "direct": float(raw["direct"]),
                # absent retrograde value -> same threshold as direct (a missing
                # table column must never make the body *more* combust)
                "retrograde": (
                    float(raw["retrograde"])
                    if raw.get("retrograde") is not None
                    else float(raw["direct"])
                ),
            }
        return result

    def _friendship() -> dict[str, dict[str, tuple[str, ...]]]:
        result: dict[str, dict[str, tuple[str, ...]]] = {}
        for body, raw in tables["natural_friendship"].items():
            if not isinstance(raw, dict):
                raise RuleSchemaError(f"natural_friendship[{body!r}] must be an object")
            result[str(body)] = {
                key: tuple(str(item) for item in raw.get(key, []))
                for key in ("friends", "enemies", "neutral")
            }
        return result

    def _positions(fact_id: str) -> dict[str, tuple[int, ...]]:
        return {
            str(k): tuple(int(item) for item in v)
            for k, v in tables[fact_id].items()
        }

    return FactsRegistry(
        natures=_body_table("nature"),
        exaltation=_body_table("exaltation"),
        debilitation=_body_table("debilitation"),
        own_signs=_own_signs(),
        moolatrikona=_body_table("moolatrikona"),
        combustion_degrees=_combustion(),
        friendship=_friendship(),
        rashi_lords=_body_table("rashi_lords"),
        aspect_strength_positions=_positions("aspect_strength_positions"),
        special_aspects=_positions("special_aspects"),
        provenance=provenance,
        catalog_version=version,
    )


def _ref_from_entry(fact_id: str, entry: dict[str, Any]) -> ProvenanceRef:
    raw = entry.get("provenance")
    if not isinstance(raw, dict):
        raise RuleSchemaError(f"facts entry {fact_id!r} is missing provenance")
    try:
        source_id = str(raw["source_id"])
    except (KeyError, TypeError) as exc:
        raise RuleSchemaError(f"facts entry {fact_id!r} missing source_id: {exc!r}") from exc

    def _opt(key: str) -> str | None:
        value = raw.get(key)
        return None if value is None else str(value)

    ref = ProvenanceRef(
        source_id=source_id,
        chapter=_opt("chapter"),
        verse_start=_opt("verse_start"),
        verse_end=_opt("verse_end"),
        edition_id=_opt("edition_id"),
        commentary=_opt("commentary"),
    )
    if ref.chapter is None or ref.verse_start is None or ref.edition_id is None:
        raise RuleSchemaError(
            f"facts entry {fact_id!r} must pin source/chapter/verse/edition (ADR-012)"
        )
    return ref


# --------------------------------------------------------------------------- #
# Pure derivation (facts are derived from JRE-003 outputs + the tables)
# --------------------------------------------------------------------------- #


def derive_nature(facts: FactsRegistry, body: str) -> str:
    """Natural benefic/malefic classification (BPHS ch. 3 v. 11)."""
    return facts.natures[body]


def derive_dignity(facts: FactsRegistry, body: str, rashi: str) -> str | None:
    """Parashari dignity of ``body`` in ``rashi``, or ``None`` for bodies the
    classical tables do not grade (the nodes — BPHS ch. 3 grades seven grahas
    only)."""
    if body not in facts.exaltation:
        return None
    if rashi == facts.exaltation[body]:
        return "EXALTED"
    if rashi == facts.debilitation[body]:
        return "DEBILITATED"
    if rashi == facts.moolatrikona[body]:
        return "MULATRIKONA"
    if rashi in facts.own_signs[body]:
        return "OWN"
    lord = facts.rashi_lords[rashi]
    relation = facts.friendship[body]
    if lord in relation["friends"]:
        return "FRIEND"
    if lord in relation["enemies"]:
        return "ENEMY"
    return "NEUTRAL"


def derive_combusted(
    facts: FactsRegistry, body: str, retrograde: str, separation_from_sun_deg: float
) -> bool:
    """Combustion against the Sun (BPHS ch. 7 v. 28-29 table).

    ``separation_from_sun_deg`` is the shortest angular separation (as in the
    snapshot ``pair(SUN, <BODY>).separation_deg``). The nodes are never
    combust; motion (direct/retrograde) selects the table column.
    """
    if body not in facts.combustion_degrees:
        return False
    table = facts.combustion_degrees[body]
    threshold = table["retrograde"] if retrograde == "RETROGRADE" else table["direct"]
    return separation_from_sun_deg <= threshold


def derive_aspect_strength(
    facts: FactsRegistry, aspecter: str, aspected_house: int
) -> str | None:
    """Classical strength of ``aspecter``'s glance on a body in its
    ``aspected_house`` (BPHS ch. 26 v. 2-5 / Phaladīpikā ch. 2 v. 23).

    Returns ``None`` when the position carries no classical aspect. Saturn,
    Jupiter and Mars cast *full* aspects on their special positions (3rd/10th,
    5th/9th, 4th/8th respectively).
    """
    if aspecter in facts.special_aspects and aspected_house in facts.special_aspects[aspecter]:
        return "FULL"
    for strength, positions in facts.aspect_strength_positions.items():
        if aspected_house in positions:
            return strength
    return None


# --------------------------------------------------------------------------- #
# Snapshot enrichment (called by normalize_snapshot when facts are provided)
# --------------------------------------------------------------------------- #


def enrich_snapshot(snapshot: dict[str, Any], facts: FactsRegistry) -> dict[str, Any]:
    """Add the v1.1.0 derived facts to a normalized snapshot, in place and
    deterministically.

    - ``planets[]`` entries gain ``nature``, ``dignity`` and ``combusted``.
      Combustion needs the ``pair(SUN, <BODY>)`` separation; bodies outside
      the classical table (the Sun itself, the nodes) are never combust and
      bodies without a SUN pair default to **False** — absent data must never
      fire a rule.
    - ``pairs[]`` entries gain ``aspect_strength`` only when a classical
      aspect exists (house position from the aspecter; needs the
      ``relative_houses`` section).
    """
    planets = snapshot.get("planets")
    if isinstance(planets, list):
        pairs = snapshot.get("pairs")
        sun_separation: dict[str, float] = {}
        if isinstance(pairs, list):
            for entry in pairs:
                if not isinstance(entry, dict):
                    continue
                first = entry.get("first")
                second = entry.get("second")
                if first == "SUN" and second != "SUN":
                    sun_separation[str(second)] = float(entry["separation_deg"])
                elif second == "SUN" and first != "SUN":
                    sun_separation[str(first)] = float(entry["separation_deg"])
        for entry in planets:
            if not isinstance(entry, dict):
                continue
            body = str(entry.get("body", ""))
            if body in facts.natures:
                entry["nature"] = facts.natures[body]
            dignity = derive_dignity(facts, body, str(entry.get("rashi", "")))
            if dignity is not None:
                entry["dignity"] = dignity
            if body in facts.combustion_degrees:
                entry["combusted"] = derive_combusted(
                    facts,
                    body,
                    str(entry.get("retrograde", "DIRECT")),
                    sun_separation.get(body, float("inf")),
                )
            else:
                entry["combusted"] = False
    return snapshot


# --------------------------------------------------------------------------- #
# Deterministic checksum helper (mirrors models.canonical_catalog_json)
# --------------------------------------------------------------------------- #


def facts_checksum(document: dict[str, Any]) -> str:
    """SHA-256 of a facts-catalog document with ``checksum_sha256`` removed."""
    body = {key: value for key, value in document.items() if key != "checksum_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
