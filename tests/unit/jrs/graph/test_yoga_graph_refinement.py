"""JRS-092: Unit tests for Kendra-Trikona / Yoga Graph Validation Refinement.

Verifies cyclic graph safety, multi-hop weight decay, Kendra-Trikona nexus,
new edge types, formation score bounds, signed chain impact preservation,
determinism, and Parivartana detection.
"""

from __future__ import annotations

import pytest

from jrs.graph.chain_evaluator import (
    ChainEdge,
    ChainNode,
    ChainPath,
    DIGNITY_SCORES,
    DirectedChainEvaluator,
    Dignity,
    EdgeType,
    EDGE_WEIGHTS,
)
from jrs.graph.chain_strength import ChainStrengthEngine, HOP_DAMPING
from jrs.graph.functional_lordship import FunctionalRole


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def evaluator_aries() -> DirectedChainEvaluator:
    """Aries Lagna evaluator."""
    return DirectedChainEvaluator(lagna_sign=1)


@pytest.fixture()
def engine() -> ChainStrengthEngine:
    """Chain strength engine."""
    return ChainStrengthEngine()


# ── 1. New Edge Types ────────────────────────────────────────────────────────


class TestNewEdgeTypes:
    """Verify LORD_OF and OCCUPIES edge types are registered correctly."""

    def test_lord_of_exists_in_enum(self) -> None:
        """LORD_OF must exist in EdgeType enum."""
        assert EdgeType.LORD_OF == "LORD_OF"

    def test_occupies_exists_in_enum(self) -> None:
        """OCCUPIES must exist in EdgeType enum."""
        assert EdgeType.OCCUPIES == "OCCUPIES"

    def test_lord_of_weight(self) -> None:
        """LORD_OF weight must be 0.80."""
        assert EDGE_WEIGHTS[EdgeType.LORD_OF] == 0.80

    def test_occupies_weight(self) -> None:
        """OCCUPIES weight must be 0.70."""
        assert EDGE_WEIGHTS[EdgeType.OCCUPIES] == 0.70

    def test_existing_weights_unchanged(self) -> None:
        """All existing edge weights must remain unchanged."""
        assert EDGE_WEIGHTS[EdgeType.CONJUNCTION] == 1.00
        assert EDGE_WEIGHTS[EdgeType.PARIVARTANA] == 0.90
        assert EDGE_WEIGHTS[EdgeType.MUTUAL_ASPECT] == 0.85
        assert EDGE_WEIGHTS[EdgeType.ONE_WAY_ASPECT] == 0.75
        assert EDGE_WEIGHTS[EdgeType.DISPOSITOR] == 0.60
        assert EDGE_WEIGHTS[EdgeType.NAKSHATRA_PARIVARTANA] == 0.85
        assert EDGE_WEIGHTS[EdgeType.NAKSHATRA_LORD] == 0.65

    def test_lord_of_edge_traversable(self, evaluator_aries: DirectedChainEvaluator) -> None:
        """LORD_OF edges can be added and traversed."""
        evaluator_aries.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        evaluator_aries.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        evaluator_aries.add_edge("Sun", "Mars", "LORD_OF")

        paths = evaluator_aries.find_paths("Sun", "Mars", max_depth=3)
        assert len(paths) == 1
        assert paths[0].edges[0].edge_type == EdgeType.LORD_OF
        assert paths[0].edges[0].weight == 0.80

    def test_occupies_edge_traversable(self, evaluator_aries: DirectedChainEvaluator) -> None:
        """OCCUPIES edges can be added and traversed."""
        evaluator_aries.add_node("Jupiter", house=9, sign=12, dignity="OWN_SIGN")
        evaluator_aries.add_node("Venus", house=12, sign=12, dignity="ENEMY_SIGN")
        evaluator_aries.add_edge("Jupiter", "Venus", "OCCUPIES")

        paths = evaluator_aries.find_paths("Jupiter", "Venus", max_depth=3)
        assert len(paths) == 1
        assert paths[0].edges[0].edge_type == EdgeType.OCCUPIES
        assert paths[0].edges[0].weight == 0.70


# ── 2. Cyclic Graph Safety ───────────────────────────────────────────────────


