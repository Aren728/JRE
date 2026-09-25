"""Phase 5B: Ashtakavarga calculation module tests.

Validates the classical bindu matrix against BPHS Ch 66 canonical totals,
the deterministic JSON fixture (``tests/fixtures/ashtakavarga/``), the
Shodhana reduction semantics, Shodhita Pinda, and the feature-flag
regression guard.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.calculations.ashtakavarga import (
    ANCHORS,
    ASHTAKAVARGA_STAGE_VERSION,
    BENEFIC_TOTALS,
    BINDU_MATRIX,
    EKADHIPATYA_PAIRS,
    PLANETARY_ANCHORS,
    RASHI_ORDER,
    TRIKONA_GROUPS,
    ashta_scoring_enabled,
    ashtakavarga_to_dict,
    compute_bav,
    compute_full_ashtakavarga,
    compute_pinda,
    compute_sav,
    ekadhipatya_shodhana,
    trikona_shodhana,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "ashtakavarga"
    / "fixture_000_einstein.json"
)

FIXTURE_FACTS = {
    "planets": {
        "SUN": {"rashi": "MEENA"},
        "MOON": {"rashi": "VRISHCHIKA"},
        "MARS": {"rashi": "MAKARA"},
        "MERCURY": {"rashi": "MEENA"},
        "JUPITER": {"rashi": "KUMBHA"},
        "VENUS": {"rashi": "MEENA"},
        "SATURN": {"rashi": "MEENA"},
    },
    "lagna": "MITHUNA",
}


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# ── Classical table invariants (BPHS Ch 66) ─────────────────────────────────
class TestClassicalTables:
    def test_planetary_totals_match_bphs(self) -> None:
        assert BENEFIC_TOTALS == {
            "SUN": 48,
            "MOON": 49,
            "MARS": 39,
            "MERCURY": 54,
            "JUPITER": 56,
            "VENUS": 52,
            "SATURN": 39,
        }

    def test_matrix_rows_sum_to_canonical_totals(self) -> None:
        for anchor in ANCHORS:
            row_total = sum(len(h) for h in BINDU_MATRIX[anchor].values())
            if anchor == "LAGNA":
                assert row_total == 50  # BPHS 66.65-68
            else:
                assert row_total == BENEFIC_TOTALS[anchor]

    def test_all_rows_have_eight_contributors(self) -> None:
        for anchor in ANCHORS:
            assert set(BINDU_MATRIX[anchor]) == set(ANCHORS)
            for houses in BINDU_MATRIX[anchor].values():
                assert len(houses) == len(set(houses))  # no duplicates
                assert all(1 <= h <= 12 for h in houses)

    def test_ekadhipatya_pairs_are_same_lorded(self) -> None:
        assert EKADHIPATYA_PAIRS == (
            ("MESHA", "VRISHCHIKA"),  # Mars
            ("VRISHABHA", "TULA"),  # Venus
            ("MITHUNA", "KANYA"),  # Mercury
            ("DHANUSHA", "MEENA"),  # Jupiter
            ("MAKARA", "KUMBHA"),  # Saturn
        )

    def test_trikona_groups_are_trines(self) -> None:
        for group in TRIKONA_GROUPS:
            idxs = [RASHI_ORDER.index(s) for s in group]
            assert (idxs[1] - idxs[0]) % 12 == 4
            assert (idxs[2] - idxs[1]) % 12 == 4


# ── BAV / SAV computation ───────────────────────────────────────────────────
class TestBAV:
    def test_bav_row_totals_are_anchor_totals(self) -> None:
        bav = compute_bav({a: "MESHA" for a in ANCHORS})
        for anchor in ANCHORS:
            assert sum(bav[anchor]) == (
                50 if anchor == "LAGNA" else BENEFIC_TOTALS[anchor]
            )

    def test_bav_per_sign_bounded_0_to_8(self) -> None:
        bav = compute_bav({a: "MEENA" for a in ANCHORS})
        for anchor in ANCHORS:
            assert len(bav[anchor]) == 12
            assert all(0 <= v <= 8 for v in bav[anchor])

    def test_bav_depends_on_anchor_position(self) -> None:
        mesha = compute_bav({a: "MESHA" for a in ANCHORS})["SUN"]
        meena = compute_bav({a: "MEENA" for a in ANCHORS})["SUN"]
        assert mesha != meena  # rotation moves the bindus


class TestSAV:
    def test_sav_excludes_lagna_and_totals_337(self) -> None:
        signs = {a: "MESHA" for a in ANCHORS}
        bav = compute_bav(signs)
        sav = compute_sav(bav)
        assert len(sav) == 12
        assert sum(sav) == 337  # mathematical invariant
        # The SAV must equal the 7-planet column sum (Lagna row excluded).
        planetary = [0] * 12
        for anchor in PLANETARY_ANCHORS:
            for i, v in enumerate(bav[anchor]):
                planetary[i] += v
        assert list(sav) == planetary


# ── Shodhana reductions ─────────────────────────────────────────────────────
class TestShodhana:
    ROW = (4, 5, 6, 3, 7, 2, 5, 4, 6, 3, 5, 4)

    def test_trikona_reduces_all_to_row_minimum(self) -> None:
        reduced = trikona_shodhana(self.ROW)
        for group in TRIKONA_GROUPS:
            idxs = [RASHI_ORDER.index(s) for s in group]
            values = [reduced[i] for i in idxs]
            assert len(set(values)) == 1  # all three equal
            assert values[0] == min(self.ROW[i] for i in idxs)

    def test_trikona_is_monotone_non_increasing(self) -> None:
        reduced = trikona_shodhana(self.ROW)
        assert all(r <= o for r, o in zip(reduced, self.ROW))

    def test_ekadhipatya_higher_reduced_to_lower(self) -> None:
        # Mithuna(idx 2)=6 vs Kanya(idx 5)=2 -> Mithuna reduced to 2.
        reduced = ekadhipatya_shodhana(self.ROW)
        assert reduced[2] == 2
        assert reduced[5] == 2

    def test_ekadhipatya_equal_counts_zero_both(self) -> None:
        # Mesha(idx 0)=4 vs Vrishchika(idx 7)=4 -> both zeroed.
        reduced = ekadhipatya_shodhana(self.ROW)
        assert reduced[0] == 0
        assert reduced[7] == 0

    def test_ekadhipatya_requires_both_occupied(self) -> None:
        # Only Mesha occupied: the Mars pair must be left untouched.
        reduced = ekadhipatya_shodhana(
            self.ROW, occupied_signs=frozenset({"MESHA"})
        )
        assert (reduced[0], reduced[7]) == (self.ROW[0], self.ROW[7])

    def test_ekadhipatya_unconditional_when_occupancy_none(self) -> None:
        reduced = ekadhipatya_shodhana(self.ROW, occupied_signs=None)
        assert (reduced[0], reduced[7]) == (0, 0)


# ── Pinda ───────────────────────────────────────────────────────────────────
class TestPinda:
    def test_pinda_structure_and_sum(self, fixture_data: dict) -> None:
        pinda = fixture_data["expected"]["report"]["pinda"]["SUN"]
        assert pinda["shodhya_pinda"] == (
            pinda["rashi_pinda"] + pinda["graha_pinda"]
        )

    def test_graha_pinda_is_position_dependent(self) -> None:
        # Moving ONE planet (Saturn) changes the relative geometry: the
        # occupied sign whose bindus each anchor's Graha Pinda reads for
        # Saturn shifts from Mesha (idx 0) to Meena (idx 11). A
        # whole-chart rotation would be a symmetry (identical Pinda).
        signs_a = {a: "MESHA" for a in ANCHORS}
        signs_b = {**signs_a, "SATURN": "MEENA"}
        pa = compute_pinda(compute_bav(signs_a), signs_a)
        pb = compute_pinda(compute_bav(signs_b), signs_b)
        assert pa != pb  # at least one anchor's Pinda moved
        # Saturn's own Graha Pinda must differ: its occupied sign changed.
        assert (
            pa["SATURN"]["graha_pinda"] != pb["SATURN"]["graha_pinda"]
        )
        # Rashi Pinda (pure row x sign-multiplier sum) is unaffected by
        # where other planets sit.
        assert pa["SUN"]["rashi_pinda"] == pb["SUN"]["rashi_pinda"]


# ── Deterministic fixture contract ──────────────────────────────────────────
class TestFixtureContract:
    def test_fixture_exists(self) -> None:
        assert FIXTURE_PATH.exists()

    def test_report_matches_fixture(self, fixture_data: dict) -> None:
        rep = compute_full_ashtakavarga(FIXTURE_FACTS)
        assert ashtakavarga_to_dict(rep) == fixture_data["expected"]["report"]

    def test_sav_total_is_337(self, fixture_data: dict) -> None:
        assert fixture_data["expected"]["sav_total"] == 337
        rep = ashtakavarga_to_dict(compute_full_ashtakavarga(FIXTURE_FACTS))
        assert sum(rep["sav"]) == fixture_data["expected"]["sav_total"]

    def test_fact_ids_are_namespaced(self, fixture_data: dict) -> None:
        fact_ids = fixture_data["expected"]["report"]["fact_ids"]
        assert len(fact_ids) == 17  # 8 BAV + SAV + 8 PINDA
        assert all(fid.startswith("FACT-ASHTA-") for fid in fact_ids)
        assert fact_ids[0] == "FACT-ASHTA-BAV-SUN"
        assert "FACT-ASHTA-SAV" in fact_ids
        assert fact_ids[-1] == "FACT-ASHTA-PINDA-LAGNA"

    def test_determinism(self) -> None:
        a = ashtakavarga_to_dict(compute_full_ashtakavarga(FIXTURE_FACTS))
        b = ashtakavarga_to_dict(compute_full_ashtakavarga(FIXTURE_FACTS))
        assert a == b


# ── Feature flag (baseline regression guard) ────────────────────────────────
class TestFeatureFlag:
    def test_default_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JRS_ASHTA_SCORING", raising=False)
        assert ashta_scoring_enabled() is False

    def test_env_truthy_enables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("1", "true", "YES", "on"):
            monkeypatch.setenv("JRS_ASHTA_SCORING", value)
            assert ashta_scoring_enabled() is True

    def test_env_falsy_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("", "0", "false", "off", "no"):
            monkeypatch.setenv("JRS_ASHTA_SCORING", value)
            assert ashta_scoring_enabled() is False

    def test_version_constant(self) -> None:
        assert ASHTAKAVARGA_STAGE_VERSION == "1.0.0"
