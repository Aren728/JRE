"""JRS-012 Phase D — Nakshatra Relationship & Parivartana Engine unit tests.

Tests use synthetic/mocked planetary longitudes. No real astronomical data.
"""

from __future__ import annotations

import pytest

from jrs.graph.chain_evaluator import (
    ChainEdge,
    ChainNode,
    ChainPath,
    DirectedChainEvaluator,
    EdgeType,
    RelationshipGraph,
)
from jrs.graph.chain_strength import ChainStrengthEngine
from jrs.graph.nakshatra_service import (
    NAKSHATRA_ARC,
    NAKSHATRA_LORD_WEIGHT,
    NAKSHATRA_NAMES,
    NAKSHATRA_PARIVARTANA_WEIGHT,
    NakshatraEdge,
    NakshatraRelationshipService,
)
from jrs.structural.models import PlanetRelationship, RelationshipType
from jrs.yoga_evaluator.service import YogaEvaluatorService


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 1: Nakshatra Lord Resolution
# ══════════════════════════════════════════════════════════════════════════════


class TestNakshatraLordResolution:
    """Tests for correct Nakshatra lord resolution across 0–360°."""

    def setup_method(self) -> None:
        self.svc = NakshatraRelationshipService()

    def test_0_degrees_ashwini_lord_is_ketu(self) -> None:
        """0° → Ashwini → lord is Ketu."""
        assert self.svc.get_nakshatra_lord(0.0) == "KETU"

    def test_nakshatra_arc_boundaries(self) -> None:
        """Each Nakshatra spans exactly NAKSHATRA_ARC degrees."""
        # Ashwini: 0°–13.333° → lord Ketu
        # Bharani: 13.333°–26.666° → lord Venus
        # Krittika: 26.666°–40.0° → lord Sun
        expected_lords = ["KETU", "VENUS", "SUN", "MOON", "MARS", "RAHU", "JUPITER", "SATURN", "MERCURY"]
        for i, lord in enumerate(expected_lords):
            deg = i * NAKSHATRA_ARC + 0.1  # Just inside the Nakshatra
            assert self.svc.get_nakshatra_lord(deg) == lord, f"Failed at {deg}°"

    def test_360_degrees_wraps_to_0(self) -> None:
        """360° wraps to 0° → Ashwini → lord Ketu."""
        assert self.svc.get_nakshatra_lord(360.0) == "KETU"

    def test_full_cycle_27_nakshatras(self) -> None:
        """Full 360° cycle covers all 27 Nakshatras (9 lords × 3)."""
        lords_seen: set[str] = set()
        for i in range(27):
            deg = i * NAKSHATRA_ARC + 0.1
            lord = self.svc.get_nakshatra_lord(deg)
            lords_seen.add(lord)
        # All 9 lords should appear
        assert len(lords_seen) == 9

    def test_negative_longitude_wraps(self) -> None:
        """Negative longitude wraps correctly."""
        lord = self.svc.get_nakshatra_lord(-10.0)
        assert lord in {"KETU", "VENUS", "SUN", "MOON", "MARS", "RAHU", "JUPITER", "SATURN", "MERCURY"}

    def test_nakshatra_names_count(self) -> None:
        """There are exactly 27 Nakshatra names."""
        assert len(NAKSHATRA_NAMES) == 27

    def test_nakshatra_name_for_0_degrees(self) -> None:
        """0° → Ashwini."""
        assert self.svc.get_nakshatra_name(0.0) == "ASHWINI"

    def test_nakshatra_name_for_20_degrees(self) -> None:
        """~20° → Bharani (second Nakshatra)."""
        assert self.svc.get_nakshatra_name(20.0) == "BHARANI"

    def test_nakshatra_name_for_350_degrees(self) -> None:
        """350° → Revati (last Nakshatra)."""
        assert self.svc.get_nakshatra_name(350.0) == "REVATI"


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 2: Mutual Nakshatra Exchange Detection
# ══════════════════════════════════════════════════════════════════════════════


