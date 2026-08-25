"""JRS-073 Relationship Graph unit tests."""

from __future__ import annotations

import pytest
from jrs.structural.models import PlanetRelationship, RelationshipType
from jrs.structural.service import RelationshipGraphService


class TestRelationshipGraphService:
    def test_conjunction_detection(self) -> None:
        """Test A: Mock facts with Sun and Moon in Aries -> returns CONJUNCTION."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "longitude": 15.5},
                "MOON": {"rashi": "MESHA", "longitude": 20.1},
            }
        }
        rels = service.extract_relationships(facts)
        
        conjunctions = [r for r in rels if r.relationship_type == RelationshipType.CONJUNCTION]
        assert len(conjunctions) == 1
        
        conj = conjunctions[0]
        assert {conj.planet_a, conj.planet_b} == {"SUN", "MOON"}
        assert conj.relationship_type == RelationshipType.CONJUNCTION

    def test_dispositor_detection(self) -> None:
        """Test B: Mock facts with Sun in Aries (owned by Mars) -> returns DISPOSITOR (Sun, Mars)."""
        service = RelationshipGraphService()
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "longitude": 15.5},
                "MARS": {"rashi": "SIMHA", "longitude": 120.0},  # Mars is in Leo (owned by Sun)
            }
        }
        rels = service.extract_relationships(facts)
        
        # Should find SUN->MARS (Sun in Aries owned by Mars) and MARS->SUN (Mars in Leo owned by Sun)
        dispositor_rels = [r for r in rels if r.relationship_type == RelationshipType.DISPOSITOR]
        assert len(dispositor_rels) == 2
        
        # Check that SUN->MARS is present
        sun_mars = [r for r in dispositor_rels if r.planet_a == "SUN" and r.planet_b == "MARS"]
        assert len(sun_mars) == 1
        assert sun_mars[0].relationship_type == RelationshipType.DISPOSITOR

    def test_transit_activation(self) -> None:
        """Test A: Mock natal facts (Sun in Aries) + Mock transit facts (Saturn in Libra) -> TRANSIT_ASPECT."""
        service = RelationshipGraphService()
        natal_facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "longitude": 15.5},
                "MOON": {"rashi": "MESHA", "longitude": 20.1},  # Natal conjunction with Sun
            }
        }
        transit_facts = {
            "planets": {
                "SATURN": {"rashi": "TULA", "longitude": 195.0},  # Libra aspects Aries (7th)
            }
        }
        
        rels = service.extract_relationships(natal_facts, transit_facts)
        
        # Should have natal conjunction, two transit aspects, and active natal conjunction
        transit_aspects = [r for r in rels if r.relationship_type == RelationshipType.TRANSIT_ASPECT]
        assert len(transit_aspects) == 2  # Saturn aspects both Sun and Moon
        
        # Check that the natal conjunction is marked as active
        natal_conjs = [r for r in rels if r.relationship_type == RelationshipType.CONJUNCTION]
        assert len(natal_conjs) == 1
        assert natal_conjs[0].is_active is True
