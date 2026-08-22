"""Unit tests for Nakshatra Activation models."""

from __future__ import annotations

import json

import pytest

from jyotish import BodyId, NakshatraId, Pada, PlanetState, RashiId, RetrogradeState
from jyotish.models import DmsValue
from nakshatra_activation.models import (
    NAKSHATRA_ACTIVATION_VERSION,
    NakshatraActivation,
    NakshatraActivationReport,
    NakshatraRelationshipType,
)


def _make_planet_state(
    body: BodyId = BodyId.MOON,
    longitude: float = 10.0,
    rashi: RashiId = RashiId.MESHA,
    nakshatra: NakshatraId = NakshatraId.ASHWINI,
    pada: Pada = Pada.PADA_1,
) -> PlanetState:
    """Helper to create a PlanetState for testing."""
    return PlanetState(
        body=body,
        longitude_tropical=longitude,
        longitude_sidereal=longitude,
        longitude_used=longitude,
        dms=DmsValue(degrees=int(longitude), minutes=0, seconds=0.0, sign=0),
        rashi=rashi,
        degree_in_rashi=longitude % 30.0,
        nakshatra=nakshatra,
        nakshatra_lord=BodyId.KETU,
        pada=pada,
        degree_in_nakshatra=longitude % (360.0 / 27.0),
        latitude=0.0,
        speed_longitude=13.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T00:00:00Z",
        julian_day_ut=2451544.5,
        provider_id="test",
        ephemeris_version="test",
    )


class TestNakshatraRelationshipType:
    """Tests for the NakshatraRelationshipType enum."""

    def test_all_types_have_string_values(self) -> None:
        for t in NakshatraRelationshipType:
            assert isinstance(t.value, str)
            assert t.value == t.name

    def test_type_count(self) -> None:
        assert len(NakshatraRelationshipType) == 6

    def test_type_from_value(self) -> None:
        occ = NakshatraRelationshipType("NAKSHATRA_OCCUPANCY")
        assert occ is NakshatraRelationshipType.NAKSHATRA_OCCUPANCY

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError):
            NakshatraRelationshipType("INVALID")

    def test_all_six_types_exist(self) -> None:
        NRT = NakshatraRelationshipType
        assert NRT.NAKSHATRA_OCCUPANCY.value == "NAKSHATRA_OCCUPANCY"
        assert NRT.NAKSHATRA_LORD_ACTIVATION.value == "NAKSHATRA_LORD_ACTIVATION"
        assert NRT.TRANSIT_NAKSHATRA_INGRESS.value == "TRANSIT_NAKSHATRA_INGRESS"
        assert NRT.NATAL_NAKSHATRA_ACTIVATION.value == "NATAL_NAKSHATRA_ACTIVATION"
        assert NRT.MUTUAL_NAKSHATRA_EXCHANGE.value == "MUTUAL_NAKSHATRA_EXCHANGE"
        assert NRT.NAKSHATRA_DEPENDENCY.value == "NAKSHATRA_DEPENDENCY"


class TestNakshatraActivation:
    """Tests for the NakshatraActivation dataclass."""

    def test_creation(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        assert activation.source_planet == BodyId.MOON
        assert activation.nakshatra == NakshatraId.ASHWINI
        assert activation.relationship_type == NakshatraRelationshipType.NAKSHATRA_OCCUPANCY

    def test_frozen(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        with pytest.raises(AttributeError):
            activation.source_planet = BodyId.SUN  # type: ignore[misc]

    def test_deterministic_id_computed(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        assert activation.deterministic_id != ""
        assert len(activation.deterministic_id) == 64  # SHA-256 hex

    def test_deterministic_id_same_for_equal_inputs(self) -> None:
        state1 = _make_planet_state()
        state2 = _make_planet_state()
        a1 = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state1,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        a2 = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state2,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        assert a1.deterministic_id == a2.deterministic_id

    def test_deterministic_id_different_for_different_inputs(self) -> None:
        state = _make_planet_state()
        a1 = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        a2 = NakshatraActivation(
            source_planet=BodyId.SUN,
            source_position=state,
            nakshatra=NakshatraId.ROHINI,
            nakshatra_lord=BodyId.MOON,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_LORD_ACTIVATION,
        )
        assert a1.deterministic_id != a2.deterministic_id

    def test_to_dict(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        d = activation.to_dict()
        assert d["source_planet"] == "MOON"
        assert d["nakshatra"] == "ASHWINI"
        assert d["nakshatra_lord"] == "KETU"
        assert d["relationship_type"] == "NAKSHATRA_OCCUPANCY"

    def test_to_dict_deterministic(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        d1 = activation.to_dict()
        d2 = activation.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestNakshatraActivationReport:
    """Tests for the NakshatraActivationReport dataclass."""

    def test_creation(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        report = NakshatraActivationReport(activations=(activation,))
        assert len(report.activations) == 1

    def test_result_for_planet(self) -> None:
        state = _make_planet_state()
        a1 = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        a2 = NakshatraActivation(
            source_planet=BodyId.SUN,
            source_position=state,
            nakshatra=NakshatraId.ROHINI,
            nakshatra_lord=BodyId.MOON,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        report = NakshatraActivationReport(activations=(a1, a2))
        moon_activations = report.result_for(BodyId.MOON)
        assert len(moon_activations) == 1
        assert moon_activations[0].source_planet == BodyId.MOON

    def test_result_for_nakshatra(self) -> None:
        state = _make_planet_state()
        a1 = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        report = NakshatraActivationReport(activations=(a1,))
        ashwini = report.result_for_nakshatra(NakshatraId.ASHWINI)
        assert len(ashwini) == 1

    def test_to_dict(self) -> None:
        state = _make_planet_state()
        activation = NakshatraActivation(
            source_planet=BodyId.MOON,
            source_position=state,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            natal_lord_state=None,
            transit_lord_state=None,
            relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
        )
        report = NakshatraActivationReport(activations=(activation,))
        d = report.to_dict()
        assert d["activation_count"] == 1
        assert len(d["activations"]) == 1
        assert d["version"] == NAKSHATRA_ACTIVATION_VERSION