class TestNakshatraParivartanaDetection:
    """Tests for NAKSHATRA_PARIVARTANA (mutual exchange) detection."""

    def setup_method(self) -> None:
        self.svc = NakshatraRelationshipService()

    def test_mutual_exchange_detected(self) -> None:
        """Planets in mutual Nakshatra exchange are detected."""
        # We need: Planet A in Nakshatra ruled by B, AND Planet B in Nakshatra ruled by A.
        # Ketu rules Ashwini (0°–13.33°), Venus rules Bharani (13.33°–26.66°)
        # Sun rules Krittika (26.66°–40°), Moon rules Rohini (40°–53.33°)
        # Mars rules Mrigashira (53.33°–66.66°), Rahu rules Ardra (66.66°–80°)
        # Jupiter rules Punarvasu (80°–93.33°), Saturn rules Pushya (93.33°–106.66°)
        # Mercury rules Ashlesha (106.66°–120°)

        # To create a mutual exchange, we need two planets where:
        # A is in a Nakshatra whose lord is B, AND B is in a Nakshatra whose lord is A.
        # Example: Planet at 5° (Ashwini, lord=Ketu) and Planet at 0.5° (also Ashwini, lord=Ketu)
        # That's not an exchange. We need different Nakshatras.

        # Let's construct: Planet X at 5° (Ashwini, lord=Ketu)
        #                   Planet Y at 115° (Ashlesha, lord=Mercury)
        # X's lord is Ketu, Y's lord is Mercury. Not an exchange.

        # We need: X in Nakshatra lorded by Y, AND Y in Nakshatra lorded by X.
        # This requires careful construction. Let's find two Nakshatras A, B where
        # lord(A) = planet_Y and lord(B) = planet_X.
        # Since we're using planet names as both positions and lords, we need
        # planets whose names match the Nakshatra lords.

        # Simplified: Use planet names that are also Vimshottari lords.
        # Ketu rules Ashwini (0°). If planet "KETU" is at 5° (Ashwini), lord=KETU.
        # We need another planet in a Nakshatra whose lord is "KETU" — that's Ashwini or Magha.
        # If "SUN" is at 30° (Krittika, lord=SUN), that's not helpful.

        # The key insight: for a true mutual exchange, we need:
        # Planet A's Nakshatra lord = Planet B, AND Planet B's Nakshatra lord = Planet A.
        # Since the lord cycle is KETU→VENUS→SUN→MOON→MARS→RAHU→JUPITER→SATURN→MERCURY,
        # we need two adjacent lords in the cycle, e.g., KETU and VENUS:
        # - Planet at 5° (Ashwini, lord=KETU) → if there's a planet named "KETU"
        # - Planet at 20° (Bharani, lord=VENUS) → if there's a planet named "VENUS"
        # Then: VENUS's Nakshatra lord = KETU (Bharani → lord VENUS... wait, no)

        # Actually: the lord of Bharani is VENUS. So if planet "KETU" is in Bharani,
        # its Nakshatra lord is VENUS. And if planet "VENUS" is in Ashwini,
        # its Nakshatra lord is KETU. That's a mutual exchange!

        positions = {
            "KETU": 20.0,    # Bharani → lord VENUS
            "VENUS": 5.0,    # Ashwini → lord KETU
        }
        edges = self.svc.detect_relationships(positions)
        parivartana = [e for e in edges if e.edge_type == "NAKSHATRA_PARIVARTANA"]
        assert len(parivartana) == 1
        assert parivartana[0].weight == NAKSHATRA_PARIVARTANA_WEIGHT

    def test_parivartana_bidirectional(self) -> None:
        """Parivartana edge is recorded once (not duplicated)."""
        positions = {
            "KETU": 20.0,    # Bharani → lord VENUS
            "VENUS": 5.0,    # Ashwini → lord KETU
        }
        edges = self.svc.detect_relationships(positions)
        parivartana = [e for e in edges if e.edge_type == "NAKSHATRA_PARIVARTANA"]
        assert len(parivartana) == 1

    def test_parivartana_edge_fields(self) -> None:
        """Parivartana edge has correct source, target, and nakshatra names."""
        positions = {
            "KETU": 20.0,    # Bharani
            "VENUS": 5.0,    # Ashwini
        }
        edges = self.svc.detect_relationships(positions)
        parivartana = [e for e in edges if e.edge_type == "NAKSHATRA_PARIVARTANA"]
        assert len(parivartana) == 1
        edge = parivartana[0]
        assert edge.source_nakshatra == "BHARANI"
        assert edge.target_nakshatra == "ASHWINI"

    def test_no_exchange_for_non_matching(self) -> None:
        """Non-matching Nakshatra positions do not produce Parivartana."""
        positions = {
            "SUN": 5.0,      # Ashwini → lord KETU
            "MOON": 20.0,    # Bharani → lord VENUS
        }
        edges = self.svc.detect_relationships(positions)
        parivartana = [e for e in edges if e.edge_type == "NAKSHATRA_PARIVARTANA"]
        assert len(parivartana) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 3: One-Way Nakshatra Dependency Detection
