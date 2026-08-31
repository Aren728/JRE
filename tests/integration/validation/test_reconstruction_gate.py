"""Reconstruction Gate — Phase E1/E2/E4 Integration Test.

Loads ALL immutable chart fixtures (chart_001 through chart_005), passes
raw_birth_data through the JRE fact-generation pipeline (JyotishService),
and asserts exact matches against the expected_canonical_facts.

If a mismatch occurs, the failure message explicitly identifies the
layer of failure:
  - "Astronomical Truth Mismatch" for longitude discrepancies.
  - "Jyotisha Transformation Mismatch" for rashi/nakshatra/pada errors.
  - "House Computation Mismatch" for bhava assignment errors.
  - "Navamsha Computation Mismatch" for D9 sign errors.

This test gates the empirical validation pipeline: it must PASS before
any predictive-layer work proceeds.

Usage:
    pytest tests/integration/validation/test_reconstruction_gate.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# ── Fixtures Discovery ─────────────────────────────────────────────────────

FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "fixtures"
    / "validation_charts"
)

# Modern personalities directory
MODERN_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "fixtures"
    / "modern_personalities"
)

# All chart fixture files in the cohort (validation + modern)
CHART_FIXTURES: list[Path] = sorted(
    list(FIXTURES_DIR.glob("chart_*.json"))
    + list(MODERN_DIR.glob("chart_*.json"))
    if MODERN_DIR.exists()
    else FIXTURES_DIR.glob("chart_*.json")
)

# Fallback if no fixtures discovered (shouldn't happen)
assert CHART_FIXTURES, f"No chart fixtures found in {FIXTURES_DIR}"

TOLERANCE_LONGITUDE = 1e-4  # degrees — sub-arcsecond precision
TOLERANCE_DEGREE_IN_RASHI = 1e-4


def _load_fixture(path: Path) -> dict[str, Any]:
    """Load and parse a chart fixture JSON."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ── Parametrized Fixtures ──────────────────────────────────────────────────


@pytest.fixture(params=CHART_FIXTURES, ids=lambda p: p.stem)
def fixture_path(request: pytest.FixtureRequest) -> Path:
    """Parametrized fixture: yields each chart fixture path."""
    return request.param


@pytest.fixture()
def fixture_data(fixture_path: Path) -> dict[str, Any]:
    """Parsed JSON from the chart fixture."""
    return _load_fixture(fixture_path)


@pytest.fixture()
def chart_subject(fixture_data: dict[str, Any]) -> str:
    """Human-readable subject name for test IDs."""
    return fixture_data.get("_meta", {}).get("subject", "Unknown")


@pytest.fixture()
def generated_chart(fixture_data: dict[str, Any]) -> Any:
    """Run the JRE pipeline on the fixture birth data.

    Returns the NatalChart produced by JyotishService.chart().
    """
    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    raw = fixture_data["raw_birth_data"]
    birth = BirthData(
        date=raw["date"],
        time=raw["time"],
        timezone=raw["timezone"],
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
    )
    svc = JyotishService()
    return svc.chart(birth)


# ── D9 (Navamsha) Helper ───────────────────────────────────────────────────

_SIGN_TYPES: dict[int, str] = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}


def _compute_d9_sign(longitude_used: float, rashi_order: list) -> str:
    """Classical navamsha sign from a sidereal longitude.

    Fire signs  → navamsha starts from the same sign.
    Earth signs → navamsha starts from sign + 5 (mod 12).
    Air signs   → navamsha starts from sign + 4 (mod 12).
    Water signs → navamsha starts from sign + 8 (mod 12).
    """
    sign_index = int(longitude_used / 30.0)
    degree_in_sign = longitude_used - (sign_index * 30.0)
    navamsha_within_sign = int(degree_in_sign / (30.0 / 9.0))

    sign_type = _SIGN_TYPES[sign_index]
    if sign_type == "fire":
        start = sign_index
    elif sign_type == "earth":
        start = (sign_index + 5) % 12
    elif sign_type == "air":
        start = (sign_index + 4) % 12
    else:  # water
        start = (sign_index + 8) % 12

    d9_index = (start + navamsha_within_sign) % 12
    return rashi_order[d9_index].value


