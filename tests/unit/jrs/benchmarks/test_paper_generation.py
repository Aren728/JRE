"""Phase 11B: Paper artifact & technical report tests.

Validates that docs/paper is a faithful, deterministic compilation of
the live sealed artifacts: required sections, headline numbers sourced
from the bench seal and ablation report, PDF determinism, and the
--check staleness contract.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PAPER_MD = REPO_ROOT / "docs" / "paper" / "jre_bench_paper.md"
PAPER_PDF = REPO_ROOT / "docs" / "paper" / "jre_bench_paper.pdf"
BENCH_SEAL = REPO_ROOT / "benchmarks" / "JRE-BENCH-001.json"
ABLATION_JSON = REPO_ROOT / "reports" / "ablation_matrix.json"

_spec = importlib.util.spec_from_file_location(
    "generate_paper", REPO_ROOT / "scripts" / "generate_paper.py"
)
paper_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(paper_mod)


@pytest.fixture(scope="module")
def bench() -> dict:
    return json.loads(BENCH_SEAL.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ablation() -> dict:
    return json.loads(ABLATION_JSON.read_text(encoding="utf-8"))


@pytest.mark.skipif(not PAPER_MD.exists(), reason="paper not yet generated")
class TestPaperContent:
    def test_required_sections(self) -> None:
        text = PAPER_MD.read_text(encoding="utf-8")
        for section in (
            "## Abstract",
            "## 1. Introduction",
            "## 2. Benchmark Design (JRE-BENCH-001)",
            "## 3. Determinism & Audit Infrastructure",
            "## 4. Ablation Methodology",
            "## 5. Results",
            "## 6. Power & Pre-Registration (JRE-BENCH-002)",
            "## 7. Threats to Validity",
            "## 8. Conclusion",
            "## References",
        ):
            assert section in text, section

    def test_headline_numbers_sourced_from_artifacts(
        self, bench: dict, ablation: dict
    ) -> None:
        text = PAPER_MD.read_text(encoding="utf-8")
        base = bench["baseline"]
        companion = bench["companion_baselines"][0]
        # Baseline and companion F1 exactly as sealed.
        assert f"Micro-F1 = {base['micro_f1']}" in text
        assert f"{companion['micro_f1']}**" in text
        # Confusion counts exactly as sealed.
        assert f"TP={base['confusion']['tp']}" in text
        assert f"FP={base['confusion']['fp']}" in text
        assert f"FN={base['confusion']['fn']}" in text
        # A3 verdict numbers exactly as measured.
        a3 = next(r for r in ablation["experiments"] if r["experiment_id"] == "A3")
        assert f"p = {a3['mcnemar']['p_value']:.2f}" in text
        assert f"+{a3['f1_delta']:.4f}" in text

    def test_all_four_experiments_tabulated(self) -> None:
        text = PAPER_MD.read_text(encoding="utf-8")
        for exp_id in ("A1", "A2", "A3", "A4"):
            assert f"| {exp_id} |" in text

    def test_no_hand_edited_drift_with_check_mode(self) -> None:
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "scripts/generate_paper.py", "--check"],
            capture_output=True,
            text=True,
            timeout=1200,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.skipif(not PAPER_PDF.exists(), reason="paper PDF not generated")
class TestPaperPdf:
    def test_pdf_header(self) -> None:
        assert PAPER_PDF.read_bytes()[:5] == b"%PDF-"

    def test_pdf_deterministic(self) -> None:
        ablation = json.loads(ABLATION_JSON.read_text(encoding="utf-8"))
        bench = json.loads(BENCH_SEAL.read_text(encoding="utf-8"))
        release_path = REPO_ROOT / "releases" / "v1.0.0-rc1.json"
        release = (
            json.loads(release_path.read_text(encoding="utf-8"))
            if release_path.exists()
            else None
        )
        markdown = paper_mod._render_markdown(
            {
                "bench": bench,
                "ablation": ablation,
                "calibration": {},
                "release": release,
                "golden_line": paper_mod._golden_verify_line(),
            }
        )
        assert paper_mod._render_pdf(markdown) == PAPER_PDF.read_bytes()


class TestGeneratorContract:
    def test_missing_artifact_fails_loudly(self, tmp_path: Path) -> None:
        # Point the module at an empty repo root: _collect_artifacts must
        # refuse to compile a paper from incomplete evidence.
        orig_root = paper_mod.REPO_ROOT
        attr_paths = {
            "BENCH_SEAL": "JRE-BENCH-001.json",
            "ABLATION_JSON": "ablation_matrix.json",
            "CALIBRATION_JSON": "calibration_phase_5f_hooks.json",
            "PREREG_DOC": "phase_11a_bench002_preregistration.md",
        }
        try:
            paper_mod.REPO_ROOT = tmp_path
            for attr, filename in attr_paths.items():
                setattr(paper_mod, attr, tmp_path / filename)
            with pytest.raises(SystemExit, match="Required artifacts missing"):
                paper_mod._collect_artifacts()
        finally:
            paper_mod.REPO_ROOT = orig_root
            paper_mod.BENCH_SEAL = orig_root / "benchmarks" / "JRE-BENCH-001.json"
            paper_mod.ABLATION_JSON = orig_root / "reports" / "ablation_matrix.json"
            paper_mod.CALIBRATION_JSON = (
                orig_root / "reports" / "calibration_phase_5f_hooks.json"
            )
            paper_mod.PREREG_DOC = (
                orig_root
                / "docs"
                / "validation"
                / "phase_11a_bench002_preregistration.md"
            )

    def test_inline_md_escapes_before_markup(self) -> None:
        rendered = paper_mod._inline_md("a < b & **bold** `code`")
        assert "&lt;" in rendered and "&amp;" in rendered
        assert "<b>bold</b>" in rendered
        assert "Courier" in rendered