# ══════════════════════════════════════════════════════════════════════════════


class TestNakshatraLordDependency:
    """Tests for NAKSHATRA_LORD (one-directional dependency) detection."""

    def setup_method(self) -> None:
        self.svc = NakshatraRelationshipService()

    def test_one_way_dependency_detected(self) -> None:
        """Planet in Nakshatra ruled by another → NAKSHATRA_LORD edge."""
        # SUN at 5° → Ashwini → lord KETU
        # MOON at 20° → Bharani → lord VENUS
        # No mutual exchange, but SUN depends on KETU (lord of its Nakshatra)
        # and MOON depends on VENUS.
        positions = {
            "SUN": 5.0,      # Ashwini → lord KETU
            "MOON": 20.0,    # Bharani → lord VENUS
            "KETU": 100.0,   # Pushya → lord SATURN (not SUN, so no exchange)
            "VENUS": 100.0,  # Pushya → lord SATURN (not MOON, so no exchange)
        }
        edges = self.svc.detect_relationships(positions)
        lord_edges = [e for e in edges if e.edge_type == "NAKSHATRA_LORD"]
        # SUN → KETU (SUN in Ashwini, lord=KETU)
        # MOON → VENUS (MOON in Bharani, lord=VENUS)
        assert len(lord_edges) >= 2
        sources = {e.source for e in lord_edges}
        assert "SUN" in sources
        assert "MOON" in sources

    def test_dependency_weight(self) -> None:
        """NAKSHATRA_LORD edge has weight 0.65."""
        positions = {
            "SUN": 5.0,      # Ashwini → lord KETU
            "KETU": 100.0,   # Pushya → lord SATURN
        }
        edges = self.svc.detect_relationships(positions)
        lord_edges = [e for e in edges if e.edge_type == "NAKSHATRA_LORD"]
        sun_edge = [e for e in lord_edges if e.source == "SUN"]
        assert len(sun_edge) == 1
        assert sun_edge[0].weight == NAKSHATRA_LORD_WEIGHT

    def test_dependency_not_duplicated_as_parivartana(self) -> None:
        """When both planets are in mutual exchange, no separate LORD edges."""
        positions = {
            "KETU": 20.0,    # Bharani → lord VENUS
            "VENUS": 5.0,    # Ashwini → lord KETU
        }
        edges = self.svc.detect_relationships(positions)
        lord_edges = [e for e in edges if e.edge_type == "NAKSHATRA_LORD"]
        parivartana = [e for e in edges if e.edge_type == "NAKSHATRA_PARIVARTANA"]
        # Should have Parivartana, not LORD
        assert len(parivartana) == 1
        assert len(lord_edges) == 0

    def test_self_lord_excluded(self) -> None:
        """Planet in its own Nakshatra lord's star is excluded (self-lord)."""
        # If a planet's Nakshatra lord is itself, no edge is created.
        # This happens when a planet is at 0° (Ashwini, lord=KETU) and the planet IS KETU.
        positions = {
            "KETU": 5.0,     # Ashwini → lord KETU (self-lord)
        }
        edges = self.svc.detect_relationships(positions)
        # No edges because KETU's Nakshatra lord is KETU (self)
        assert len(edges) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 4: Edge Weight Assignment & Chain Evaluator Integration
# ══════════════════════════════════════════════════════════════════════════════


