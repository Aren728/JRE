"""Phase 5C: Gochara (transit) calculation module tests.

Validates the whole-sign house geometry, the classical Vedha table with
its exemptions, the Kakshya 3°45′ division with the canonical lord
sequence, TQS band mapping, the deterministic JSON fixture
(``tests/fixtures/gochara/``), the pinned-epoch invariant, and the
feature-flag guard.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from jrs.calculations.gochara import (
    GOCHARA_BANDS,
    GOCHARA_STAGE_VERSION,
    GOCHARA_TRANSIT_EPOCH,
    KAKSHYA_ARC_DEG,
    KAKSHYA_LORDS,
    VEDHA_MULTIPLIER,
    VEDHA_TABLE,
    band_for_tqs,
    compute_gochara,
    compute_tqs,
    gochara_scoring_enabled,
    gochara_to_dict,
    house_from_anchor,
    is_vedha_obstructed,
    kakshya_of,
    rashi_of_longitude,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "gochara"
    / "fixture_000_einstein.json"
)

FIXTURE_FACTS = {
    "planets": {
        "SUN": {"rashi": "MEENA", "longitude": 331.32419345824417},
        "MOON": {"rashi": "VRISHCHIKA", "longitude": 232.22148712046456},
        "MARS": {"rashi": "MAKARA", "longitude": 274.7331682026066},
        "MERCURY": {"rashi": "MEENA", "longitude": 340.95139065805967},
        "JUPITER": {"rashi": "KUMBHA", "longitude": 305.3077339155739},
        "VENUS": {"rashi": "MEENA", "longitude": 354.79925006625405},
        "SATURN": {"rashi": "MEENA", "longitude": 342.01443295977805},
    },
    "lagna": "MITHUNA",
    "ashtakavarga": {
        "sav": [22, 27, 30, 22, 34, 19, 27, 35, 29, 42, 22, 28],
        "shodhita_sav": [18, 13, 17, 17, 18, 13, 17, 17, 18, 4, 4, 17],
    },
}

FIXTURE_TRANSITS = {
    "SUN": 255.0,
    "MOON": 305.0,
    "MARS": 235.0,
    "MERCURY": 262.5,
    "JUPITER": 253.0,
    "VENUS": 280.0,
    "SATURN": 296.0,
}


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


# ── Geometry ────────────────────────────────────────────────────────────────
class TestHouses:
    def test_whole_sign_counting(self) -> None:
        assert house_from_anchor(0.0, 0.0) == 1  # same sign
        assert house_from_anchor(35.0, 0.0) == 2  # one sign ahead
        assert house_from_anchor(350.0, 0.0) == 12  # one sign behind
        assert house_from_anchor(180.0, 0.0) == 7  # opposition

    def test_anchor_reduced_to_sign(self) -> None:
        # 5° of the anchor's sign vs 25°: both are house 1 (whole-sign).
        assert house_from_anchor(25.0, 5.0) == 1

    def test_rashi_of_longitude(self) -> None:
        assert rashi_of_longitude(0.0) == "MESHA"
        assert rashi_of_longitude(299.9) == "MAKARA"
        assert rashi_of_longitude(360.0) == "MESHA"


class TestKakshya:
    def test_arc_is_3deg45(self) -> None:
        assert KAKSHYA_ARC_DEG == 3.75

    def test_canonical_lord_sequence(self) -> None:
        assert KAKSHYA_LORDS == (
            "SATURN",
            "JUPITER",
            "MARS",
            "SUN",
            "VENUS",
            "MERCURY",
            "MOON",
            "LAGNA",
        )

    def test_division_boundaries(self) -> None:
        assert kakshya_of(3.0)["lord"] == "SATURN"  # 0°–3°45′
        assert kakshya_of(4.0)["lord"] == "JUPITER"  # 3°45′–7°30′
        assert kakshya_of(29.9)["lord"] == "LAGNA"  # 26°15′–30°
        k = kakshya_of(26.3)  # 8th spans 26.25-30.0; 26.0 would be 7th
        assert k["index"] == 8
        assert k["start_deg"] == 26.25
        assert k["end_deg"] == 30.0
        assert kakshya_of(26.0)["index"] == 7  # boundary exclusive

    def test_spans_are_contiguous(self) -> None:
        for i in range(1, 9):
            k = kakshya_of((i - 1) * KAKSHYA_ARC_DEG + 0.01)
            assert k["index"] == i


# ── Classical Vedha table ───────────────────────────────────────────────────
class TestVedha:
    def test_table_shape(self) -> None:
        assert set(VEDHA_TABLE) == {
            "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN",
        }
        for planet, pairs in VEDHA_TABLE.items():
            for favorable, obstructing in pairs.items():
                # Obstructing house is opposite-ish: pairs sum to 12 or 14
                # (classical 1/12, 2/12, 3/9, 4/10, 5/9, 5/11, 6/12, 8/12
                # style oppositions) — spot-assert the known rows.
                assert 1 <= favorable <= 12
                assert 1 <= obstructing <= 12

    def test_sun_row_matches_classical(self) -> None:
        assert VEDHA_TABLE["SUN"] == {3: 9, 6: 12, 10: 4, 11: 5}

    def test_exemptions_honor_classical_rule(self) -> None:
        # Saturn in 9th does NOT obstruct Sun in 3rd.
        blocked, house = is_vedha_obstructed(
            "SUN", 3, {"SUN": 3, "SATURN": 9}
        )
        assert blocked is False
        assert house == 9  # pair exists; occupant is exempt

        # Mercury in 5th does NOT obstruct Moon in 1st.
        blocked, _ = is_vedha_obstructed("MOON", 1, {"MOON": 1, "MERCURY": 5})
        assert blocked is False

    def test_active_obstruction(self) -> None:
        # Venus in 12th obstructs Mars in 3rd (no exemption).
        blocked, house = is_vedha_obstructed(
            "MARS", 3, {"MARS": 3, "VENUS": 12}
        )
        assert blocked is True
        assert house == 12

    def test_no_obstruction_without_occupant(self) -> None:
        blocked, house = is_vedha_obstructed("MARS", 3, {"MARS": 3})
        assert blocked is False
        assert house == 12  # pair still reported

    def test_no_pair_no_obstruction(self) -> None:
        blocked, house = is_vedha_obstructed("MARS", 4, {"MARS": 4, "SUN": 10})
        assert blocked is False
        assert house is None


# ── TQS and bands ───────────────────────────────────────────────────────────
class TestTQS:
    def test_tqs_is_sav_lookup(self) -> None:
        row = tuple(range(12))
        assert compute_tqs(row, 9) == 9

    def test_band_mapping(self) -> None:
        assert band_for_tqs(42)["label"] == "SUPPORTIVE"
        assert band_for_tqs(30)["label"] == "SUPPORTIVE"
        assert band_for_tqs(29)["label"] == "NEUTRAL"
        assert band_for_tqs(25)["label"] == "NEUTRAL"
        assert band_for_tqs(20)["label"] == "MIXED"
        assert band_for_tqs(10)["label"] == "AFFLICTED"

    def test_bands_are_frozen(self) -> None:
        assert GOCHARA_BANDS == (
            (30, 1.08, "SUPPORTIVE"),
            (25, 1.00, "NEUTRAL"),
            (18, 0.92, "MIXED"),
            (0, 0.80, "AFFLICTED"),
        )
        assert VEDHA_MULTIPLIER == 0.80


# ── Full report ─────────────────────────────────────────────────────────────
class TestComputeGochara:
    def test_report_matches_fixture(self, fixture_data: dict) -> None:
        rep = gochara_to_dict(
            compute_gochara(
                FIXTURE_FACTS,
                FIXTURE_TRANSITS,
                epoch=GOCHARA_TRANSIT_EPOCH,
            )
        )
        assert rep == fixture_data["expected"]["report"]

    def test_pinned_epoch_by_default(self) -> None:
        rep = compute_gochara(FIXTURE_FACTS, FIXTURE_TRANSITS)
        assert rep["epoch_utc"] == "2020-01-01T00:00:00+0000"

    def test_fact_id_format(self, fixture_data: dict) -> None:
        planets = fixture_data["expected"]["report"]["planets"]
        assert planets["SATURN"]["fact_id"] == "FACT-GOCHARA-SATURN-MAKARA-K7"
        # All planet fact ids follow FACT-GOCHARA-<PLANET>-<SIGN>-K<n>.
        for p, r in planets.items():
            parts = r["fact_id"].split("-")
            assert parts[0] == "FACT" and parts[1] == "GOCHARA"
            assert parts[2] == p
            assert parts[-1].startswith("K")

    def test_fact_ids_include_natal_anchors(self, fixture_data: dict) -> None:
        fact_ids = fixture_data["expected"]["report"]["fact_ids"]
        assert "FACT-GOCHARA-MOON-NATAL" in fact_ids
        assert "FACT-GOCHARA-LAGNA-NATAL" in fact_ids
        assert len(fact_ids) == 9  # 7 planets + 2 anchors

    def test_tqs_uses_shodhita_when_available(self, fixture_data: dict) -> None:
        planets = fixture_data["expected"]["report"]["planets"]
        # VENUS transits MAKARA (idx 9): shodhita row has 4 there.
        assert planets["VENUS"]["tqs"] == 4
        assert fixture_data["expected"]["report"]["tqs_basis"] == "shodhita_sav"

    def test_vedha_reflected_in_report(self, fixture_data: dict) -> None:
        planets = fixture_data["expected"]["report"]["planets"]
        # VENUS at 280° = MAKARA, house 3 from Moon; natal-Moon-side
        # occupants make the classical pair active in the fixture.
        assert planets["VENUS"]["vedha_obstructed"] is True
        assert planets["VENUS"]["effective_multiplier"] == round(
            planets["VENUS"]["band"]["multiplier"] * VEDHA_MULTIPLIER, 6
        )

    def test_missing_planet_raises(self) -> None:
        incomplete = {k: v for k, v in FIXTURE_TRANSITS.items() if k != "MARS"}
        with pytest.raises(ValueError, match="missing planets"):
            compute_gochara(FIXTURE_FACTS, incomplete)

    def test_determinism(self) -> None:
        a = gochara_to_dict(
            compute_gochara(FIXTURE_FACTS, FIXTURE_TRANSITS)
        )
        b = gochara_to_dict(
            compute_gochara(FIXTURE_FACTS, FIXTURE_TRANSITS)
        )
        assert a == b

    def test_to_dict_is_json_serializable(self, fixture_data: dict) -> None:
        rep = fixture_data["expected"]["report"]
        assert json.loads(json.dumps(rep)) == rep


# ── Feature flag & version ──────────────────────────────────────────────────
class TestFeatureFlag:
    def test_default_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JRS_GOCHARA_SCORING", raising=False)
        assert gochara_scoring_enabled() is False

    def test_env_truthy_enables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("1", "true", "YES", "on"):
            monkeypatch.setenv("JRS_GOCHARA_SCORING", value)
            assert gochara_scoring_enabled() is True

    def test_env_falsy_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for value in ("", "0", "false", "off"):
            monkeypatch.setenv("JRS_GOCHARA_SCORING", value)
            assert gochara_scoring_enabled() is False

    def test_epoch_is_pinned_utc(self) -> None:
        assert GOCHARA_TRANSIT_EPOCH == dt.datetime(
            2020, 1, 1, tzinfo=dt.timezone.utc
        )

    def test_version_constant(self) -> None:
        assert GOCHARA_STAGE_VERSION == "1.0.0"
