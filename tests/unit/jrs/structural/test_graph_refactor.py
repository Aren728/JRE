"""Tests for Phase 1 graph refactoring (RI-010G).

Tests:
- Exchange (Parivartana) detection
- Directed aspect flags (is_directed=True for aspects)
- Node involvement detection
- New PlanetRelationship fields
"""

from __future__ import annotations

import pytest

from jrs.structural.models import PlanetRelationship, RelationshipType
from jrs.structural.service import RelationshipGraphService


class TestExchangeDetection:
    """Test Parivartana (sign exchange) detection."""

    def test_exchange_detected(self) -> None:
        """Mars in Taurus (Venus's sign), Venus in Aries (Mars's sign) → EXCHANGE."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "MARS": {"rashi": "VRISHABHA"},    # Taurus (lord = Venus)
                "VENUS": {"rashi": "MESHA"},        # Aries (lord = Mars)
            }
        }
        rels = service.extract_relationships(facts)
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        assert len(exchanges) == 1
        ex = exchanges[0]
        assert {ex.planet_a, ex.planet_b} == {"MARS", "VENUS"}
        assert ex.is_directed is False

    def test_no_exchange_when_not_reciprocal(self) -> None:
        """Mars in Taurus, Venus in Gemini → no exchange (Venus not in Mars's sign)."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "MARS": {"rashi": "VRISHABHA"},    # Taurus (lord = Venus)
                "VENUS": {"rashi": "MITHUNA"},     # Gemini (lord = Mercury, not Mars)
            }
        }
        rels = service.extract_relationships(facts)
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        assert len(exchanges) == 0

    def test_exchange_takes_priority_over_separate_edges(self) -> None:
        """Exchange creates its own edge; conjunction takes priority if same sign."""
        service = RelationshipGraphService()
        # Jupiter in Sagittarius (own sign), Saturn in Pisces (Jupiter's sign)
        # Jupiter in Pisces would be conjunction + exchange, but they're in different signs
        facts = {
            "planets": {
                "JUPITER": {"rashi": "DHANUSHA"},   # Sagittarius (lord = Jupiter)
                "SATURN": {"rashi": "MEENA"},        # Pisces (lord = Jupiter)
            }
        }
        rels = service.extract_relationships(facts)
        # No exchange: Saturn in Jupiter's sign, but Jupiter NOT in Saturn's sign
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        assert len(exchanges) == 0

    def test_exchange_not_duplicate(self) -> None:
        """Same exchange pair not reported twice."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "MARS": {"rashi": "VRISHABHA"},
                "VENUS": {"rashi": "MESHA"},
            }
        }
        rels = service.extract_relationships(facts)
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        assert len(exchanges) == 1


class TestDirectedAspectFlags:
    """Test that aspects are marked is_directed=True."""

    def test_aspect_is_directed(self) -> None:
        """Mars in Aries aspects Sun in Libra → is_directed=True."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "MARS": {"rashi": "MESHA"},       # Aries
                "SUN": {"rashi": "TULA"},          # Libra (7th from Aries)
            }
        }
        rels = service.extract_relationships(facts)
        aspects = [r for r in rels if r.relationship_type == RelationshipType.ASPECT]
        assert len(aspects) >= 1
        mars_aspect = next(r for r in aspects if r.planet_a == "MARS")
        assert mars_aspect.is_directed is True
        assert mars_aspect.planet_b == "SUN"

    def test_conjunction_is_not_directed(self) -> None:
        """Sun and Mercury conjunct → is_directed=False."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA"},
                "MERCURY": {"rashi": "MESHA"},
            }
        }
        rels = service.extract_relationships(facts)
        conjunctions = [r for r in rels if r.relationship_type == RelationshipType.CONJUNCTION]
        assert len(conjunctions) == 1
        assert conjunctions[0].is_directed is False

    def test_dispositor_is_directed(self) -> None:
        """Sun in Aries (Mars's sign) → DISPOSITOR is_directed=True."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA"},      # Aries (lord = Mars)
                "MARS": {"rashi": "VRISHABHA"},  # Taurus
            }
        }
        rels = service.extract_relationships(facts)
        dispos = [r for r in rels if r.relationship_type == RelationshipType.DISPOSITOR]
        assert len(dispos) == 1
        assert dispos[0].is_directed is True
        assert dispos[0].planet_a == "SUN"
        assert dispos[0].planet_b == "MARS"

    def test_exchange_is_not_directed(self) -> None:
        """Exchange is undirected: is_directed=False."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "MARS": {"rashi": "VRISHABHA"},
                "VENUS": {"rashi": "MESHA"},
            }
        }
        rels = service.extract_relationships(facts)
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        assert len(exchanges) == 1
        assert exchanges[0].is_directed is False


class TestNodeInvolvement:
    """Test node_involvement flag on relationships."""

    def test_rahu_conjunct_marks_node_involvement(self) -> None:
        """Rahu conjunct Sun → node_involvement=True."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA"},
                "RAHU": {"rashi": "MESHA"},
            }
        }
        rels = service.extract_relationships(facts)
        conjunctions = [r for r in rels if r.relationship_type == RelationshipType.CONJUNCTION]
        assert len(conjunctions) == 1
        assert conjunctions[0].node_involvement is True

    def test_no_node_marks_node_involvement_false(self) -> None:
        """Sun conjunct Mercury → node_involvement=False."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA"},
                "MERCURY": {"rashi": "MESHA"},
            }
        }
        rels = service.extract_relationships(facts)
        conjunctions = [r for r in rels if r.relationship_type == RelationshipType.CONJUNCTION]
        assert len(conjunctions) == 1
        assert conjunctions[0].node_involvement is False

    def test_node_aspect_marks_involvement(self) -> None:
        """Saturn aspects Ketu → node_involvement=True."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SATURN": {"rashi": "MESHA"},    # Aries
                "KETU": {"rashi": "TULA"},        # Libra (7th from Aries)
            }
        }
        rels = service.extract_relationships(facts)
        aspects = [r for r in rels if r.relationship_type == RelationshipType.ASPECT]
        assert len(aspects) >= 1
        saturn_aspect = next(r for r in aspects if r.planet_a == "SATURN")
        assert saturn_aspect.node_involvement is True