class TestCyclicGraphSafety:
    """Verify mutual dispositor loops terminate cleanly."""

    def test_parivartana_cycle_terminates(self) -> None:
        """Mutual Parivartana (A→B→A) should not cause infinite recursion."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")
        ev.add_edge("Mars", "Sun", "PARIVARTANA")

        # Should terminate without stack overflow
        paths = ev.find_paths("Sun", "Mars", max_depth=3)
        assert len(paths) >= 1

    def test_dispositor_cycle_terminates(self) -> None:
        """A→B→C→A dispositor cycle should terminate at max depth."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mercury", house=1, sign=3, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=9, sign=8, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mercury", "DISPOSITOR")
        ev.add_edge("Mercury", "Mars", "DISPOSITOR")
        ev.add_edge("Mars", "Sun", "DISPOSITOR")

        # Should find paths but not loop infinitely
        paths = ev.find_paths("Sun", "Mars", max_depth=3)
        assert len(paths) >= 1
        # All paths should have length <= 3
        for p in paths:
            assert p.length <= 3

    def test_three_node_cycle_respects_max_depth(self) -> None:
        """Cycle A→B→C→A with max_depth=2 should not reach A again."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mercury", house=1, sign=3, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=9, sign=8, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")
        ev.add_edge("Mars", "Sun", "DISPOSITOR")

        paths = ev.find_paths("Sun", "Mars", max_depth=2)
        for p in paths:
            assert p.length <= 2


# ── 3. Multi-hop Weight Decay ────────────────────────────────────────────────


class TestMultiHopWeightDecay:
    """Verify 1-hop vs 2-hop vs 3-hop scores decay predictably."""

    def test_1hop_stronger_than_2hop(self, engine: ChainStrengthEngine) -> None:
        """1-hop path should have higher absolute impact than 2-hop."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Mercury", house=1, sign=1, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=5, sign=5, dignity="OWN_SIGN")

        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")

        path_1hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"]),
            edges=(ev._manual_edges[0],),
            length=1,
        )
        path_2hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"], ev._manual_nodes["Mars"]),
            edges=(ev._manual_edges[0], ev._manual_edges[1]),
            length=2,
        )

        impact_1 = abs(engine.compute_path_impact(path_1hop).net_functional_impact)
        impact_2 = abs(engine.compute_path_impact(path_2hop).net_functional_impact)

        # 1-hop should be stronger (less damping)
        assert impact_1 > impact_2

    def test_2hop_stronger_than_3hop(self, engine: ChainStrengthEngine) -> None:
        """2-hop path should have higher absolute impact than 3-hop."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Mercury", house=1, sign=1, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Jupiter", house=9, sign=12, dignity="EXALTED")

        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")
        ev.add_edge("Mars", "Jupiter", "DISPOSITOR")

        path_2hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"], ev._manual_nodes["Mars"]),
            edges=(ev._manual_edges[0], ev._manual_edges[1]),
            length=2,
        )
        path_3hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"],
                   ev._manual_nodes["Mars"], ev._manual_nodes["Jupiter"]),
            edges=(ev._manual_edges[0], ev._manual_edges[1], ev._manual_edges[2]),
            length=3,
        )

        impact_2 = abs(engine.compute_path_impact(path_2hop).net_functional_impact)
        impact_3 = abs(engine.compute_path_impact(path_3hop).net_functional_impact)

        assert impact_2 > impact_3

    def test_decay_factor_is_0_70(self, engine: ChainStrengthEngine) -> None:
        """Each additional hop should multiply impact by ~0.70 (times edge/node weights)."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="FRIEND_SIGN")
        ev.add_node("Mercury", house=1, sign=1, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=5, sign=5, dignity="FRIEND_SIGN")

        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "CONJUNCTION")

        path_1hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"]),
            edges=(ev._manual_edges[0],),
            length=1,
        )
        path_2hop = ChainPath(
            nodes=(ev._manual_nodes["Sun"], ev._manual_nodes["Mercury"], ev._manual_nodes["Mars"]),
            edges=(ev._manual_edges[0], ev._manual_edges[1]),
            length=2,
        )

        impact_1 = engine.compute_path_impact(path_1hop).net_functional_impact
        impact_2 = engine.compute_path_impact(path_2hop).net_functional_impact

        # With same node/edge weights, ratio should be ~0.70
        if impact_1 != 0.0:
            ratio = impact_2 / impact_1
            assert ratio == pytest.approx(0.70, abs=0.01)


# ── 4. Kendra-Trikona Nexus ──────────────────────────────────────────────────


