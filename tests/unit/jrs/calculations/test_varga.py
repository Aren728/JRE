"""Phase 5D: Multi-varga calculation module tests.

Validates the D1/D9/D10/D60 divisional arithmetic against the repo's
golden-verified D9 convention (500/500 fixture cases) and the BPHS D10
worked example, plus dignity, vargottama, the D10 career anchor, the
deterministic JSON fixture (``tests/fixtures/varga/``), and the
feature-flag guard.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.calculations.varga import (
    CAREER_ANCHOR_PLANETS,
    DIGNITY_SCORES,
    VARGA_DIVISIONS,
    VARGA_STAGE_VERSION,
    compute_multi_varga,
    dignity_of,
    multi_varga_to_dict,
    varga_placement,
    varga_scoring_enabled,
    varga_sign_index,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "varga"
    / "fixture_000_einstein.json"
)

FIXTURE_FACTS = {
    "planets": {
        "SUN": {"longitude": 331.32419345824417},
        "MOON": {"longitude": 232.22148712046456},
        "MARS": {"longitude": 274.7331682026066},
        "MERCURY": {"longitude": 340.95139065805967},
        "JUPITER": {"longitude": 305.3077339155739},
        "VENUS": {"longitude": 354.79925006625405},
        "SATURN": {"longitude": 342.01443295977805},
    },
}
LAGNA_LON = 76.64987356635059
VARGOTTAMA_LON = 0.0  # MESHA 0deg: first navamsa of a fire sign = itself

EXPECTED_D9_SUN = "VRISHCHIKA"  # golden-fixture verified for Einstein


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# ── Divisional arithmetic ───────────────────────────────────────────────────
class TestDivisionalArithmetic:
    def test_d1_is_the_sign_itself(self) -> None:
        assert varga_sign_index(5.0, "D1") == 0  # MESHA
        assert varga_sign_index(331.32, "D1") == 11  # MEENA

    def test_d9_matches_golden_verified_convention(self) -> None:
        # Einstein's SUN: MEENA 1.32 -> VRISHCHIKA (per hand-verified
        # expected_canonical_facts; the textbook continuous rule would
        # give KARKA — deliberately NOT used here).
        assert varga_placement(331.32419345824417, "D9")["sign"] == EXPECTED_D9_SUN

    def test_d9_parity_with_repo_compute_d9_sign(self) -> None:
        # The repo's _compute_d9_sign (nested in build_jre_facts) is
        # golden-validated; re-derive it locally and compare over a
        # 0.01-degree grid across the whole zodiac.
        rashi = (
            "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
            "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
        )
        nav_arc = 30.0 / 9.0

        def repo_d9(lon: float) -> str:
            si = int(lon / 30.0)
            part = int((lon - si * 30.0) / nav_arc)
            st = si % 4
            start = (
                si if st == 0
                else (si + 5) % 12 if st == 1
                else (si + 4) % 12 if st == 2
                else (si + 8) % 12
            )
            return rashi[(start + part) % 12]

        for i in range(0, 36000):
            lon = i * 0.01
            assert (
                varga_placement(lon, "D9")["sign"] == repo_d9(lon)
            ), f"D9 parity broken at {lon}"

    def test_d9_all_starts_are_consistent_with_repo_offsets(self) -> None:
        # Fire signs start from themselves; earth +5; air +4; water +8.
        for si in range(12):
            lon = si * 30.0 + 0.1  # first navamsa of the sign
            start = varga_sign_index(lon, "D9")
            st = si % 4
            expected = (
                si if st == 0
                else (si + 5) % 12 if st == 1
                else (si + 4) % 12 if st == 2
                else (si + 8) % 12
            )
            assert start == expected

    def test_d10_bphs_worked_example(self) -> None:
        # BPHS: Jupiter at 17deg20' Leo (odd, 6th part) -> Capricorn.
        leo_jupiter = 4 * 30 + 17 + 20 / 60
        assert varga_placement(leo_jupiter, "D10")["sign"] == "MAKARA"

    def test_d10_odd_self_even_ninth(self) -> None:
        # Odd sign MESHA: 1st part -> MESHA.
        assert varga_placement(1.0, "D10")["sign"] == "MESHA"
        # Even sign VRISHABHA: 1st part -> 9th from it (inclusive) =
        # MAKARA.
        assert varga_placement(31.0, "D10")["sign"] == "MAKARA"

    def test_d60_continuous_half_degree_parts(self) -> None:
        # 0.4deg MESHA: part 1 (0-0.5), stays MESHA; 0.6deg -> part 2 ->
        # VRISHABHA.
        assert varga_placement(0.4, "D60")["sign"] == "MESHA"
        assert varga_placement(0.6, "D60")["sign"] == "VRISHABHA"

    def test_unknown_division_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown varga division"):
            varga_sign_index(0.0, "D7")

    def test_division_arcs(self) -> None:
        assert VARGA_DIVISIONS["D9"][1] == pytest.approx(30.0 / 9.0)
        assert VARGA_DIVISIONS["D10"][1] == 3.0
        assert VARGA_DIVISIONS["D60"][1] == 0.5


# ── Dignity ─────────────────────────────────────────────────────────────────
class TestDignity:
    def test_exaltation_and_debilitation(self) -> None:
        assert dignity_of("SUN", 0) == "EXALTED"  # MESHA
        assert dignity_of("SUN", 6) == "DEBILITATED"  # TULA
        assert dignity_of("JUPITER", 3) == "EXALTED"  # KARKA
        assert dignity_of("JUPITER", 9) == "DEBILITATED"  # MAKARA

    def test_own_signs(self) -> None:
        assert dignity_of("SATURN", 10) == "OWN"  # KUMBHA
        assert dignity_of("MARS", 0) == "OWN"  # MESHA
        assert dignity_of("VENUS", 1) == "OWN"  # VRISHABHA

    def test_exaltation_takes_precedence_over_own(self) -> None:
        # Tula is both Saturn's exaltation and own sign; exaltation wins.
        assert dignity_of("SATURN", 6) == "EXALTED"

    def test_neutral_fallback(self) -> None:
        assert dignity_of("SUN", 8) == "NEUTRAL"
        assert dignity_of("UNKNOWN", 0) == "NEUTRAL"


# ── Report assembly ─────────────────────────────────────────────────────────
class TestReport:
    def test_report_matches_fixture(self, fixture_data: dict) -> None:
        rep = multi_varga_to_dict(
            compute_multi_varga(FIXTURE_FACTS, lagna_longitude=LAGNA_LON)
        )
        assert rep == fixture_data["expected"]["report"]

    def test_vargottama_demo_matches_fixture(self, fixture_data: dict) -> None:
        demo = multi_varga_to_dict(
            compute_multi_varga(
                {
                    "planets": {
                        p: {"longitude": VARGOTTAMA_LON}
                        for p in FIXTURE_FACTS["planets"]
                    }
                },
                lagna_longitude=VARGOTTAMA_LON,
            )
        )
        assert demo == fixture_data["expected"]["vargottama_report"]
        # Every body (incl. Lagna) is vargottama at MESHA 0deg.
        assert all(demo["vargottama"].values())

    def test_einstein_has_no_vargottama(self, fixture_data: dict) -> None:
        rep = fixture_data["expected"]["report"]
        assert not any(rep["vargottama"].values())

    def test_navamsha_dignity_values(self, fixture_data: dict) -> None:
        nav = fixture_data["expected"]["report"]["navamsha_dignity"]
        assert nav["JUPITER"] == "EXALTED"  # D9 KARKA
        assert nav["SATURN"] == "OWN"  # D9 KUMBHA
        assert nav["MARS"] == "DEBILITATED"  # D9 KARKA
        assert "LAGNA" not in nav  # dignity undefined for the Lagna

    def test_career_anchor_structure(self, fixture_data: dict) -> None:
        anchor = fixture_data["expected"]["report"]["career_anchor"]
        assert anchor["planet"] in CAREER_ANCHOR_PLANETS
        assert anchor["dignity"] in ("EXALTED", "OWN", "NEUTRAL", "DEBILITATED")
        assert anchor["strength"] == DIGNITY_SCORES[anchor["dignity"]]
        assert set(anchor["scores"]) == set(CAREER_ANCHOR_PLANETS)

    def test_fact_ids_shape(self, fixture_data: dict) -> None:
        rep = fixture_data["expected"]["report"]
        fact_ids = rep["fact_ids"]
        # 8 bodies x 4 divisions + career anchor (no vargottama here).
        assert len(fact_ids) == 33
        assert fact_ids[0] == "FACT-VARGA-D1-SUN"
        assert "FACT-VARGA-D9-LAGNA" in fact_ids
        assert fact_ids[-1] == "FACT-VARGA-D10-CAREER-ANCHOR"

    def test_vargottama_fact_ids_emitted(self, fixture_data: dict) -> None:
        demo = fixture_data["expected"]["vargottama_report"]
        for body in ("SUN", "LAGNA"):
            assert f"FACT-VARGA-VARGOTTAMA-{body}" in demo["fact_ids"]

    def test_determinism(self) -> None:
        a = multi_varga_to_dict(
            compute_multi_varga(FIXTURE_FACTS, lagna_longitude=LAGNA_LON)
        )
        b = multi_varga_to_dict(
            compute_multi_varga(FIXTURE_FACTS, lagna_longitude=LAGNA_LON)
        )
        assert a == b

    def test_missing_longitude_raises(self) -> None:
        with pytest.raises(ValueError, match="missing longitude"):
            compute_multi_varga({"planets": {"SUN": {}}})

    def test_lagna_optional(self) -> None:
        rep = compute_multi_varga(FIXTURE_FACTS)
        assert rep["lagna_evaluated"] is False
        assert "LAGNA" not in rep["placements"]


# ── Feature flag & version ──────────────────────────────────────────────────
class TestFeatureFlag:
    def test_default_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JRS_VARGA_SCORING", raising=False)
        assert varga_scoring_enabled() is False

    def test_env_truthy_enables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("1", "true", "YES", "on"):
            monkeypatch.setenv("JRS_VARGA_SCORING", value)
            assert varga_scoring_enabled() is True

    def test_env_falsy_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("", "0", "false", "off"):
            monkeypatch.setenv("JRS_VARGA_SCORING", value)
            assert varga_scoring_enabled() is False

    def test_version_constant(self) -> None:
        assert VARGA_STAGE_VERSION == "1.0.0"
