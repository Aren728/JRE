"""Phase 9C: Benchmark integrity protocol tests (JRE-BENCH-001).

The sealed benchmark manifest must always agree with live repository
state: frozen corpus hashes, label schema, evaluation protocol, and the
gating Phase F3 baseline. Any drift in corpus inputs, thresholds, or
protocol is an integrity violation — amendments require a NEW benchmark
id, never in-place mutation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from jrs.validation.benchmark import (
    BASELINE_MACRO_F1,
    BASELINE_MICRO_F1,
    BASELINE_PRECISION,
    BASELINE_RECALL,
    F1_TOLERANCE,
    MANIFEST_PATH,
    verify_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SEAL_PATH = REPO_ROOT / "benchmarks" / "JRE-BENCH-001.json"
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_clean_reproduce.py"


@pytest.fixture(scope="module")
def seal() -> dict:
    assert SEAL_PATH.exists(), (
        "JRE-BENCH-001.json missing — run scripts/seal_benchmark.py"
    )
    return json.loads(SEAL_PATH.read_text(encoding="utf-8"))


class TestBenchmarkSeal:
    def test_seal_is_frozen_with_immutable_policy(self, seal: dict) -> None:
        assert seal["benchmark_id"] == "JRE-BENCH-001"
        assert seal["status"] == "FROZEN"
        assert "never be mutated in place" in seal["policy"]["immutability"]
        assert "JRE-BENCH-002" in seal["policy"]["immutability"]

    def test_corpus_lock(self, seal: dict) -> None:
        corpus = seal["corpus"]
        assert corpus["total_charts"] == 40
        assert corpus["dev_charts"] == 30
        assert corpus["validation_charts"] == 10
        assert len(corpus["fixture_ids"]) == 40
        # The sealed corpus-manifest hash must match the live file.
        live_hash = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
        assert corpus["corpus_manifest_sha256"] == live_hash
        # And the manifest itself must verify against the fixture files.
        assert verify_manifest() == []

    def test_label_schema_lock(self, seal: dict) -> None:
        fields = {f["field"] for f in seal["label_schema"]["fields"]}
        assert {
            "event_id",
            "event_date_utc",
            "event_window_start_utc",
            "event_window_end_utc",
            "domain",
            "yoga_types",
            "expected_planets",
        } <= fields
        assert len(seal["label_schema"]["event_domains"]) >= 6

    def test_evaluation_protocol_lock(self, seal: dict) -> None:
        protocol = seal["evaluation_protocol"]
        assert protocol["implementation"].endswith("evaluate_corpus")
        assert "2*TP / (2*TP + FP + FN)" in protocol["micro_f1"]
        assert "unweighted mean" in protocol["macro_f1"]
        assert "unmatched_<yoga>" in protocol["excluded"]

    def test_gating_baseline_matches_module_constants(self, seal: dict) -> None:
        baseline = seal["baseline"]
        assert baseline["gating"] is True
        assert baseline["micro_f1"] == BASELINE_MICRO_F1
        assert baseline["macro_f1"] == BASELINE_MACRO_F1
        assert baseline["precision"] == BASELINE_PRECISION
        assert baseline["recall"] == BASELINE_RECALL
        assert baseline["non_degradation_tolerance"] == F1_TOLERANCE
        assert baseline["confusion"] == {"tp": 71, "fp": 31, "fn": 18}

    def test_companion_baselines_recorded_not_gating(self, seal: dict) -> None:
        companions = seal["companion_baselines"]
        scenarios = {c["scenario"] for c in companions}
        assert {"MULTI_VARGA", "ALL_ON"} <= scenarios
        for companion in companions:
            assert companion["gating" in companion] is False if isinstance(
                companion.get("gating"), bool
            ) else True
            assert companion["micro_f1"] >= seal["baseline"]["micro_f1"]

    def test_reproduction_target_shared_with_audit(self, seal: dict) -> None:
        # The 9A audit script must carry the identical frozen target.
        audit_text = AUDIT_SCRIPT.read_text(encoding="utf-8")
        assert '"tp": 71' in audit_text
        assert '"fp": 31' in audit_text
        assert '"fn": 18' in audit_text
        assert "0.7435" in audit_text
        # And the seal's seal-generator self-reference exists.
        assert seal["sealed_by"] == "scripts/seal_benchmark.py"

    def test_seal_verification_tool_agrees(self, seal: dict) -> None:
        # Rebuild the seal from live state and compare locked sections.
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "scripts/seal_benchmark.py", "--check"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-400:]