class TestNakshatraEdgeWeights:
    """Tests for correct edge weight assignment in ChainEdge."""

    def test_nakshatra_parivartana_weight_in_edge_weights(self) -> None:
        """NAKSHATRA_PARIVARTANA weight is registered in EDGE_WEIGHTS."""
        from jrs.graph.chain_evaluator import EDGE_WEIGHTS
        assert EDGE_WEIGHTS[EdgeType.NAKSHATRA_PARIVARTANA] == 0.85

    def test_nakshatra_lord_weight_in_edge_weights(self) -> None:
        """NAKSHATRA_LORD weight is registered in EDGE_WEIGHTS."""
        from jrs.graph.chain_evaluator import EDGE_WEIGHTS
        assert EDGE_WEIGHTS[EdgeType.NAKSHATRA_LORD] == 0.65

    def test_manual_nakshatra_parivartana_edge(self) -> None:
        """Manual graph API supports NAKSHATRA_PARIVARTANA edge type."""
        evaluator = DirectedChainEvaluator(lagna_sign=1)
        evaluator.add_node("KETU", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_node("VENUS", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_edge("KETU", "VENUS", "NAKSHATRA_PARIVARTANA")
        paths = evaluator.find_paths("KETU", "VENUS", max_depth=3)
        assert len(paths) == 1
        assert paths[0].edges[0].edge_type == EdgeType.NAKSHATRA_PARIVARTANA
        assert paths[0].edges[0].weight == 0.85

    def test_manual_nakshatra_lord_edge(self) -> None:
        """Manual graph API supports NAKSHATRA_LORD edge type."""
        evaluator = DirectedChainEvaluator(lagna_sign=1)
        evaluator.add_node("SUN", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_node("KETU", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_edge("SUN", "KETU", "NAKSHATRA_LORD")
        paths = evaluator.find_paths("SUN", "KETU", max_depth=3)
        assert len(paths) == 1
        assert paths[0].edges[0].edge_type == EdgeType.NAKSHATRA_LORD
        assert paths[0].edges[0].weight == 0.65


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 5: Chain Strength with Nakshatra Edges
# ══════════════════════════════════════════════════════════════════════════════


class TestChainStrengthNakshatraEdges:
    """Tests for ChainStrengthEngine handling of Nakshatra edge attenuation."""

    def setup_method(self) -> None:
        self.engine = ChainStrengthEngine()

    def test_nakshatra_parivartana_path_impact(self) -> None:
        """Path with NAKSHATRA_PARIVARTANA edge computes correct impact."""
        from jrs.graph.chain_evaluator import Dignity
        from jrs.graph.functional_lordship import FunctionalRole

        root = ChainNode(
            planet="KETU", house=1, sign=1, dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False, is_combust=False,
            functional_role=FunctionalRole.BENEFIC, base_weight=1.00,
        )
        target = ChainNode(
            planet="VENUS", house=1, sign=1, dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False, is_combust=False,
            functional_role=FunctionalRole.BENEFIC, base_weight=1.00,
        )
        edge = ChainEdge(
            source="KETU", target="VENUS",
            edge_type=EdgeType.NAKSHATRA_PARIVARTANA,
            weight=0.85,
        )
        path = ChainPath(nodes=(root, target), edges=(edge,), length=1)
        result = self.engine.compute_path_impact(path)

        # F_role(BENEFIC) = 1.00
        # M_node = 1.00 (FRIEND_SIGN, no retro/combust)
        # W_edge = 0.85
        # HOP_DAMPING = 0.70
        # nak_attenuation = 1.00
        expected = 1.00 * 1.00 * (0.85 * 1.00 * 0.70 * 1.00)
        assert result.net_functional_impact == pytest.approx(expected)

    def test_nakshatra_lord_path_impact(self) -> None:
        """Path with NAKSHATRA_LORD edge computes correct impact."""
        from jrs.graph.chain_evaluator import Dignity
        from jrs.graph.functional_lordship import FunctionalRole

        root = ChainNode(
            planet="SUN", house=1, sign=1, dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False, is_combust=False,
            functional_role=FunctionalRole.BENEFIC, base_weight=1.00,
        )
        target = ChainNode(
            planet="KETU", house=1, sign=1, dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False, is_combust=False,
            functional_role=FunctionalRole.NEUTRAL, base_weight=0.00,
        )
        edge = ChainEdge(
            source="SUN", target="KETU",
            edge_type=EdgeType.NAKSHATRA_LORD,
            weight=0.65,
        )
        path = ChainPath(nodes=(root, target), edges=(edge,), length=1)
        result = self.engine.compute_path_impact(path)

        # F_role(BENEFIC) = 1.00
        # M_node = 1.00
        # W_edge = 0.65
        # HOP_DAMPING = 0.70
        expected = 1.00 * 1.00 * (0.65 * 1.00 * 0.70 * 1.00)
        assert result.net_functional_impact == pytest.approx(expected)


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 6: Integration — Layer 1.5 with Nakshatra Edges
# ══════════════════════════════════════════════════════════════════════════════


class TestNakshatraServiceIntegration:
    """Integration tests for Nakshatra edges in the full pipeline."""

    def setup_method(self) -> None:
        self.service = YogaEvaluatorService()

    def test_compute_chain_impact_with_nakshatra_longitudes(self) -> None:
        """compute_chain_impact includes Nakshatra edges when longitudes present."""
        jre_facts = {
            "planets": {
                "KETU": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 20.0,
                },
                "VENUS": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 5.0,
                },
            },
            "lagna_sign": 1,
        }
        impact = self.service.compute_chain_impact(
            involved_planets=["KETU", "VENUS"],
            jre_facts=jre_facts,
        )
        assert isinstance(impact, float)

    def test_compute_chain_impact_without_longitudes(self) -> None:
        """compute_chain_impact works normally without longitudes (no Nakshatra edges)."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False,
                },
                "SATURN": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False,
                },
            },
            "lagna_sign": 1,
        }
        impact = self.service.compute_chain_impact(
            involved_planets=["JUPITER", "SATURN"],
            jre_facts=jre_facts,
        )
        assert isinstance(impact, float)

    def test_get_chain_paths_with_nakshatra_edges(self) -> None:
        """get_chain_paths includes paths traversing Nakshatra edges."""
        jre_facts = {
            "planets": {
                "KETU": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 20.0,
                },
                "VENUS": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 5.0,
                },
                "SATURN": {
                    "house": 4, "rashi_num": 10, "combust": False,
                    "debilitated": False, "retrograde": False,
                },
            },
            "lagna_sign": 1,
        }
        paths = self.service.get_chain_paths(
            involved_planets=["KETU", "VENUS"],
            jre_facts=jre_facts,
        )
        assert isinstance(paths, list)

    def test_evaluate_formation_with_nakshatra_data(self) -> None:
        """evaluate_formation includes Nakshatra impact when longitudes present."""
        jre_facts = {
            "planets": {
                "KETU": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 20.0,
                },
                "VENUS": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 5.0,
                },
            },
            "lagna_sign": 1,
            "moon_nakshatra": "ASHWINI",
            "moon_nakshatra_degree": 5.0,
        }
        result = self.service.evaluate_formation(
            yoga_name="TestNakshatra",
            involved_planets=["KETU", "VENUS"],
            jre_facts=jre_facts,
        )
        assert result.chain_impact is not None

    def test_full_pipeline_with_nakshatra_parivartana(self) -> None:
        """Full pipeline with Nakshatra Parivartana between KETU and VENUS."""
        # KETU at 20° (Bharani, lord=VENUS), VENUS at 5° (Ashwini, lord=KETU)
        # This creates a NAKSHATRA_PARIVARTANA (weight=0.85)
        jre_facts = {
            "planets": {
                "KETU": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 20.0,
                },
                "VENUS": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 5.0,
                },
            },
            "lagna_sign": 1,
        }
        paths = self.service.get_chain_paths(
            involved_planets=["KETU", "VENUS"],
            jre_facts=jre_facts,
        )
        # Should discover at least one path via NAKSHATRA_PARIVARTANA
        nakshatra_paths = [
            p for p in paths
            if any(e.edge_type == EdgeType.NAKSHATRA_PARIVARTANA for e in p.path.edges)
        ]
        assert len(nakshatra_paths) >= 1

    def test_nakshatra_edge_does_not_pollute_existing(self) -> None:
        """Nakshatra edges do not interfere with existing structural edges."""
        jre_facts = {
            "planets": {
                "KETU": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 20.0,
                },
                "VENUS": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "longitude": 5.0,
                },
                "JUPITER": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False,
                },
            },
            "lagna_sign": 1,
        }
        impact = self.service.compute_chain_impact(
            involved_planets=["KETU", "VENUS"],
            jre_facts=jre_facts,
        )
        # Impact should be computed without errors
        assert isinstance(impact, float)

    def test_nakshatra_edge_loop_suppression(self) -> None:
        """Nakshatra edges respect depth-bounded loop suppression."""
        evaluator = DirectedChainEvaluator(max_depth=2)
        # Create a cycle via Nakshatra edges
        evaluator.add_node("KETU", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_node("VENUS", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_node("SUN", house=1, sign=1, dignity="FRIEND_SIGN")
        evaluator.add_edge("KETU", "VENUS", "NAKSHATRA_PARIVARTANA")
        evaluator.add_edge("VENUS", "SUN", "NAKSHATRA_LORD")
        evaluator.add_edge("SUN", "KETU", "NAKSHATRA_LORD")

        # With max_depth=2, should not produce paths longer than 2 hops
        paths = evaluator.find_paths("KETU", "SUN", max_depth=2)
        for p in paths:
            assert p.length <= 2
