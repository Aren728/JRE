"""Unit tests for NakshatraActivationService."""

from __future__ import annotations

import json

import pytest

from jyotish import BodyId, NakshatraId, Pada, PlanetState, RashiId, RetrogradeState
from nakshatra_activation.errors import InvalidActivationRequestError
from nakshatra_activation.models import (
    NakshatraActivationReport,
    NakshatraRelationshipType,
)
from nakshatra_activation.service import NakshatraActivationService


class TestServiceInit:
    """Tests for NakshatraActivationService initialization."""

    def test_default_init(self) -> None:
        service = NakshatraActivationService()
        assert service is not None


class TestComputeActivations:
    """Tests for the compute_activations method."""

    def test_basic_occupancy(self, simple_planet_states: tuple[PlanetState, ...]) -> None:
        """Test that occupancy activations are computed for each planet."""
        service = NakshatraActivationService()
        report = service.compute_activations(simple_planet_states)

        assert isinstance(report, NakshatraActivationReport)
        assert len(report.activations) > 0

        # Check that each planet has an occupancy activation
        occupancy = [
            a for a in report.activations
            if a.relationship_type == NakshatraRelationshipType.NAKSHATRA_OCCUPANCY
        ]
        assert len(occupancy) == len(simple_planet_states)

        # Check Moon is in ASHWINI
        moon_occ = [a for a in occupancy if a.source_planet == BodyId.MOON]
        assert len(moon_occ) == 1
        assert moon_occ[0].nakshatra == NakshatraId.ASHWINI
        assert moon_occ[0].nakshatra_lord == BodyId.KETU

        # Check Sun is in ROHINI
        sun_occ = [a for a in occupancy if a.source_planet == BodyId.SUN]
        assert len(sun_occ) == 1
        assert sun_occ[0].nakshatra == NakshatraId.ROHINI
        assert sun_occ[0].nakshatra_lord == BodyId.MOON

    def test_lord_activations(self, simple_planet_states: tuple[PlanetState, ...]) -> None:
        """Test that lord activations are computed."""
        service = NakshatraActivationService()
        report = service.compute_activations(simple_planet_states)

        lord_activations = [
            a for a in report.activations
            if a.relationship_type == NakshatraRelationshipType.NAKSHATRA_LORD_ACTIVATION
        ]
        # Sun in ROHINI (lord = MOON) should produce a lord activation
        sun_lord = [
            a for a in lord_activations
            if a.source_planet == BodyId.SUN and a.nakshatra_lord == BodyId.MOON
        ]
        assert len(sun_lord) == 1

    def test_shared_nakshatra_dependencies(
        self, shared_nakshatra_states: tuple[PlanetState, ...]
    ) -> None:
        """Test that shared nakshatras produce dependency activations."""
        service = NakshatraActivationService()
        report = service.compute_activations(shared_nakshatra_states)

        dependencies = [
            a for a in report.activations
            if a.relationship_type == NakshatraRelationshipType.NAKSHATRA_DEPENDENCY
        ]
        # Both Moon and Mercury in ASHWINI should produce 2 dependency activations
        assert len(dependencies) == 2

        # Both should reference ASHWINI
        for dep in dependencies:
            assert dep.nakshatra == NakshatraId.ASHWINI

    def test_transit_ingress(self, simple_planet_states: tuple[PlanetState, ...]) -> None:
        """Test that transit ingress activations are computed."""
        from jyotish.models import DmsValue

        # Create a transit Moon that enters ASHWINI (same nakshatra as natal Moon)
        transit_moon = PlanetState(
            body=BodyId.MOON,
            longitude_tropical=5.0,
            longitude_sidereal=5.0,
            longitude_used=5.0,
            dms=DmsValue(degrees=5, minutes=0, seconds=0.0, sign=0),
            rashi=RashiId.MESHA,
            degree_in_rashi=5.0,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            pada=Pada.PADA_1,
            degree_in_nakshatra=5.0,
            latitude=0.0,
            speed_longitude=13.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-06-01T00:00:00Z",
            julian_day_ut=2451694.5,
            provider_id="test",
            ephemeris_version="test",
        )

        service = NakshatraActivationService()
        report = service.compute_activations(
            simple_planet_states,
            transit_states=(transit_moon,),
            activation_window_start="2000-06-01T00:00:00Z",
            activation_window_end="2000-06-15T00:00:00Z",
        )

        ingress = [
            a for a in report.activations
            if a.relationship_type == NakshatraRelationshipType.TRANSIT_NAKSHATRA_INGRESS
        ]
        # Transit Moon in ASHWINI (natal Moon's nakshatra) should produce ingress
        assert len(ingress) >= 1
        assert ingress[0].nakshatra == NakshatraId.ASHWINI

        natal_activation = [
            a for a in report.activations
            if a.relationship_type == NakshatraRelationshipType.NATAL_NAKSHATRA_ACTIVATION
        ]
        # Should also produce a natal activation for Moon
        assert len(natal_activation) >= 1

    def test_invalid_request(self) -> None:
        """Test that invalid requests raise errors."""
        service = NakshatraActivationService()

        with pytest.raises(InvalidActivationRequestError):
            service.compute_activations(())  # type: ignore[arg-type]

        with pytest.raises(InvalidActivationRequestError):
            service.compute_activations("not a tuple")  # type: ignore[arg-type]

    def test_deterministic_output(self, simple_planet_states: tuple[PlanetState, ...]) -> None:
        """Test that output is deterministic."""
        service = NakshatraActivationService()
        r1 = service.compute_activations(simple_planet_states)
        r2 = service.compute_activations(simple_planet_states)

        d1 = json.dumps(r1.to_dict(), sort_keys=True)
        d2 = json.dumps(r2.to_dict(), sort_keys=True)
        assert d1 == d2

    def test_all_activations_have_deterministic_id(
        self, simple_planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Test that all activations have deterministic IDs."""
        service = NakshatraActivationService()
        report = service.compute_activations(simple_planet_states)

        for activation in report.activations:
            assert activation.deterministic_id != ""
            assert len(activation.deterministic_id) == 64

    def test_all_activations_have_provenance(
        self, simple_planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Test that all activations have provenance."""
        service = NakshatraActivationService()
        report = service.compute_activations(simple_planet_states)

        for activation in report.activations:
            assert activation.provenance != ""

    def test_only_fact_output(
        self, simple_planet_states: tuple[PlanetState, ...]
    ) -> None:
        """CRITICAL: Verify that output contains only facts, no interpretations."""
        service = NakshatraActivationService()
        report = service.compute_activations(simple_planet_states)

        # All relationship types must be from the enum (facts only)
        for activation in report.activations:
            assert isinstance(activation.relationship_type, NakshatraRelationshipType)
