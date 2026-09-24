"""JRS-091: Deterministic Golden-State Validation.

Intermediate hash contract for the JRE pipeline. Each deterministic
pipeline checkpoint (chart, JRE facts, dasha, yogas, report, ...) is
serialized to canonical JSON and hashed with the same canonicalization
rules as the prediction packet store (``storage._canonicalize_floats``:
round-6 floats, tuple→list, sorted keys, compact separators, SHA-256).

A :class:`GoldenStateManifest` records the ordered stage hashes for one
fixture under one engine version and is stored as a golden fixture
(``tests/fixtures/golden_states/<fixture_id>.json``).
:class:`GoldenStateValidator` recomputes hashes from live pipeline
payloads and raises :class:`GoldenStateMismatchError` on the first
divergence — catching non-determinism at stage granularity instead of
only at final output.

Usage::

    manifest = build_manifest(
        engine_version="v1.0.0-beta",
        fixture_id="chart_001_pilot",
        stage_payloads={"chart": chart.to_dict(), "jre_facts": facts},
    )
    manifest.to_dict()  # → tests/fixtures/golden_states/chart_001_pilot.json

    GoldenStateValidator(manifest).verify_all(
        {"chart": chart.to_dict(), "jre_facts": facts}
    )
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

#: Version of THIS hash-contract schema (bump on any breaking change to
#: the canonicalization rules or manifest shape, and regenerate fixtures).
GOLDEN_STATE_SCHEMA_VERSION = "1.0.0"

#: Ordered canonical pipeline checkpoint ids. Known ids always appear in
#: this order inside a manifest; unknown custom ids follow, sorted
#: alphabetically (the ordering must stay deterministic for fixtures).
CANONICAL_STAGE_IDS: tuple[str, ...] = (
    "chart",  # natal chart: planets, houses, ayanamsa (JRE-003/JRE-005)
    "jre_facts",  # JRE fact extraction (dignities, aspects, balances)
    "dasha",  # Vimshottari periods and balances (JRE engine)
    "yogas",  # yoga evaluation results (JRS-075/076/077)
    "report",  # final synthesis / evaluation payload
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GoldenStateMismatchError(Exception):
    """A recomputed stage hash differs from the golden record."""


def _canonicalize_floats(obj: Any) -> Any:
    """Recursively canonicalize floats to 6-decimal precision.

    Mirrors ``jrs.validation.storage._canonicalize_floats`` so stage
    hashes and packet hashes share one float policy — prevents
    cross-platform / cross-Python serialization drift from producing
    false mismatches. Tuples become lists (JSON arrays).
    """
    if isinstance(obj, bool):  # bool is an int subclass; keep as-is
        return obj
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _canonicalize_floats(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize_floats(v) for v in obj]
    return obj


def canonical_payload(payload: Any) -> str:
    """Serialize a stage payload to canonical JSON text.

    Canonical form: floats rounded to 6 decimals, tuples as lists, dict
    keys sorted, compact separators. Identical semantic payloads always
    produce byte-identical text regardless of construction order.
    """
    return json.dumps(
        _canonicalize_floats(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def stage_hash(stage_id: str, payload: Any) -> str:
    """Compute the golden-state hash for one pipeline stage.

    The schema version and stage id are folded into the preimage so
    identical payloads at different stages (or under different contract
    versions) can never collide — domain separation.
    """
    preimage = f"{GOLDEN_STATE_SCHEMA_VERSION}|{stage_id}|{canonical_payload(payload)}"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def _stage_sort_key(stage_id: str) -> tuple[int, str]:
    """Known canonical stages sort first (in declaration order), then
    unknown ids alphabetically."""
    try:
        return (0, f"{CANONICAL_STAGE_IDS.index(stage_id):04d}")
    except ValueError:
        return (1, stage_id)


@dataclass(frozen=True)
class StageRecord:
    """One recorded pipeline checkpoint: stage id + payload hash."""

    stage_id: str
    payload_hash: str


@dataclass(frozen=True)
class GoldenStateManifest:
    """Ordered stage hashes for one fixture under one engine version.

    Persisted as ``tests/fixtures/golden_states/<fixture_id>.json`` via
    :meth:`to_dict` / :meth:`from_dict`.
    """

    engine_version: str
    fixture_id: str
    schema_version: str = GOLDEN_STATE_SCHEMA_VERSION
    stages: tuple[StageRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (deterministic key order
        is enforced by ``json.dumps(sort_keys=True)`` at write time)."""
        return {
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "fixture_id": self.fixture_id,
            "stages": [
                {"stage_id": s.stage_id, "payload_hash": s.payload_hash}
                for s in self.stages
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoldenStateManifest:
        """Deserialize a manifest dict; raises ``ValueError`` on shape or
        schema-version mismatch (callers regenerate fixtures on bump)."""
        try:
            schema_version = str(data["schema_version"])
            engine_version = str(data["engine_version"])
            fixture_id = str(data["fixture_id"])
            raw_stages = data["stages"]
        except KeyError as exc:
            raise ValueError(f"golden-state manifest missing field: {exc}") from exc
        if schema_version != GOLDEN_STATE_SCHEMA_VERSION:
            raise ValueError(
                f"golden-state schema mismatch: manifest={schema_version!r}, "
 f"contract={GOLDEN_STATE_SCHEMA_VERSION!r} — regenerate fixtures"
            )
        if not isinstance(raw_stages, list):
            raise ValueError("golden-state manifest 'stages' must be a list")
        stages: list[StageRecord] = []
        for raw in raw_stages:
            if not isinstance(raw, dict) or "stage_id" not in raw or "payload_hash" not in raw:
                raise ValueError(f"malformed stage record: {raw!r}")
            stage_id = str(raw["stage_id"])
            payload_hash = str(raw["payload_hash"])
            if not _HEX64.match(payload_hash):
                raise ValueError(
 f"stage {stage_id!r}: payload_hash must be 64 lowercase hex chars, "
 f"got {payload_hash!r}"
                )
            stages.append(StageRecord(stage_id=stage_id, payload_hash=payload_hash))
        return cls(
            engine_version=engine_version,
            fixture_id=fixture_id,
            schema_version=schema_version,
            stages=tuple(stages),
        )

    def stage_ids(self) -> tuple[str, ...]:
        """Recorded stage ids in manifest order."""
        return tuple(s.stage_id for s in self.stages)

    def hash_of(self, stage_id: str) -> str:
        """Golden hash for a stage; ``KeyError`` if not recorded."""
        for record in self.stages:
            if record.stage_id == stage_id:
                return record.payload_hash
        raise KeyError(f"stage {stage_id!r} not recorded in golden manifest")


def build_manifest(
    engine_version: str,
    fixture_id: str,
    stage_payloads: dict[str, Any],
) -> GoldenStateManifest:
    """Build a :class:`GoldenStateManifest` from ordered stage payloads.

    Stages are hashed with :func:`stage_hash` and recorded in
    deterministic order: canonical stages first (declaration order),
    then custom ids alphabetically. Rebuilding from the same payloads
    always yields a byte-identical manifest.
    """
    if not stage_payloads:
        raise ValueError("golden-state manifest requires at least one stage payload")
    ordered_ids = sorted(stage_payloads, key=_stage_sort_key)
    stages = tuple(
        StageRecord(stage_id=stage_id, payload_hash=stage_hash(stage_id, stage_payloads[stage_id]))
        for stage_id in ordered_ids
    )
    return GoldenStateManifest(
        engine_version=engine_version,
        fixture_id=fixture_id,
        stages=stages,
    )


class GoldenStateValidator:
    """Recompute stage hashes against a golden manifest.

    Fails loudly (raises) on the first divergence so the failing stage
    pinpoints where determinism broke in the pipeline.
    """

    def __init__(self, manifest: GoldenStateManifest) -> None:
        self._manifest = manifest

    @property
    def manifest(self) -> GoldenStateManifest:
        return self._manifest

    def verify_stage(self, stage_id: str, payload: Any) -> None:
        """Verify one stage; raises on unknown stage or hash mismatch.

        Raises:
            KeyError: If ``stage_id`` is not recorded in the manifest.
            GoldenStateMismatchError: If the recomputed hash differs.
        """
        golden = self._manifest.hash_of(stage_id)  # KeyError if absent
        computed = stage_hash(stage_id, payload)
        if computed != golden:
            raise GoldenStateMismatchError(
                f"golden-state mismatch at stage {stage_id!r} "
                f"(fixture {self._manifest.fixture_id!r}, "
                f"engine {self._manifest.engine_version!r}): "
                f"golden={golden} computed={computed}"
            )

    def verify_all(self, stage_payloads: dict[str, Any]) -> tuple[str, ...]:
        """Verify every provided stage; returns verified stage ids in
        manifest order. Raises on the first mismatch. Stages recorded in
        the manifest but not provided are skipped (partial verification),
        and provided stages absent from the manifest raise ``KeyError``.
        """
        for stage_id in stage_payloads:
            self._manifest.hash_of(stage_id)  # unknown stage → KeyError
        verified = [
            record.stage_id
            for record in self._manifest.stages
            if record.stage_id in stage_payloads
        ]
        for stage_id in verified:
            self.verify_stage(stage_id, stage_payloads[stage_id])
        return tuple(verified)