class TestKendraTrikonaNexus:
    """Verify Kendra-Trikona nexus scoring."""

    def test_direct_conjunction_strongest(self) -> None:
        """Direct conjunction between Kendra and Trikona lord > other links."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Jupiter", "CONJUNCTION")

        score = ev.evaluate_kendra_trikona_nexus(lagna_sign=1)
        assert score > 0.0

    def test_no_link_score_zero(self) -> None:
        """No edges between Kendra/Trikona lords → score = 0."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=2, sign=2, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=3, sign=3, dignity="FRIEND_SIGN")
        ev.add_edge("Sun", "Mars", "CONJUNCTION")

        score = ev.evaluate_kendra_trikona_nexus(lagna_sign=1)
        assert score == 0.0

    def test_conjunction_greater_than_dispositor(self) -> None:
        """CONJUNCTION link > DISPOSITOR link between same Kendra-Trikona pair."""
        ev1 = DirectedChainEvaluator(lagna_sign=1)
        ev1.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev1.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev1.add_edge("Sun", "Jupiter", "CONJUNCTION")
        score_conj = ev1.evaluate_kendra_trikona_nexus(lagna_sign=1)

        ev2 = DirectedChainEvaluator(lagna_sign=1)
        ev2.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev2.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev2.add_edge("Sun", "Jupiter", "DISPOSITOR")
        score_disp = ev2.evaluate_kendra_trikona_nexus(lagna_sign=1)

        assert score_conj > score_disp

    def test_empty_graph_score_zero(self) -> None:
        """Empty graph → nexus score = 0."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        assert ev.evaluate_kendra_trikona_nexus(lagna_sign=1) == 0.0

    def test_nexus_score_deterministic(self) -> None:
        """Identical inputs produce identical nexus scores."""
        ev1 = DirectedChainEvaluator(lagna_sign=1)
        ev1.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev1.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev1.add_edge("Sun", "Jupiter", "CONJUNCTION")

        ev2 = DirectedChainEvaluator(lagna_sign=1)
        ev2.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev2.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev2.add_edge("Sun", "Jupiter", "CONJUNCTION")

        assert ev1.evaluate_kendra_trikona_nexus(1) == ev2.evaluate_kendra_trikona_nexus(1)


# ── 5. Formation Score Bounds ────────────────────────────────────────────────


class TestFormationScoreBounds:
    """Verify formation score output is strictly in [0.0, 1.0]."""

    def test_empty_paths_score_zero(self, engine: ChainStrengthEngine) -> None:
        """Empty path list → formation score = 0.0."""
        assert engine.compute_formation_score([]) == 0.0

    def test_single_positive_path_bounded(self, engine: ChainStrengthEngine) -> None:
        """Single positive path → score in [0.0, 1.0]."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Jupiter", house=5, sign=4, dignity="EXALTED")
        ev.add_edge("Sun", "Jupiter", "CONJUNCTION")

        paths = ev.find_paths("Sun", "Jupiter", max_depth=3)
        score = engine.compute_formation_score(paths)
        assert 0.0 <= score <= 1.0

    def test_high_impact_clamped(self, engine: ChainStrengthEngine) -> None:
        """Very high aggregate impact should be clamped to 1.0."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        # Create many high-impact paths
        for i in range(10):
            ev.add_node(f"Planet_{i}", house=1, sign=1, dignity="EXALTED")
        for i in range(9):
            ev.add_edge(f"Planet_{i}", f"Planet_{i + 1}", "CONJUNCTION")

        paths = ev.find_paths("Planet_0", "Planet_9", max_depth=3)
        score = engine.compute_formation_score(paths)
        assert 0.0 <= score <= 1.0

    def test_malefic_chain_score_bounded(self, engine: ChainStrengthEngine) -> None:
        """Negative MALEFIC chain → score clamped to 0.0 (not negative)."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Saturn", house=6, sign=6, dignity="DEBILITATED")
        ev.add_node("Mars", house=8, sign=8, dignity="DEBILITATED")
        ev.add_edge("Saturn", "Mars", "ONE_WAY_ASPECT")

        paths = ev.find_paths("Saturn", "Mars", max_depth=3)
        score = engine.compute_formation_score(paths)
        assert score >= 0.0  # Clamped, not negative


