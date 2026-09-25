"""Phase 5E: Dasha/transit permissive-gate module tests.

Validates the structural-hierarchy gate (dasha authority authorizes;
transit quality never substitutes), the canonical window anchoring, the
deterministic JSON fixture (``tests/fixtures/dasha_transit/``), and the
feature-flag guard. Einstein at the pinned epoch runs Venus MD / Sun AD
/ Saturn PD — VENUS, SUN and SATURN are authorized, the rest blocked.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from jrs.calculations.dasha_transit import (
    DASHA_TRANSIT_EPOCH,
    DASHA_TRANSIT_STAGE_VERSION,
    GOCHARA_PLANETS,
    MIN_AD_WINDOW_DAYS,
    MIN_PD_WINDOW_DAYS,
    REL_DASHA_TRANSIT_AUTHORIZES,
    REL_DASHA_TRANSIT_BLOCKS,
    compute_dasha_transit,
    dasha_transit_scoring_enabled,
    dasha_transit_to_dict,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "dasha_transit"
    / "fixture_000_einstein.json"
)

FIXTURE_FACTS = {
    "planets": {
        "SUN": {"longitude": 331.32419345824417, "rashi": "MEENA"},
        "MOON": {"longitude": 232.22148712046456, "rashi": "VRISHCHIKA"},
        "MARS": {"longitude": 274.7331682026066, "rashi": "DHANUSHA"},
        "MERCURY": {"longitude": 340.95139065805967, "rashi": "MEENA"},
        "JUPITER": {"longitude": 305.3077339155739, "rashi": "MAKARA"},
        "VENUS": {"longitude": 354.79925006625405, "rashi": "MEENA"},
        "SATURN": {"longitude": 342.01443295977805, "rashi": "MEENA"},
    },
}
BIRTH_DATE = "1879-03-14"


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report() -> dict:
    return dasha_transit_to_dict(
        compute_dasha_transit(FIXTURE_FACTS, birth_date=BIRTH_DATE)
    )


# ── Constants & flag ────────────────────────────────────────────────────────
class TestConstantsAndFlag:
    def test_stage_version(self) -> None:
        assert DASHA_TRANSIT_STAGE_VERSION == "1.0.0"

    def test_pinned_epoch_never_wall_clock(self) -> None:
        assert DASHA_TRANSIT_EPOCH == dt.datetime(
            2020, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc
        )

    def test_min_window_constants(self) -> None:
        assert MIN_AD_WINDOW_DAYS == 3.0
        assert MIN_PD_WINDOW_DAYS == 1.0

    def test_relationship_id_constants(self) -> None:
        assert REL_DASHA_TRANSIT_AUTHORIZES == "REL-DASHA-TRANSIT-AUTHORIZES"
        assert REL_DASHA_TRANSIT_BLOCKS == "REL-DASHA-TRANSIT-BLOCKS"

    def test_gate_planets_match_gochara(self) -> None:
        assert GOCHARA_PLANETS == (
            "SUN",
            "MOON",
            "MARS",
            "MERCURY",
            "JUPITER",
            "VENUS",
            "SATURN",
        )

    def test_flag_default_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JRS_DASHA_TRANSIT_SCORING", raising=False)
        assert dasha_transit_scoring_enabled() is False

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", "on"])
    def test_flag_truthy_values(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("JRS_DASHA_TRANSIT_SCORING", value)
        assert dasha_transit_scoring_enabled() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
    def test_flag_falsy_values(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("JRS_DASHA_TRANSIT_SCORING", value)
        assert dasha_transit_scoring_enabled() is False


# ── Window anchoring ────────────────────────────────────────────────────────
class TestWindowAnchoring:
    def test_active_window_matches_canonical_engine(self) -> None:
        from jrs.engine.dasha import calculate_vimshottari_dasha

        window = calculate_vimshottari_dasha(
            moon_longitude=FIXTURE_FACTS["planets"]["MOON"]["longitude"],
            birth_date_str=BIRTH_DATE,
            target_date=dt.datetime(2020, 1, 1),
        )
        assert window["mahadasha"].upper() == "VENUS"
        assert window["antardasha"].upper() == "SUN"
        assert window["pratyantardasha"].upper() == "SATURN"

    def test_window_payload(self, report: dict) -> None:
        w = report["dasha_window"]
        assert w["mahadasha"] == "VENUS"
        assert w["antardasha"] == "SUN"
        assert w["pratyantardasha"] == "SATURN"
        assert w["start_date"] == "2019-12-04"
        assert w["end_date"] == "2020-01-30"
        assert w["duration_days"] == pytest.approx(57.0)
        assert w["window_degenerate"] is False
        assert list(w["fact_ids"]) == [
            "FACT-DASHA-MD-VENUS",
            "FACT-DASHA-AD-SUN",
            "FACT-DASHA-PD-SATURN",
        ]

    def test_epoch_override_moves_window(self) -> None:
        moved = dasha_transit_to_dict(
            compute_dasha_transit(
                FIXTURE_FACTS,
                birth_date=BIRTH_DATE,
                epoch=dt.datetime(2050, 6, 1, tzinfo=dt.timezone.utc),
            )
        )
        assert moved["dasha_window"]["mahadasha"] == "MOON"
        assert moved["dasha_window"]["antardasha"] == "VENUS"
        assert moved["dasha_window"]["pratyantardasha"] == "MOON"

    def test_timezone_aware_and_naive_epochs_agree(self) -> None:
        aware = compute_dasha_transit(
            FIXTURE_FACTS, birth_date=BIRTH_DATE, epoch=DASHA_TRANSIT_EPOCH
        )
        naive = compute_dasha_transit(
            FIXTURE_FACTS,
            birth_date=BIRTH_DATE,
            epoch=dt.datetime(2020, 1, 1),
        )
        assert dasha_transit_to_dict(aware) == dasha_transit_to_dict(naive)

    def test_epoch_utc_echo(self, report: dict) -> None:
        assert report["epoch_utc"] == "2020-01-01T00:00:00+0000"


# ── Gate decisions ──────────────────────────────────────────────────────────
class TestGateDecisions:
    def test_authorized_planets(self, report: dict) -> None:
        assert report["planets"]["VENUS"]["decision"] == "AUTHORIZED"
        assert report["planets"]["VENUS"]["authorized_by"] == "MD"
        assert report["planets"]["SUN"]["decision"] == "AUTHORIZED"
        assert report["planets"]["SUN"]["authorized_by"] == "AD"
        assert report["planets"]["SATURN"]["decision"] == "AUTHORIZED"
        assert report["planets"]["SATURN"]["authorized_by"] == "PD"

    def test_blocked_planets(self, report: dict) -> None:
        for body in ("MOON", "MARS", "MERCURY", "JUPITER"):
            entry = report["planets"][body]
            assert entry["decision"] == "BLOCKED", body
            assert entry["authorized_by"] is None, body

    def test_summary_counts(self, report: dict) -> None:
        assert report["summary"] == {"authorized": 3, "blocked": 4}

    def test_relationship_ids_follow_decision(self, report: dict) -> None:
        for body, entry in report["planets"].items():
            expected = (
                REL_DASHA_TRANSIT_AUTHORIZES
                if entry["decision"] == "AUTHORIZED"
                else REL_DASHA_TRANSIT_BLOCKS
            )
            assert entry["relationship"] == expected, body

    def test_all_seven_bodies_reported(self, report: dict) -> None:
        assert set(report["planets"]) == set(GOCHARA_PLANETS)

    def test_fact_ids_complete(self, report: dict) -> None:
        assert len(report["fact_ids"]) == 10  # 3 window + 7 gate facts
        assert report["fact_ids"][:3] == [
            "FACT-DASHA-MD-VENUS",
            "FACT-DASHA-AD-SUN",
            "FACT-DASHA-PD-SATURN",
        ]
        for body in GOCHARA_PLANETS:
            assert f"FACT-DASHA-TRANSIT-GATE-{body}" in report["fact_ids"]

    def test_gate_policy_declares_authority_semantics(
        self, report: dict
    ) -> None:
        assert report["gate_policy"]["authority"] == "dasha_window_only"


# ── Authority semantics ─────────────────────────────────────────────────────
class TestAuthoritySemantics:
    @staticmethod
    def _facts_with_gochara(bodies: dict[str, dict]) -> dict:
        facts = {
            "planets": dict(FIXTURE_FACTS["planets"]),
            "gochara": {"planets": bodies},
        }
        return facts

    def test_transit_quality_never_substitutes_authority(self) -> None:
        # MOON transits with a SUPPORTIVE band but holds no dasha
        # authority in the pinned window -> still BLOCKED.
        facts = self._facts_with_gochara(
            {
                "MOON": {
                    "transit_rashi": "KARKA",
                    "house_from_moon": 9,
                    "tqs": 33,
                    "band": {"label": "SUPPORTIVE"},
                    "vedha_obstructed": False,
                }
            }
        )
        gated = dasha_transit_to_dict(compute_dasha_transit(facts, birth_date=BIRTH_DATE))
        moon = gated["planets"]["MOON"]
        assert moon["transit_state"]["band"] == "SUPPORTIVE"
        assert moon["decision"] == "BLOCKED"
        assert moon["relationship"] == REL_DASHA_TRANSIT_BLOCKS

    def test_gochara_report_transit_state_used(self) -> None:
        facts = self._facts_with_gochara(
            {
                "VENUS": {
                    "transit_rashi": "MEENA",
                    "house_from_moon": 5,
                    "tqs": 12,
                    "band": {"label": "AFFLICTED"},
                    "vedha_obstructed": True,
                }
            }
        )
        gated = dasha_transit_to_dict(compute_dasha_transit(facts, birth_date=BIRTH_DATE))
        venus = gated["planets"]["VENUS"]
        assert venus["transit_state"]["basis"] == "gochara_report"
        assert venus["transit_state"]["band"] == "AFFLICTED"
        # AFFLICTED transit quality does not revoke dasha authority.
        assert venus["decision"] == "AUTHORIZED"
        assert venus["relationship"] == REL_DASHA_TRANSIT_AUTHORIZES

    def test_whole_sign_fallback_without_gochara(self, report: dict) -> None:
        # No gochara report in FIXTURE_FACTS -> minimal whole-sign state.
        state = report["planets"]["VENUS"]["transit_state"]
        assert state["basis"] == "whole_sign_fallback"
        assert state["band"] == "NEUTRAL"
        assert state["tqs"] is None
        # VENUS in MEENA counted from natal MOON in VRISHCHIKA -> house 5.
        assert state["house_from_moon"] == 5

    def test_missing_moon_longitude_raises(self) -> None:
        with pytest.raises(ValueError, match="MOON longitude"):
            compute_dasha_transit(
                {"planets": {"SUN": {"longitude": 1.0, "rashi": "MESHA"}}},
                birth_date=BIRTH_DATE,
            )

    def test_missing_rashi_in_fallback_raises(self) -> None:
        # Deep-copy the per-planet dicts: FIXTURE_FACTS is a shared
        # module-scope fixture and must not be mutated.
        facts = {
            "planets": {
                body: dict(entry) for body, entry in FIXTURE_FACTS["planets"].items()
            }
        }
        del facts["planets"]["MARS"]["rashi"]
        with pytest.raises(ValueError, match="rashi for body: MARS"):
            compute_dasha_transit(facts, birth_date=BIRTH_DATE)

    def test_moon_anchor_never_raises_without_own_transit(self) -> None:
        facts = {"planets": dict(FIXTURE_FACTS["planets"])}
        gated = dasha_transit_to_dict(
            compute_dasha_transit(facts, birth_date=BIRTH_DATE)
        )
        moon_state = gated["planets"]["MOON"]["transit_state"]
        assert moon_state["basis"] == "natal_anchor"
        assert moon_state["house_from_moon"] == 1
        assert moon_state["transit_rashi"] == "VRISHCHIKA"


# ── Determinism & serialization ─────────────────────────────────────────────
class TestDeterminism:
    def test_identical_inputs_identical_reports(self) -> None:
        a = dasha_transit_to_dict(
            compute_dasha_transit(FIXTURE_FACTS, birth_date=BIRTH_DATE)
        )
        b = dasha_transit_to_dict(
            compute_dasha_transit(FIXTURE_FACTS, birth_date=BIRTH_DATE)
        )
        assert a == b

    def test_serialization_json_safe(self, report: dict) -> None:
        round_trip = json.loads(json.dumps(report))
        assert round_trip == report


# ── Fixture contract ────────────────────────────────────────────────────────
class TestFixtureContract:
    def test_fixture_window_matches(self, fixture_data: dict, report: dict) -> None:
        assert fixture_data["expected"]["dasha_window"] == report["dasha_window"]

    def test_fixture_decisions_match(self, fixture_data: dict, report: dict) -> None:
        assert fixture_data["expected"]["decisions"] == {
            body: entry["decision"] for body, entry in report["planets"].items()
        }

    def test_fixture_authorized_by_match(
        self, fixture_data: dict, report: dict
    ) -> None:
        assert fixture_data["expected"]["authorized_by"] == {
            body: entry["authorized_by"] for body, entry in report["planets"].items()
        }

    def test_fixture_summary_match(self, fixture_data: dict, report: dict) -> None:
        assert fixture_data["expected"]["summary"] == report["summary"]

    def test_fixture_fact_ids_match(self, fixture_data: dict, report: dict) -> None:
        assert fixture_data["expected"]["fact_ids"] == report["fact_ids"]

    def test_fixture_relationships_match(
        self, fixture_data: dict, report: dict
    ) -> None:
        assert fixture_data["expected"]["relationships"] == {
            body: entry["relationship"].replace("REL-DASHA-TRANSIT-", "")
            for body, entry in report["planets"].items()
        }