# ── Planetary Fact Assertions ──────────────────────────────────────────────


class TestLagnaReconstruction:
    """Verify the Lagna (ascendant) is reconstructed identically."""

    def test_lagna_rashi(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"]["rashi"]
        actual = generated_chart.lagna.rashi.value
        assert actual == expected, (
            f"[{chart_subject}] Jyotisha Transformation Mismatch: "
            f"Expected Lagna Rashi {expected}, got {actual}"
        )

    def test_lagna_nakshatra(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"]["nakshatra"]
        actual = generated_chart.lagna.nakshatra.value
        assert actual == expected, (
            f"[{chart_subject}] Jyotisha Transformation Mismatch: "
            f"Expected Lagna Nakshatra {expected}, got {actual}"
        )

    def test_lagna_pada(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"]["pada"]
        actual = generated_chart.lagna.pada.value
        assert actual == expected, (
            f"[{chart_subject}] Jyotisha Transformation Mismatch: "
            f"Expected Lagna Pada {expected}, got {actual}"
        )

    def test_lagna_nakshatra_lord(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"]["nakshatra_lord"]
        actual = generated_chart.lagna.nakshatra_lord.value
        assert actual == expected, (
            f"[{chart_subject}] Jyotisha Transformation Mismatch: "
            f"Expected Lagna Nakshatra Lord {expected}, got {actual}"
        )

    def test_lagna_longitude(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"][
            "ascendant_longitude_deg"
        ]
        actual = generated_chart.lagna.ascendant_longitude_deg
        assert abs(actual - expected) < TOLERANCE_LONGITUDE, (
            f"[{chart_subject}] Astronomical Truth Mismatch: "
            f"Expected Lagna Longitude {expected:.6f}°, got {actual:.6f}° "
            f"(delta={abs(actual - expected):.6f}°)"
        )

    def test_lagna_degree_in_rashi(
        self, generated_chart: Any, fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        expected = fixture_data["expected_canonical_facts"]["lagna"]["degree_in_rashi"]
        actual = generated_chart.lagna.degree_in_rashi
        assert abs(actual - expected) < TOLERANCE_DEGREE_IN_RASHI, (
            f"[{chart_subject}] Jyotisha Transformation Mismatch: "
            f"Expected Lagna degree_in_rashi {expected:.6f}°, got {actual:.6f}°"
        )


# ── Planetary Fact Assertions ──────────────────────────────────────────────


class TestPlanetaryReconstruction:
    """Verify every planet's natal facts are reconstructed identically.

    Checks: longitude (tropical, sidereal, used), rashi, nakshatra,
    nakshatra_lord, pada, retrograde, and D9 sign.
    """

    PLANETS = [
        "SUN", "MOON", "MARS", "MERCURY", "JUPITER",
        "VENUS", "SATURN", "RAHU", "KETU",
    ]

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        generated_chart: Any,
        fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        self.chart = generated_chart
        self.expected = fixture_data["expected_canonical_facts"]["planets"]
        self.subject = chart_subject

    def _get_planet_state(self, planet_name: str) -> Any:
        """Look up a PlanetState by BodyId value."""
        from astronomy.models import BodyId

        body_id = BodyId(planet_name)
        for ps in self.chart.planet_states:
            if ps.body is body_id:
                return ps
        raise AssertionError(f"Planet {planet_name} not found in chart")

    # ── Tropical Longitude ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_longitude_tropical(self, planet: str) -> None:
        expected = self.expected[planet]["longitude_tropical"]
        actual = self._get_planet_state(planet).longitude_tropical
        assert abs(actual - expected) < TOLERANCE_LONGITUDE, (
            f"[{self.subject}] Astronomical Truth Mismatch: Expected {planet} "
            f"Tropical Longitude {expected:.6f}°, got {actual:.6f}° "
            f"(delta={abs(actual - expected):.6f}°)"
        )

    # ── Sidereal Longitude ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_longitude_sidereal(self, planet: str) -> None:
        expected = self.expected[planet]["longitude_sidereal"]
        actual = self._get_planet_state(planet).longitude_sidereal
        assert actual is not None, (
            f"[{self.subject}] Astronomical Truth Mismatch: "
            f"{planet} sidereal longitude is None"
        )
        assert abs(actual - expected) < TOLERANCE_LONGITUDE, (
            f"[{self.subject}] Astronomical Truth Mismatch: Expected {planet} "
            f"Sidereal Longitude {expected:.6f}°, got {actual:.6f}° "
            f"(delta={abs(actual - expected):.6f}°)"
        )

    # ── Rashi ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_rashi(self, planet: str) -> None:
        expected = self.expected[planet]["rashi"]
        actual = self._get_planet_state(planet).rashi.value
        assert actual == expected, (
            f"[{self.subject}] Jyotisha Transformation Mismatch: "
            f"Expected {planet} Rashi {expected}, got {actual}"
        )

    # ── Nakshatra ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_nakshatra(self, planet: str) -> None:
        expected = self.expected[planet]["nakshatra"]
        actual = self._get_planet_state(planet).nakshatra.value
        assert actual == expected, (
            f"[{self.subject}] Jyotisha Transformation Mismatch: "
            f"Expected {planet} Nakshatra {expected}, got {actual}"
        )

    # ── Nakshatra Lord ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_nakshatra_lord(self, planet: str) -> None:
        expected = self.expected[planet]["nakshatra_lord"]
        actual = self._get_planet_state(planet).nakshatra_lord.value
        assert actual == expected, (
            f"[{self.subject}] Jyotisha Transformation Mismatch: "
            f"Expected {planet} Nakshatra Lord {expected}, got {actual}"
        )

    # ── Pada ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_pada(self, planet: str) -> None:
        expected = self.expected[planet]["pada"]
        actual = self._get_planet_state(planet).pada.value
        assert actual == expected, (
            f"[{self.subject}] Jyotisha Transformation Mismatch: "
            f"Expected {planet} Pada {expected}, got {actual}"
        )

    # ── Retrograde Status ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_retrograde(self, planet: str) -> None:
        expected = self.expected[planet]["retrograde"]
        actual = self._get_planet_state(planet).retrograde.value
        assert actual == expected, (
            f"[{self.subject}] Astronomical Truth Mismatch: "
            f"Expected {planet} Retrograde Status {expected}, got {actual}"
        )

    # ── D9 (Navamsha) Sign ──

    @pytest.mark.parametrize("planet", PLANETS)
    def test_d9_sign(self, planet: str) -> None:
        from jyotish.rashi import RASHI_ORDER

        expected = self.expected[planet]["d9_sign"]
        actual = _compute_d9_sign(
            self._get_planet_state(planet).longitude_used,
            list(RASHI_ORDER),
        )
        assert actual == expected, (
            f"[{self.subject}] Navamsha Computation Mismatch: "
            f"Expected {planet} D9 Sign {expected}, got {actual}"
        )


# ── House (Bhava) Assertions ───────────────────────────────────────────────


class TestHouseReconstruction:
    """Verify all 12 house assignments are reconstructed identically."""

    HOUSE_NUMBERS = list(range(1, 13))

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        generated_chart: Any,
        fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        self.chart = generated_chart
        self.expected = fixture_data["expected_canonical_facts"]["houses"]
        self.subject = chart_subject

    @pytest.mark.parametrize("house_num", HOUSE_NUMBERS)
    def test_house_rashi(self, house_num: int) -> None:
        expected_rashi = self.expected[str(house_num)]["rashi"]
        bhava = self.chart.bhavas[house_num - 1]
        actual_rashi = bhava.rashi.value
        assert actual_rashi == expected_rashi, (
            f"[{self.subject}] House Computation Mismatch: "
            f"Expected House {house_num} Rashi {expected_rashi}, got {actual_rashi}"
        )

    @pytest.mark.parametrize("house_num", HOUSE_NUMBERS)
    def test_house_lord(self, house_num: int) -> None:
        expected_lord = self.expected[str(house_num)]["lord"]
        bhava = self.chart.bhavas[house_num - 1]
        actual_lord = bhava.house_lord.value
        assert actual_lord == expected_lord, (
            f"[{self.subject}] House Computation Mismatch: "
            f"Expected House {house_num} Lord {expected_lord}, got {actual_lord}"
        )

    @pytest.mark.parametrize("house_num", HOUSE_NUMBERS)
    def test_house_occupants(self, house_num: int) -> None:
        expected_occupants = self.expected[str(house_num)]["occupants"]
        bhava = self.chart.bhavas[house_num - 1]
        actual_occupants = sorted(o.value for o in bhava.occupants)
        assert actual_occupants == sorted(expected_occupants), (
            f"[{self.subject}] House Computation Mismatch: "
            f"Expected House {house_num} Occupants "
            f"{sorted(expected_occupants)}, got {actual_occupants}"
        )


# ── Comprehensive Reconstruction Gate ──────────────────────────────────────


class TestReconstructionGate:
    """Full end-to-end gate: all facts must match or the pipeline is broken."""

    def test_full_reconstruction_matches_fixture(
        self,
        generated_chart: Any,
        fixture_data: dict[str, Any],
        chart_subject: str,
    ) -> None:
        """Master assertion: every single canonical fact matches.

        This is a single test to provide a clear PASS/FAIL signal.
        Individual sub-tests above provide the diagnostic breakdown.
        """
        from astronomy.models import BodyId
        from jyotish.rashi import RASHI_ORDER

        expected = fixture_data["expected_canonical_facts"]
        mismatches: list[str] = []

        # ── Lagna ──
        lagna = generated_chart.lagna
        exp_lagna = expected["lagna"]
        if lagna.rashi.value != exp_lagna["rashi"]:
            mismatches.append(
                f"Lagna Rashi: expected {exp_lagna['rashi']}, "
                f"got {lagna.rashi.value}"
            )
        if lagna.nakshatra.value != exp_lagna["nakshatra"]:
            mismatches.append(
                f"Lagna Nakshatra: expected {exp_lagna['nakshatra']}, "
                f"got {lagna.nakshatra.value}"
            )
        if lagna.pada.value != exp_lagna["pada"]:
            mismatches.append(
                f"Lagna Pada: expected {exp_lagna['pada']}, "
                f"got {lagna.pada.value}"
            )

        # ── Planets ──
        for planet_name, exp_planet in expected["planets"].items():
            body_id = BodyId(planet_name)
            ps = None
            for state in generated_chart.planet_states:
                if state.body is body_id:
                    ps = state
                    break
            if ps is None:
                mismatches.append(f"{planet_name}: NOT FOUND in pipeline output")
                continue

            if abs(ps.longitude_tropical - exp_planet["longitude_tropical"]) > TOLERANCE_LONGITUDE:
                mismatches.append(
                    f"{planet_name} Tropical Longitude: expected "
                    f"{exp_planet['longitude_tropical']:.6f}°, "
                    f"got {ps.longitude_tropical:.6f}°"
                )
            if ps.longitude_sidereal is not None and abs(
                ps.longitude_sidereal - exp_planet["longitude_sidereal"]
            ) > TOLERANCE_LONGITUDE:
                mismatches.append(
                    f"{planet_name} Sidereal Longitude: expected "
                    f"{exp_planet['longitude_sidereal']:.6f}°, "
                    f"got {ps.longitude_sidereal:.6f}°"
                )
            if ps.rashi.value != exp_planet["rashi"]:
                mismatches.append(
                    f"{planet_name} Rashi: expected {exp_planet['rashi']}, "
                    f"got {ps.rashi.value}"
                )
            if ps.nakshatra.value != exp_planet["nakshatra"]:
                mismatches.append(
                    f"{planet_name} Nakshatra: expected {exp_planet['nakshatra']}, "
                    f"got {ps.nakshatra.value}"
                )
            if ps.pada.value != exp_planet["pada"]:
                mismatches.append(
                    f"{planet_name} Pada: expected {exp_planet['pada']}, "
                    f"got {ps.pada.value}"
                )
            if ps.retrograde.value != exp_planet["retrograde"]:
                mismatches.append(
                    f"{planet_name} Retrograde: expected {exp_planet['retrograde']}, "
                    f"got {ps.retrograde.value}"
                )
            d9 = _compute_d9_sign(ps.longitude_used, list(RASHI_ORDER))
            if d9 != exp_planet["d9_sign"]:
                mismatches.append(
                    f"{planet_name} D9 Sign: expected {exp_planet['d9_sign']}, "
                    f"got {d9}"
                )

        # ── Houses ──
        for house_num_str, exp_house in expected["houses"].items():
            house_num = int(house_num_str)
            bhava = generated_chart.bhavas[house_num - 1]
            if bhava.rashi.value != exp_house["rashi"]:
                mismatches.append(
                    f"House {house_num} Rashi: expected {exp_house['rashi']}, "
                    f"got {bhava.rashi.value}"
                )
            if bhava.house_lord.value != exp_house["lord"]:
                mismatches.append(
                    f"House {house_num} Lord: expected {exp_house['lord']}, "
                    f"got {bhava.house_lord.value}"
                )
            actual_occ = sorted(o.value for o in bhava.occupants)
            if actual_occ != sorted(exp_house["occupants"]):
                mismatches.append(
                    f"House {house_num} Occupants: expected "
                    f"{sorted(exp_house['occupants'])}, got {actual_occ}"
                )

        # ── Gate Verdict ──
        assert not mismatches, (
            f"RECONSTRUCTION GATE FAILED [{chart_subject}] — "
            f"pipeline produced divergent facts:\n"
            + "\n".join(f"  • {m}" for m in mismatches)
        )

    def test_fixture_is_immutable(
        self, fixture_data: dict[str, Any], chart_subject: str,
    ) -> None:
        """Verify the fixture itself is well-formed and complete."""
        raw = fixture_data["raw_birth_data"]
        assert "date" in raw
        assert "time" in raw
        assert "timezone" in raw
        assert "latitude" in raw
        assert "longitude" in raw

        expected = fixture_data["expected_canonical_facts"]
        assert "lagna" in expected
        assert "planets" in expected
        assert "houses" in expected
        assert len(expected["planets"]) == 9, (
            f"[{chart_subject}] Expected 9 planets, got {len(expected['planets'])}"
        )
        assert len(expected["houses"]) == 12, (
            f"[{chart_subject}] Expected 12 houses, got {len(expected['houses'])}"
        )

        known_events = fixture_data["known_events"]
        assert len(known_events) >= 2, (
            f"[{chart_subject}] Expected at least 2 known events, "
            f"got {len(known_events)}"
        )
        assert all("event_id" in e for e in known_events)
        assert all("domain" in e for e in known_events)

    def test_fixture_config_matches_pipeline_defaults(
        self, fixture_data: dict[str, Any], chart_subject: str,
    ) -> None:
        """Verify the fixture documents the same config the pipeline uses."""
        from jyotish.config import load_config

        config = load_config()
        meta = fixture_data["_meta"]["pipeline_config"]
        assert meta["zodiac_mode"] == config.zodiac_mode.value, (
            f"[{chart_subject}] zodiac_mode mismatch"
        )
        assert meta["ayanamsa"] == config.ayanamsa.value, (
            f"[{chart_subject}] ayanamsa mismatch"
        )
        assert meta["house_system"] == config.house_system.value, (
            f"[{chart_subject}] house_system mismatch"
        )
        assert meta["node_model"] == config.node_model.value, (
            f"[{chart_subject}] node_model mismatch"
        )