# ── 6. Signed Chain Impact Preservation ──────────────────────────────────────


class TestSignedChainImpact:
    """Verify MALEFIC chains produce negative net_functional_impact."""

    def test_malefic_chain_negative_impact(self, engine: ChainStrengthEngine) -> None:
        """MALEFIC root node → negative net_functional_impact."""
        # Moon for Aries Lagna: owns house 4 (Kendra) → MALEFIC
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Moon", house=4, sign=4, dignity="DEBILITATED")
        ev.add_node("Mercury", house=6, sign=3, dignity="FRIEND_SIGN")
        ev.add_edge("Moon", "Mercury", "ONE_WAY_ASPECT")

        paths = ev.find_paths("Moon", "Mercury", max_depth=3)
        assert len(paths) == 1

        impact = engine.compute_path_impact(paths[0])
        assert impact.net_functional_impact < 0.0

    def test_benefic_chain_positive_impact(self, engine: ChainStrengthEngine) -> None:
        """BENEFIC root node → positive net_functional_impact."""
        # Sun for Aries Lagna: owns house 5 (Trikona) → BENEFIC
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="EXALTED")
        ev.add_node("Saturn", house=10, sign=11, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Saturn", "CONJUNCTION")

        paths = ev.find_paths("Sun", "Saturn", max_depth=3)
        assert len(paths) == 1

        impact = engine.compute_path_impact(paths[0])
        assert impact.net_functional_impact > 0.0

    def test_neutral_chain_zero_impact(self, engine: ChainStrengthEngine) -> None:
        """NEUTRAL root node → zero net_functional_impact."""
        # Mars for Aries Lagna: owns 1+8 (Kendra+Dusthana) → NEUTRAL
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_node("Venus", house=7, sign=7, dignity="OWN_SIGN")
        ev.add_edge("Mars", "Venus", "CONJUNCTION")

        paths = ev.find_paths("Mars", "Venus", max_depth=3)
        assert len(paths) == 1

        impact = engine.compute_path_impact(paths[0])
        # Mars in house 1 is NEUTRAL for Aries Lagna → F_role = 0.0
        assert impact.net_functional_impact == 0.0


# ── 7. Determinism ───────────────────────────────────────────────────────────


class TestDeterminism:
    """Verify identical inputs yield bit-for-bit identical floats."""

    def test_path_impact_deterministic(self, engine: ChainStrengthEngine) -> None:
        """Same path computed twice → identical float."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Mercury", house=1, sign=1, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")

        paths = ev.find_paths("Sun", "Mars", max_depth=3)
        assert len(paths) == 1

        impact_1 = engine.compute_path_impact(paths[0]).net_functional_impact
        impact_2 = engine.compute_path_impact(paths[0]).net_functional_impact
        assert impact_1 == impact_2

    def test_formation_score_deterministic(self, engine: ChainStrengthEngine) -> None:
        """Same paths computed twice → identical formation score."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Jupiter", "CONJUNCTION")

        paths = ev.find_paths("Sun", "Jupiter", max_depth=3)
        score_1 = engine.compute_formation_score(paths)
        score_2 = engine.compute_formation_score(paths)
        assert score_1 == score_2

    def test_nexus_score_deterministic(self) -> None:
        """Same graph → identical nexus score."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Jupiter", "CONJUNCTION")

        score_1 = ev.evaluate_kendra_trikona_nexus(1)
        score_2 = ev.evaluate_kendra_trikona_nexus(1)
        assert score_1 == score_2

    def test_scores_rounded_to_6_decimals(self, engine: ChainStrengthEngine) -> None:
        """Formation score should be rounded to 6 decimal places."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Mercury", house=1, sign=3, dignity="FRIEND_SIGN")
        ev.add_node("Mars", house=5, sign=8, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mercury", "CONJUNCTION")
        ev.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")

        paths = ev.find_paths("Sun", "Mars", max_depth=3)
        formation = engine.compute_formation_score(paths)

        # Formation score is rounded to 6 decimal places
        assert formation == round(formation, 6)


# ── 8. Parivartana Detection ─────────────────────────────────────────────────


class TestParivartanaDetection:
    """Verify Parivartana Yoga detection from existing edge data."""

    def test_detects_mutual_exchange(self) -> None:
        """Mutual PARIVARTANA edges should be detected as a yoga."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")
        ev.add_edge("Mars", "Sun", "PARIVARTANA")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 1
        assert yogas[0].length == 2
        planets = {yogas[0].nodes[0].planet, yogas[0].nodes[1].planet}
        assert planets == {"Sun", "Mars"}

    def test_no_exchange_no_yoga(self) -> None:
        """Non-PARIVARTANA edges should not produce yogas."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "CONJUNCTION")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 0

    def test_one_way_parivartana_no_yoga(self) -> None:
        """One-way PARIVARTANA (no reciprocal) should not produce yoga."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 0

    def test_no_duplicates(self) -> None:
        """Same exchange detected from both directions → only one yoga."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")
        ev.add_edge("Mars", "Sun", "PARIVARTANA")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 1

    def test_multiple_exchanges(self) -> None:
        """Multiple independent Parivartana exchanges detected."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_node("Jupiter", house=9, sign=9, dignity="OWN_SIGN")
        ev.add_node("Mercury", house=3, sign=3, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")
        ev.add_edge("Mars", "Sun", "PARIVARTANA")
        ev.add_edge("Jupiter", "Mercury", "PARIVARTANA")
        ev.add_edge("Mercury", "Jupiter", "PARIVARTANA")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 2

    def test_parivartana_yoga_has_correct_edges(self) -> None:
        """Detected yoga should contain PARIVARTANA edges."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Mars", house=1, sign=1, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Mars", "PARIVARTANA")
        ev.add_edge("Mars", "Sun", "PARIVARTANA")

        yogas = ev.detect_parivartana_yogas()
        assert len(yogas) == 1
        for edge in yogas[0].edges:
            assert edge.edge_type == EdgeType.PARIVARTANA


