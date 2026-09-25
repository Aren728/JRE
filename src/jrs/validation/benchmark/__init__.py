"""Phase F4: Frozen Validation Benchmark Corpus.

Freezes the 30 development charts and 10 validation charts with immutable
inputs, canonical ground-truth event labels, and an explicit
open-world vs. closed-world target scope tag.

    dev (30)     -> golden_states provenance invariants + CI benchmark gate
    validation (10) -> gated by the same thresholds below

Run
---
    python scripts/run_benchmark_eval.py
    python scripts/run_benchmark_eval.py --manifest tests/fixtures/benchmark/corpus_manifest.json

CI gate (.github/workflows/ci.yml):
    benchmark-eval job -> fails on manifest hash mismatch or
    metric non-degradation below the Phase F3 baseline.

Evaluation protocol (canonical Phase F3 mapping)
------------------------------------------------
``evaluate_corpus()`` executes the frozen corpus through
:class:`jrs.validation.runner.HistoricalValidationRunner` (``run_batch``)
and scores every real ``KnownEvent`` exactly once from its
:class:`EventPredictionMatch` verdict, mirroring the Phase F3 error
attribution protocol (``scripts/error_attribution.py``):

- TP:  a relevant prediction matched the event and was not CANCELLED.
- FP:  the event had no formed relevant prediction, but the chart still
  produced at least one non-CANCELLED prediction (the engine asserted an
  activation the ground truth does not confirm). The runner's CANCELLED
  best-prediction FALSE_NEGATIVE verdicts map here.
- FN:  no relevant prediction and no non-CANCELLED prediction anywhere in
  the chart (a silent miss).

The runner's synthetic ``unmatched_<yoga>`` FALSE_POSITIVE entries carry
no ground-truth anchor and are excluded, exactly as the F3 protocol
scored real events only.

Micro-F1 pools the 120 event-level decisions with
``2*TP / (2*TP + FP + FN)`` — the formula behind the Phase F3 headline
(F1 = 0.744, recharacterized on the frozen corpus; see the BASELINE_*
constants). Macro-F1 is the unweighted mean of per-domain F1 across the
life domains present in the scored population.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jrs.validation.models import (
    BirthChart,
    BirthData,
    ChartValidationResult,
    EventDomain,
    EventPredictionMatch,
    KnownEvent,
    PredictionVerdict,
)
from jrs.validation.error_taxonomy import (
    ErrorKind,
    attribute_match,
    summarize_attributions,
)
from jrs.validation.runner import HistoricalValidationRunner

# Path resolution: this file lives at src/jrs/validation/benchmark/__init__.py,
# so the repository root is four parents up from the package directory.
REPO_ROOT = Path(__file__).resolve().parents[4]
DEV_DIR = REPO_ROOT / "tests" / "fixtures" / "benchmark" / "dev"
VAL_DIR = REPO_ROOT / "tests" / "fixtures" / "benchmark" / "validation"
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "benchmark" / "corpus_manifest.json"
SCHEMA_PATH = REPO_ROOT / "tests" / "fixtures" / "benchmark" / "schema" / "benchmark_corpus_schema.json"

# Phase F3 baseline, recharacterized on the frozen corpus through the
# canonical evaluation protocol below (TP=71, FP=31, FN=18 over 120
# frozen events -> F1 = 0.7435 ~= the 0.744 Phase F3 headline). The F1
# anchors the non-degradation gate; the companion metrics were measured
# on the frozen corpus, not assumed from legacy reports.
BASELINE_MACRO_F1 = 0.744
BASELINE_MICRO_F1 = 0.7435
BASELINE_PRECISION = 0.6961
BASELINE_RECALL = 0.7978
F1_TOLERANCE = 0.005  # non_degradation_margin: mutation may not drop F1 by >0.5pp

# Thresholds (Technical Deliverable 3)
P_POS = 0.65  # positive target-scope threshold
P_NEG = 0.35  # positive/negative classification cutoff
K_MIN = 0.45  # minimum Kappa for reliable agreement

THRESHOLD_NOTES = {
    "P_POS": "Positive-target scope threshold: predictions >= this are scored as positive targets.",
    "P_NEG": "Positive/negative classification cutoff: >= this score is a positive prediction.",
    "K_MIN": "Minimum Kappa for reliable agreement between predicted and target labels.",
    "BASELINE": "Phase F3 baseline F1 used as the non-degradation reference.",
}

# Corpus schema tags (decision-data layer)
OPEN_WORLD = "open-world"
CLOSED_WORLD = "closed-world"
TARGET_TYPES = [OPEN_WORLD, CLOSED_WORLD]

# Canonical schema URI for the frozen corpus
SCHEMA_URI = "https://jre.jyotish/validation/benchmark/1.0.0"

# Synthetic event id prefix used by HistoricalValidationRunner for
# unmatched-prediction FALSE_POSITIVE entries (no ground-truth event).
_UNMATCHED_EVENT_PREFIX = "unmatched_"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ── Canonical hash policy (mirrors jrs.validation.golden_state + storage) ───
def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _canonicalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize(v) for v in obj]
    return obj


def canonical_json(data: Any) -> str:
    return json.dumps(_canonicalize(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── Corpus loading ──────────────────────────────────────────────────────────
def _iter_chart_fixtures() -> list[Path]:
    return sorted(DEV_DIR.glob("chart_*.json")) + sorted(VAL_DIR.glob("chart_*.json"))


def load_corpus() -> list[dict[str, Any]]:
    """Load every frozen chart fixture (30 dev + 10 validation)."""
    corpus: list[dict[str, Any]] = []
    for path in _iter_chart_fixtures():
        data = load_json(path)
        if "_meta" not in data:
            raise ValueError(f"Chart fixture missing _meta block: {path}")
        if "known_events" not in data:
            raise ValueError(f"Chart fixture missing known_events: {path}")
        corpus.append(data)
    return corpus


def validate_corpus_files() -> None:
    entries = load_json(MANIFEST_PATH)
    expected_ids = {e["fixture_id"] for e in entries}
    seen_ids = set()

    for path in _iter_chart_fixtures():
        data = load_json(path)
        fid = data["_meta"]["fixture_id"]
        seen_ids.add(fid)
        if fid not in expected_ids:
            raise ValueError(f"Orphan fixture (not in manifest): {path}")

    for entry in entries:
        if entry["fixture_id"] not in seen_ids:
            raise ValueError(f"Orphan manifest entry (no input file): {entry['fixture_id']}")
        if entry.get("target_scope") not in TARGET_TYPES:
            raise ValueError(f"Invalid target_scope for {entry['fixture_id']}: {entry.get('target_scope')!r}")


# ── Metric computation (from EventPredictionMatch outcomes) ─────────────────
def _f1_from_counts(tp: int, fp: int, fn: int) -> float:
    """F1 for one binary bucket: 2*tp / (2*tp + fp + fn)."""
    denom = 2 * tp + fp + fn
    return 2 * tp / denom if denom else 0.0


def _is_unmatched_prediction(match: EventPredictionMatch) -> bool:
    """True for the runner's synthetic unmatched-prediction entries.

    These carry a synthetic ``unmatched_<yoga>`` event id: the chart
    produced a non-CANCELLED prediction with no ground-truth counterpart.
    Like the Phase F3 protocol (which scores real events only), they are
    excluded from event-level confusion counts.
    """
    return match.event_id.startswith(_UNMATCHED_EVENT_PREFIX)


def _score_event_level(result: ChartValidationResult) -> Counter[str]:
    """Fold one chart's matches into event-level TP/FP/FN counts.

    Canonical Phase F3 mapping (see module docstring): every real
    ``KnownEvent`` is scored exactly once from its best
    :class:`EventPredictionMatch`.
    """
    counts: Counter[str] = Counter()
    has_activation = any(
        p.predicted_status != "CANCELLED" for p in result.predicted_yogas
    )
    for match in result.matches:
        if _is_unmatched_prediction(match):
            continue
        if match.verdict == PredictionVerdict.TRUE_POSITIVE:
            counts["tp"] += 1
        elif match.verdict == PredictionVerdict.FALSE_NEGATIVE:
            # CANCELLED best prediction -> asserted-but-failed (FP) when the
            # chart still produced some activation; silent miss otherwise (FN).
            counts["fp" if has_activation else "fn"] += 1
        # TRUE_NEGATIVE: not produced by the runner today — not scored.
    return counts


def _build_birth_chart(data: dict[str, Any], jre_facts: dict[str, Any]) -> BirthChart:
    """Materialize a frozen benchmark fixture into a validation BirthChart."""
    raw = data["raw_birth_data"]
    events = tuple(
        KnownEvent(
            event_id=str(e["event_id"]),
            event_date_utc=str(e.get("event_date_utc", "")),
            event_window_start_utc=str(e.get("event_window_start_utc", "")),
            event_window_end_utc=str(e.get("event_window_end_utc", "")),
            domain=EventDomain(e.get("domain", "GENERAL")),
            description=str(e.get("description", "")),
            yoga_types=tuple(e.get("yoga_types", ())),
            expected_planets=tuple(e.get("expected_planets", ())),
        )
        for e in data["known_events"]
    )
    domain = EventDomain(events[0].domain.value) if events else EventDomain.GENERAL
    return BirthChart(
        chart_id=str(data["_meta"]["fixture_id"]),
        birth_data=BirthData(
            date=str(raw["date"]),
            time=str(raw["time"]),
            timezone=str(raw.get("timezone", "Asia/Kolkata")),
            latitude=float(raw["latitude"]),
            longitude=float(raw["longitude"]),
        ),
        jre_facts=jre_facts,
        known_events=events,
        domain=domain,
        description=str(data["_meta"].get("subject", "")),
    )


def evaluate_corpus() -> dict[str, Any]:
    """Run the frozen corpus through HistoricalValidationRunner.run_batch()
    and compute Macro / Micro F1 directly from EventPredictionMatch outcomes.
    """
    from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture

    corpus = load_corpus()

    # Materialize charts: ephemeris + fact extraction per fixture.
    charts: list[BirthChart] = []
    for data in corpus:
        natal = compute_chart_from_fixture(data)
        facts = build_jre_facts(natal)
        charts.append(_build_birth_chart(data, facts))

    # ── Execute the 5-Layer pipeline over the whole batch ──
    results = HistoricalValidationRunner().run_batch(charts)

    per_chart: dict[str, dict[str, Any]] = {}
    pooled: Counter[str] = Counter()
    domain_counts: dict[str, Counter[str]] = {}
    attributions = []

    for data, result in zip(corpus, results):
        fid = str(data["_meta"]["fixture_id"])
        counts = _score_event_level(result)
        pooled.update(counts)

        # Phase 5A: root-cause attribution for every FP/FN match. Matches
        # already carry their root RULE-*/FACT-*/TEMPORAL provenance ids
        # (attached inside run_batch).
        chart_attributions = [
            attribute_match(fid, m)
            for m in result.matches
            if m.verdict
            in (PredictionVerdict.FALSE_POSITIVE, PredictionVerdict.FALSE_NEGATIVE)
        ]
        attributions.extend(chart_attributions)

        # Charts are single-domain cohort fixtures; attribute the chart's
        # event-level counts to that life domain for the Macro average.
        domain = (
            str(data["known_events"][0]["domain"])
            if data["known_events"]
            else EventDomain.GENERAL.value
        )
        domain_counts.setdefault(domain, Counter()).update(counts)

        per_chart[fid] = {
            "target_scope": str(data.get("target_scope", CLOSED_WORLD)),
            "domain": domain,
            "event_count": result.total_known_events,
            "predicted_yogas": result.total_predicted_yogas,
            "true_positives": counts["tp"],
            "false_positives": counts["fp"],
            "false_negatives": counts["fn"],
            "error_attribution": {
                "by_kind": dict(
                    sorted(Counter(a.kind.value for a in chart_attributions).items())
                ),
                "failures": [a.to_dict() for a in chart_attributions],
            },
            "matches": [
                {
                    "event_id": m.event_id,
                    "yoga_name": m.yoga_name,
                    "verdict": m.verdict.value,
                    "timing_status": m.timing_status.value,
                    "timing_overlap_ratio": round(m.timing_overlap_ratio, 6),
                    "confidence": round(m.confidence, 6),
                    "root_rule_ids": list(m.root_rule_ids),
                    "root_fact_ids": list(m.root_fact_ids),
                    "temporal_affected": m.temporal_affected,
                }
                for m in result.matches
            ],
        }

    # ── Micro-F1: pooled event-level F1 (Phase F3 protocol formula) ──
    tp, fp, fn = pooled["tp"], pooled["fp"], pooled["fn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    micro_f1 = _f1_from_counts(tp, fp, fn)

    # ── Macro-F1: unweighted mean of per-domain F1 ──
    per_domain_f1 = {
        domain: _f1_from_counts(c["tp"], c["fp"], c["fn"])
        for domain, c in sorted(domain_counts.items())
    }
    macro_f1 = (
        sum(per_domain_f1.values()) / len(per_domain_f1) if per_domain_f1 else 0.0
    )

    return {
        "n_charts": len(corpus),
        "n_dev": len(list(DEV_DIR.glob("chart_*.json"))),
        "n_validation": len(list(VAL_DIR.glob("chart_*.json"))),
        "overall_metrics": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": pooled["tn"],
        },
        "precision": precision,
        "recall": recall,
        "f1": micro_f1,
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
        "per_domain_f1": per_domain_f1,
        "per_chart": per_chart,
        "error_attribution": summarize_attributions(attributions),
    }


# ── Manifest ────────────────────────────────────────────────────────────────
def corpus_sha256(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def build_corpus_manifest() -> dict[str, Any]:
    entries = []
    for path in _iter_chart_fixtures():
        data = load_json(path)
        entries.append(
            {
                "fixture_id": data["_meta"]["fixture_id"],
                "target_scope": data.get("target_scope", CLOSED_WORLD),
                "input_sha256": sha256_file(path),
                "computed_sha256": corpus_sha256(data),
                "evaluated_at": "2026-09-24T00:00:00Z",
            }
        )
    return {
        "schema_uri": SCHEMA_URI,
        "schema_version": "1.0.0",
        "corpus_version": "1.0.0",
        "total_charts": len(entries),
        "total_inputs_sha256": corpus_sha256(entries),
        "entries": entries,
    }


def write_corpus_manifest() -> None:
    write_json(MANIFEST_PATH, build_corpus_manifest())
    print(f"Wrote corpus manifest: {MANIFEST_PATH}")


def fixture_input_path(fixture_id: str, entry: dict[str, Any]) -> Path:
    """Resolve the immutable benchmark input file for a manifest entry."""
    scope = entry.get("target_scope", CLOSED_WORLD)
    return (VAL_DIR if scope == OPEN_WORLD else DEV_DIR) / f"{fixture_id}.json"


def verify_manifest(manifest_path: Path | None = None) -> list[str]:
    """Verify every frozen fixture against the manifest.

    Checks, per entry:
    - the fixture file exists and parses;
    - ``input_sha256`` matches the file bytes (immutability);
    - ``computed_sha256`` matches the canonical payload hash;
    - ``target_scope`` matches the fixture's declared scope;
    - no orphan fixtures and no orphan manifest entries.
    """
    path = manifest_path or MANIFEST_PATH
    manifest = load_json(path)
    by_id = {e["fixture_id"]: e for e in manifest["entries"]}
    mismatches: list[str] = []
    seen: set[str] = set()

    for file_path in _iter_chart_fixtures():
        data = load_json(file_path)
        fid = data.get("_meta", {}).get("fixture_id")
        if not fid:
            mismatches.append(f"{file_path.name}: missing _meta.fixture_id")
            continue
        seen.add(fid)
        entry = by_id.get(fid)
        if entry is None:
            mismatches.append(f"{fid}: fixture not present in manifest")
            continue
        file_hash = sha256_file(file_path)
        if entry.get("input_sha256") != file_hash:
            mismatches.append(
                f"{fid}: input_sha256 drift (manifest={entry.get('input_sha256')!r}, "
                f"file={file_hash!r})"
            )
        computed = corpus_sha256(data)
        if entry.get("computed_sha256") != computed:
            mismatches.append(
                f"{fid}: computed_sha256 drift (manifest={entry.get('computed_sha256')!r}, "
                f"computed={computed!r})"
            )
        scope = data.get("target_scope", CLOSED_WORLD)
        if entry.get("target_scope") != scope:
            mismatches.append(
                f"{fid}: target_scope drift (manifest={entry.get('target_scope')!r}, "
                f"fixture={scope!r})"
            )

    for fid in sorted(set(by_id) - seen):
        mismatches.append(f"{fid}: orphan manifest entry (no input file)")

    return mismatches


# ── Gate ────────────────────────────────────────────────────────────────────
def assert_benchmark_gate() -> dict[str, Any]:
    metrics = evaluate_corpus()
    verdict = "PASS"
    failures = []

    # Manifest/invariant gate
    mismatches = verify_manifest()
    if mismatches:
        verdict = "FAIL"
        failures.extend(mismatches)

    # Metric gate (non-degradation >= baseline - tolerance)
    if metrics["macro_f1"] < BASELINE_MACRO_F1 - F1_TOLERANCE:
        failures.append(
            f"Macro F1 {metrics['macro_f1']:.4f} < threshold {BASELINE_MACRO_F1 - F1_TOLERANCE:.4f}"
        )
        verdict = "FAIL"
    if metrics["micro_f1"] < BASELINE_MICRO_F1 - F1_TOLERANCE:
        failures.append(
            f"Micro F1 {metrics['micro_f1']:.4f} < threshold {BASELINE_MICRO_F1 - F1_TOLERANCE:.4f}"
        )
        verdict = "FAIL"
    if metrics["precision"] < BASELINE_PRECISION - F1_TOLERANCE:
        failures.append(
            f"Precision {metrics['precision']:.4f} < threshold {BASELINE_PRECISION - F1_TOLERANCE:.4f}"
        )
        verdict = "FAIL"
    if metrics["recall"] < BASELINE_RECALL - F1_TOLERANCE:
        failures.append(
            f"Recall {metrics['recall']:.4f} < threshold {BASELINE_RECALL - F1_TOLERANCE:.4f}"
        )
        verdict = "FAIL"

    return {"verdict": verdict, "failures": failures, "metrics": metrics}


# ── CLI ─────────────────────────────────────────────────────────────────────
def _resolve_manifest_path(explicit: Path | None) -> None:
    """Resolve the manifest path from the CLI argument or environment.

    Mutates the module-level MANIFEST_PATH so every helper reads the same
    override (CLI wins, then BENCHMARK_MANIFEST env var).
    """
    global MANIFEST_PATH
    if explicit is not None:
        MANIFEST_PATH = explicit
        return
    override = os.environ.get("BENCHMARK_MANIFEST")
    if override:
        MANIFEST_PATH = Path(override)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to the frozen corpus manifest (default: tests/fixtures/benchmark/corpus_manifest.json).",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify hashes and exit without computing metrics.",
    )
    args = parser.parse_args(argv)

    _resolve_manifest_path(args.manifest)

    # Structural integrity: write the frozen schema if missing
    if not SCHEMA_PATH.exists():
        write_json(
            SCHEMA_PATH,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "JRS Phase F4 Frozen Validation Benchmark Corpus",
                "description": "Immutable 30-dev + 10-validation chart corpus. Canonical ground-truth event labels, open/closed-world target scope, metric thresholds, and provenance hashes.",
                "type": "object",
                "properties": {
                    "schema_uri": {"type": "string", "format": "uri"},
                    "schema_version": {"const": "1.0.0", "default": "1.0.0"},
                    "corpus_version": {"const": "1.0.0", "default": "1.0.0"},
                    "total_charts": {"type": "integer", "minimum": 0, "default": 40},
                    "total_inputs_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "entries": {
                        "type": "array",
                        "minItems": 40,
                        "items": {
                            "type": "object",
                            "properties": {
                                "fixture_id": {"type": "string"},
                                "target_scope": {"enum": TARGET_TYPES},
                                "input_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                "computed_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                "evaluated_at": {"type": "string", "format": "date-time"},
                            },
                            "required": [
                                "fixture_id",
                                "target_scope",
                                "input_sha256",
                                "computed_sha256",
                                "evaluated_at",
                            ],
                        },
                    },
                },
                "required": [
                    "schema_uri",
                    "schema_version",
                    "corpus_version",
                    "total_charts",
                    "total_inputs_sha256",
                    "entries",
                ],
            },
        )

    if args.verify_only:
        mismatches = verify_manifest()
        if mismatches:
            print("HASH VERIFICATION FAILED", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            return 1
        print(f"40 fixture(s) verified, {len(mismatches)} mismatch(es)")
        return 0

    result = assert_benchmark_gate()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"] == "PASS":
        print("\nBENCHMARK GATE: PASS (Phase F3 baseline retained)")
        return 0
    print("\nBENCHMARK GATE: FAIL", file=sys.stderr)
    for f in result["failures"]:
        print(f"  - {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