class TestNewModelFields:
    """Test new PlanetRelationship fields serialize correctly."""

    def test_to_dict_includes_new_fields(self) -> None:
        """to_dict() includes is_directed, is_war, war_victor, node_involvement."""
        rel = PlanetRelationship(
            planet_a="MARS",
            planet_b="VENUS",
            relationship_type=RelationshipType.EXCHANGE,
            is_directed=False,
            is_war=True,
            war_victor="MARS",
            node_involvement=False,
        )
        d = rel.to_dict()
        assert d["is_directed"] is False
        assert d["is_war"] is True
        assert d["war_victor"] == "MARS"
        assert "node_involvement" not in d  # False = omitted

    def test_to_dict_omits_none_war_victor(self) -> None:
        """to_dict() omits war_victor when None."""
        rel = PlanetRelationship(
            planet_a="SUN",
            planet_b="MERCURY",
            relationship_type=RelationshipType.CONJUNCTION,
        )
        d = rel.to_dict()
        assert "war_victor" not in d

    def test_to_dict_includes_node_when_true(self) -> None:
        """to_dict() includes node_involvement when True."""
        rel = PlanetRelationship(
            planet_a="SUN",
            planet_b="RAHU",
            relationship_type=RelationshipType.CONJUNCTION,
            node_involvement=True,
        )
        d = rel.to_dict()
        assert d["node_involvement"] is True

    def test_defaults_preserve_backward_compatibility(self) -> None:
        """New fields have defaults that preserve existing behavior."""
        rel = PlanetRelationship(
            planet_a="SUN",
            planet_b="MERCURY",
            relationship_type=RelationshipType.CONJUNCTION,
        )
        assert rel.is_directed is False
        assert rel.is_war is False
        assert rel.war_victor is None
        assert rel.node_involvement is False