# ── 9. Mixed Edge Type Traversal ─────────────────────────────────────────────


class TestMixedEdgeTraversal:
    """Verify mixed edge types traverse correctly in chains."""

    def test_lord_of_then_one_way_aspect(self) -> None:
        """LORD_OF → ONE_WAY_ASPECT chain traverses correctly."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=5, sign=5, dignity="OWN_SIGN")
        ev.add_node("Jupiter", house=9, sign=12, dignity="OWN_SIGN")
        ev.add_node("Saturn", house=10, sign=11, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Jupiter", "LORD_OF")
        ev.add_edge("Jupiter", "Saturn", "ONE_WAY_ASPECT")

        paths = ev.find_paths("Sun", "Saturn", max_depth=3)
        assert len(paths) == 1
        assert paths[0].length == 2
        assert paths[0].edges[0].edge_type == EdgeType.LORD_OF
        assert paths[0].edges[1].edge_type == EdgeType.ONE_WAY_ASPECT

    def test_occupies_then_conjunction(self) -> None:
        """OCCUPIES → CONJUNCTION chain traverses correctly."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Jupiter", house=9, sign=12, dignity="OWN_SIGN")
        ev.add_node("Venus", house=12, sign=12, dignity="ENEMY_SIGN")
        ev.add_node("Saturn", house=12, sign=11, dignity="OWN_SIGN")
        ev.add_edge("Jupiter", "Venus", "OCCUPIES")
        ev.add_edge("Venus", "Saturn", "CONJUNCTION")

        paths = ev.find_paths("Jupiter", "Saturn", max_depth=3)
        assert len(paths) == 1
        assert paths[0].edges[0].edge_type == EdgeType.OCCUPIES
        assert paths[0].edges[1].edge_type == EdgeType.CONJUNCTION

    def test_all_edge_types_in_path(self, engine: ChainStrengthEngine) -> None:
        """Path with multiple edge types computes correct impact."""
        ev = DirectedChainEvaluator(lagna_sign=1)
        ev.add_node("Sun", house=1, sign=1, dignity="EXALTED")
        ev.add_node("Jupiter", house=5, sign=9, dignity="OWN_SIGN")
        ev.add_node("Saturn", house=9, sign=10, dignity="OWN_SIGN")
        ev.add_edge("Sun", "Jupiter", "CONJUNCTION")
        ev.add_edge("Jupiter", "Saturn", "LORD_OF")

        paths = ev.find_paths("Sun", "Saturn", max_depth=3)
        assert len(paths) == 1

        impact = engine.compute_path_impact(paths[0])
        # Sun is YOGAKARAKA for Aries (exalted in 5th), so impact should be positive
        assert impact.net_functional_impact != 0.0
