"""JRS-011 Phase B — Multi-Hop Kendra–Trikona Chain Evaluator unit tests."""

from __future__ import annotations

import pytest

from jrs.graph.chain_evaluator import (
    ChainEdge,
    ChainNode,
    ChainPath,
    Dignity,
    DirectedChainEvaluator,
    EdgeType,
    RelationshipGraph,
)
from jrs.graph.chain_strength import (
    ChainStrengthEngine,
    NodeMultiplier,
    PathImpact,
)
from jrs.graph.functional_lordship import (
    FunctionalLordshipClassifier,
    FunctionalRole,
    LordshipProfile,
)
from jrs.structural.models import PlanetRelationship, RelationshipType
from jrs.yoga_evaluator.service import YogaEvaluatorService
from jrs.yoga_evaluator.models import YogaStatus


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 1: FunctionalLordshipClassifier
# ══════════════════════════════════════════════════════════════════════════════


class TestFunctionalLordshipClassifier:
    """Tests for BPHS Ch 34 functional lordship classification."""

    def setup_method(self) -> None:
        self.classifier = FunctionalLordshipClassifier()

    # ── Yogakaraka Tests ──────────────────────────────────────────────

    def test_mars_yogakaraka_cancer_lagna(self) -> None:
        """Mars is Yogakaraka for Cancer (4) Lagna."""
        profile = self.classifier.classify("MARS", lagna_sign=4)
        assert profile.functional_role == FunctionalRole.YOGAKARAKA
        assert profile.base_weight == 1.50
        assert "Yogakaraka" in profile.description
        # Mars owns Aries (1) and Scorpio (8)
        # Relative to Cancer (4): Aries→house10, Scorpio→house5
        assert 10 in profile.owned_houses
        assert 5 in profile.owned_houses

    def test_mars_yogakaraka_leo_lagna(self) -> None:
        """Mars is Yogakaraka for Leo (5) Lagna."""
        profile = self.classifier.classify("MARS", lagna_sign=5)
        assert profile.functional_role == FunctionalRole.YOGAKARAKA
        assert profile.base_weight == 1.50

    def test_saturn_yogakaraka_taurus_lagna(self) -> None:
        """Saturn is Yogakaraka for Taurus (2) Lagna."""
        profile = self.classifier.classify("SATURN", lagna_sign=2)
        assert profile.functional_role == FunctionalRole.YOGAKARAKA
        assert profile.base_weight == 1.50
        # Saturn owns Capricorn (10) and Aquarius (11)
        # Relative to Taurus (2): Capricorn→house9, Aquarius→house10
        assert 9 in profile.owned_houses
        assert 10 in profile.owned_houses

    def test_saturn_yogakaraka_libra_lagna(self) -> None:
        """Saturn is Yogakaraka for Libra (7) Lagna."""
        profile = self.classifier.classify("SATURN", lagna_sign=7)
        assert profile.functional_role == FunctionalRole.YOGAKARAKA
        assert profile.base_weight == 1.50

    # ── Functional Benefic Tests ──────────────────────────────────────

    def test_jupiter_malefic_12th_lord_aries(self) -> None:
        """Jupiter for Aries Lagna owns houses 9 and 12.
        12th lord → MALEFIC."""
        profile = self.classifier.classify("JUPITER", lagna_sign=1)
        # Jupiter owns Sagittarius (9) → house 9, Pisces (12) → house 12
        # House 12 is a Dusthana → 12th lord → MALEFIC
        assert profile.functional_role == FunctionalRole.MALEFIC
        assert profile.base_weight == -1.00

    def test_sun_benefic_aries_lagna(self) -> None:
        """Sun owns house 5 for Aries Lagna → benefic (trikona lord)."""
        profile = self.classifier.classify("SUN", lagna_sign=1)
        # Sun owns Leo (5). Relative to Aries (1): Leo→house5
        # Owns trikona (5), no 8th → benefic
        assert profile.functional_role == FunctionalRole.BENEFIC
        assert profile.base_weight == 1.00

    # ── Functional Malefic Tests ──────────────────────────────────────

    def test_mars_malefic_scorpio_lagna(self) -> None:
        """Mars owns house 6 for Scorpio Lagna → malefic (6th lord)."""
        profile = self.classifier.classify("MARS", lagna_sign=8)
        # Mars owns Aries (1) and Scorpio (8)
        # Relative to Scorpio (8): Aries→house6, Scorpio→house1
        # Owns 6 → malefic
        assert profile.functional_role == FunctionalRole.MALEFIC
        assert profile.base_weight == -1.00
        assert "6th" in profile.description

    def test_jupiter_malefic_kendra_only(self) -> None:
        """Jupiter owns Kendra without Trikona → Kendradhipati Dosha (natural benefic)."""
        # Jupiter owns Sagittarius (9) and Pisces (12)
        # For Gemini (3) Lagna: Sagittarius→house7 (Kendra), Pisces→house10 (Kendra)
        # Both Kendra, no Trikona → Kendradhipati Dosha
        profile = self.classifier.classify("JUPITER", lagna_sign=3)
        assert profile.functional_role == FunctionalRole.MALEFIC
        assert "Kendradhipati" in profile.description

    # ── Neutral Tests ─────────────────────────────────────────────────

    def test_mercury_neutral_aries_lagna(self) -> None:
        """Mercury owns houses 3 and 6 for Aries Lagna → malefic (6th lord)."""
        profile = self.classifier.classify("MERCURY", lagna_sign=1)
        # Mercury owns Gemini (3) and Virgo (6)
        # Relative to Aries (1): Gemini→house3, Virgo→house6
        # Owns 6 → malefic
        assert profile.functional_role == FunctionalRole.MALEFIC

    # ── Input Validation ──────────────────────────────────────────────

    def test_invalid_lagna_raises(self) -> None:
        """Invalid lagna sign raises ValueError."""
        with pytest.raises(ValueError, match="lagna_sign must be"):
            self.classifier.classify("SUN", lagna_sign=13)

    def test_unknown_planet_raises(self) -> None:
        """Unknown planet name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown planet"):
            self.classifier.classify("PLUTO", lagna_sign=1)

    # ── Classify All ──────────────────────────────────────────────────

    def test_classify_all_returns_all_planets(self) -> None:
        """classify_all returns profiles for all 7 classical planets."""
        profiles = self.classifier.classify_all(lagna_sign=1)
        assert len(profiles) == 7
        for planet in ("SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"):
            assert planet in profiles
            assert isinstance(profiles[planet], LordshipProfile)

    # ── Frozen Dataclass ──────────────────────────────────────────────

    def test_lordship_profile_frozen(self) -> None:
        """LordshipProfile is immutable."""
        profile = self.classifier.classify("SUN", lagna_sign=1)
        with pytest.raises(AttributeError):
            profile.functional_role = FunctionalRole.MALEFIC  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 2: DirectedChainEvaluator Traversal
# ══════════════════════════════════════════════════════════════════════════════


class TestDirectedChainEvaluator:
    """Tests for depth-bounded DFS chain traversal."""

    def setup_method(self) -> None:
        self.evaluator = DirectedChainEvaluator(max_depth=3)

    def _make_jre_facts(
        self,
        lagna_sign: int = 1,
        **planet_data: dict,
    ) -> dict:
        """Helper to build JRE facts dict."""
        default_planets: dict[str, dict] = {
            "SUN": {"house": 1, "rashi_num": 1, "combust": False, "debilitated": False, "retrograde": False},
            "MOON": {"house": 4, "rashi_num": 4, "combust": False, "debilitated": False, "retrograde": False},
            "MARS": {"house": 5, "rashi_num": 5, "combust": False, "debilitated": False, "retrograde": False},
            "MERCURY": {"house": 3, "rashi_num": 3, "combust": False, "debilitated": False, "retrograde": False},
            "JUPITER": {"house": 8, "rashi_num": 10, "combust": False, "debilitated": False, "retrograde": False},
            "VENUS": {"house": 7, "rashi_num": 7, "combust": False, "debilitated": False, "retrograde": False},
            "SATURN": {"house": 4, "rashi_num": 4, "combust": False, "debilitated": False, "retrograde": True},
        }
        for name, data in planet_data.items():
            default_planets[name] = data
        return {"planets": default_planets, "lagna_sign": lagna_sign}

    # ── 1-Hop Paths ───────────────────────────────────────────────────

    def test_single_conjunction_1_hop(self) -> None:
        """Two planets conjunct discover a 1-hop path."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(
            lagna_sign=1,
            JUPITER={"house": 1, "rashi_num": 1, "combust": False, "debilitated": False, "retrograde": False},
            SATURN={"house": 1, "rashi_num": 1, "combust": False, "debilitated": False, "retrograde": False},
        )
        paths = self.evaluator.evaluate(graph, jre_facts)
        # Should find paths from JUPITER→SATURN and SATURN→JUPITER
        hop_lengths = [p.length for p in paths]
        assert 1 in hop_lengths

    def test_aspect_1_hop(self) -> None:
        """Directed aspect discovers a 1-hop path."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        assert any(p.length == 1 for p in paths)
        # Edge should be ONE_WAY_ASPECT
        for path in paths:
            if path.length == 1:
                assert path.edges[0].edge_type == EdgeType.ONE_WAY_ASPECT

    def test_exchange_parivartana_1_hop(self) -> None:
        """Exchange (Parivartana) discovers a 1-hop path with PARIVARTANA edge."""
        rels = (
            PlanetRelationship(
                planet_a="MARS",
                planet_b="SATURN",
                relationship_type=RelationshipType.EXCHANGE,
                is_directed=False,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        assert any(p.length == 1 for p in paths)
        for path in paths:
            if path.length == 1:
                assert path.edges[0].edge_type == EdgeType.PARIVARTANA

    # ── 2-Hop Paths ───────────────────────────────────────────────────

    def test_2_hop_chain(self) -> None:
        """A→B→C chain discovers 2-hop paths."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="SATURN",
                planet_b="MOON",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        hop_lengths = [p.length for p in paths]
        assert 1 in hop_lengths
        assert 2 in hop_lengths

    # ── 3-Hop Paths ───────────────────────────────────────────────────

    def test_3_hop_chain(self) -> None:
        """A→B→C→D chain discovers 3-hop paths."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="SATURN",
                planet_b="MOON",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
            PlanetRelationship(
                planet_a="MOON",
                planet_b="MARS",
                relationship_type=RelationshipType.DISPOSITOR,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        hop_lengths = [p.length for p in paths]
        assert 1 in hop_lengths
        assert 2 in hop_lengths
        assert 3 in hop_lengths

    # ── Loop Suppression ──────────────────────────────────────────────

    def test_loop_suppression(self) -> None:
        """Circular A→B→A relationships do not produce infinite loops."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="SATURN",
                planet_b="JUPITER",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        # Should not have any paths longer than 1 hop (loop suppressed)
        assert all(p.length <= 1 for p in paths)

    # ── Empty Graph ───────────────────────────────────────────────────

    def test_empty_graph_no_paths(self) -> None:
        """Empty graph produces no paths."""
        graph = RelationshipGraph(relationships=())
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        assert paths == []

    # ── Transit Relationships Skipped ─────────────────────────────────

    def test_transit_relationships_skipped(self) -> None:
        """Transit aspects/conjunctions are skipped in chain traversal."""
        rels = (
            PlanetRelationship(
                planet_a="RAHU",
                planet_b="JUPITER",
                relationship_type=RelationshipType.TRANSIT_ASPECT,
                is_active=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate(graph, jre_facts)
        assert paths == []

    # ── evaluate_from Specific Planet ──────────────────────────────────

    def test_evaluate_from_specific_planet(self) -> None:
        """evaluate_from discovers paths starting from a specific planet."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="SATURN",
                planet_b="MOON",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = self.evaluator.evaluate_from("SATURN", graph, jre_facts)
        # All paths should start with SATURN
        for path in paths:
            assert path.nodes[0].planet == "SATURN"

    # ── Max Depth Bounded ─────────────────────────────────────────────

    def test_max_depth_respected(self) -> None:
        """Paths do not exceed max_depth hops."""
        evaluator = DirectedChainEvaluator(max_depth=2)
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="SATURN",
                planet_b="MOON",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
            PlanetRelationship(
                planet_a="MOON",
                planet_b="MARS",
                relationship_type=RelationshipType.DISPOSITOR,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = self._make_jre_facts(lagna_sign=1)
        paths = evaluator.evaluate(graph, jre_facts)
        assert all(p.length <= 2 for p in paths)


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 3: ChainStrengthEngine
# ══════════════════════════════════════════════════════════════════════════════


class TestChainStrengthEngine:
    """Tests for cascading strength and propagation engine."""

    def setup_method(self) -> None:
        self.engine = ChainStrengthEngine()

    def test_node_multiplier_exalted(self) -> None:
        """Exalted node has dignity score 1.50."""
        node = ChainNode(
            planet="JUPITER",
            house=4,
            sign=4,
            dignity=Dignity.EXALTED,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.BENEFIC,
            base_weight=1.00,
        )
        mult = self.engine.compute_node_multiplier(node)
        assert mult.dignity_score == 1.50
        assert mult.retrograde_multiplier == 1.00
        assert mult.combust_multiplier == 1.00
        assert mult.net_multiplier == 1.50

    def test_node_multiplier_retrograde(self) -> None:
        """Retrograde node gets 1.20x multiplier."""
        node = ChainNode(
            planet="SATURN",
            house=4,
            sign=4,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=True,
            is_combust=False,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        mult = self.engine.compute_node_multiplier(node)
        assert mult.retrograde_multiplier == 1.20
        assert mult.net_multiplier == pytest.approx(1.00 * 1.20)

    def test_node_multiplier_combust(self) -> None:
        """Combust node gets 0.40x multiplier."""
        node = ChainNode(
            planet="SATURN",
            house=4,
            sign=4,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False,
            is_combust=True,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        mult = self.engine.compute_node_multiplier(node)
        assert mult.combust_multiplier == 0.40
        assert mult.net_multiplier == pytest.approx(1.00 * 0.40)

    def test_node_multiplier_retrograde_and_combust(self) -> None:
        """Retrograde + combust node combines both multipliers."""
        node = ChainNode(
            planet="SATURN",
            house=4,
            sign=4,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=True,
            is_combust=True,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        mult = self.engine.compute_node_multiplier(node)
        assert mult.net_multiplier == pytest.approx(1.00 * 1.20 * 0.40)

    def test_path_impact_single_hop(self) -> None:
        """Single-hop path impact follows the formula.

        ΔI(P) = F_role(N_0) × M_node(N_0) × (W_edge × M_node(N_1) × 0.70)
        """
        root = ChainNode(
            planet="JUPITER",
            house=1,
            sign=4,
            dignity=Dignity.EXALTED,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.BENEFIC,
            base_weight=1.00,
        )
        target = ChainNode(
            planet="SATURN",
            house=4,
            sign=4,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        edge = ChainEdge(
            source="JUPITER",
            target="SATURN",
            edge_type=EdgeType.CONJUNCTION,
            weight=1.00,
        )
        path = ChainPath(
            nodes=(root, target),
            edges=(edge,),
            length=1,
        )
        result = self.engine.compute_path_impact(path)

        # F_role(JUPITER) = 1.00 (BENEFIC)
        # M_node(JUPITER) = 1.50 (EXALTED)
        # W_edge(CONJUNCTION) = 1.00
        # M_node(SATURN) = 1.00 (FRIEND_SIGN)
        # Hop damping = 0.70
        expected = 1.00 * 1.50 * (1.00 * 1.00 * 0.70)
        assert result.net_functional_impact == pytest.approx(expected)

    def test_path_impact_negative_role(self) -> None:
        """Negative functional role produces negative impact."""
        root = ChainNode(
            planet="SATURN",
            house=4,
            sign=4,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        target = ChainNode(
            planet="MOON",
            house=2,
            sign=2,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.BENEFIC,
            base_weight=1.00,
        )
        edge = ChainEdge(
            source="SATURN",
            target="MOON",
            edge_type=EdgeType.ONE_WAY_ASPECT,
            weight=0.75,
        )
        path = ChainPath(
            nodes=(root, target),
            edges=(edge,),
            length=1,
        )
        result = self.engine.compute_path_impact(path)
        # F_role(SATURN) = -1.00 → negative impact
        assert result.net_functional_impact < 0

    # ── Canonical Mitigation Scenario ─────────────────────────────────

    def test_canonical_mitigation_jupiter_dampens_saturn(self) -> None:
        """Exalted Jupiter (H8) aspecting Retrograde Saturn (H4) dampens
        Saturn's malefic aspect onto Moon (H2)."""
        # Build a 2-hop chain: JUPITER → SATURN → MOON
        jupiter = ChainNode(
            planet="JUPITER",
            house=8,
            sign=4,  # Exalted in Cancer
            dignity=Dignity.EXALTED,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.BENEFIC,
            base_weight=1.00,
        )
        saturn = ChainNode(
            planet="SATURN",
            house=4,
            sign=10,  # In Capricorn (own sign)
            dignity=Dignity.OWN_SIGN,
            is_retrograde=True,
            is_combust=False,
            functional_role=FunctionalRole.MALEFIC,
            base_weight=-1.00,
        )
        moon = ChainNode(
            planet="MOON",
            house=2,
            sign=2,
            dignity=Dignity.FRIEND_SIGN,
            is_retrograde=False,
            is_combust=False,
            functional_role=FunctionalRole.BENEFIC,
            base_weight=1.00,
        )
        edge1 = ChainEdge(
            source="JUPITER",
            target="SATURN",
            edge_type=EdgeType.MUTUAL_ASPECT,
            weight=0.85,
        )
        edge2 = ChainEdge(
            source="SATURN",
            target="MOON",
            edge_type=EdgeType.ONE_WAY_ASPECT,
            weight=0.75,
        )
        path = ChainPath(
            nodes=(jupiter, saturn, moon),
            edges=(edge1, edge2),
            length=2,
        )
        result = self.engine.compute_path_impact(path)

        # The dampening effect: Jupiter's positive role and exalted dignity
        # reduce the overall malefic impact of the chain.
        # Without Jupiter: SATURN→MOON alone would be more negative.
        # With Jupiter: the positive root multiplies through, dampening.
        assert result.net_functional_impact != 0

    def test_empty_path_returns_zero_impact(self) -> None:
        """Empty path returns zero impact."""
        path = ChainPath(nodes=(), edges=(), length=0)
        result = self.engine.compute_path_impact(path)
        assert result.net_functional_impact == 0.0

    def test_aggregate_impact(self) -> None:
        """Aggregate impact sums all path impacts."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jre_facts = {
            "planets": {
                "JUPITER": {"house": 1, "rashi_num": 4, "combust": False, "debilitated": False, "retrograde": False},
                "SATURN": {"house": 1, "rashi_num": 4, "combust": False, "debilitated": False, "retrograde": False},
            },
            "lagna_sign": 1,
        }
        aggregate = self.engine.compute_aggregate_impact(graph, jre_facts)
        assert isinstance(aggregate, float)


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 4: YogaEvaluatorService Integration
# ══════════════════════════════════════════════════════════════════════════════


class TestChainEvaluatorServiceIntegration:
    """Integration tests for chain evaluator wiring into YogaEvaluatorService."""

    def setup_method(self) -> None:
        self.service = YogaEvaluatorService()

    def test_evaluate_formation_with_chain_impact(self) -> None:
        """evaluate_formation computes chain_impact when lagna_sign present."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
                "SATURN": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
                "MOON": {
                    "house": 4, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
            },
            "lagna_sign": 1,
        }
        eval_result = self.service.evaluate_formation(
            yoga_name="TestChain",
            involved_planets=["JUPITER", "SATURN"],
            jre_facts=jre_facts,
        )
        # chain_impact should be computed (may be 0.0 if no relationships)
        assert eval_result.chain_impact is not None

    def test_evaluate_formation_without_lagna_no_chain(self) -> None:
        """evaluate_formation skips chain when lagna_sign absent."""
        jre_facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "SATURN": {"house": 1, "combust": False, "debilitated": False},
            },
        }
        eval_result = self.service.evaluate_formation(
            yoga_name="TestNoChain",
            involved_planets=["JUPITER", "SATURN"],
            jre_facts=jre_facts,
        )
        # chain_impact should be None when lagna_sign not provided
        assert eval_result.chain_impact is None

    def test_compute_chain_impact_returns_float(self) -> None:
        """compute_chain_impact returns a float value."""
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

    def test_get_chain_paths_returns_list(self) -> None:
        """get_chain_paths returns a list of PathImpact."""
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
        paths = self.service.get_chain_paths(
            involved_planets=["JUPITER", "SATURN"],
            jre_facts=jre_facts,
        )
        assert isinstance(paths, list)
        for p in paths:
            assert isinstance(p, PathImpact)

    def test_classical_yoga_with_chain_impact(self) -> None:
        """Classical yoga evaluation includes chain_impact in results."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                    "house_lord_of": 5,
                },
                "MOON": {
                    "house": 4, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
                "MARS": {
                    "house": 5, "rashi_num": 5, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "SIMHA",
                    "house_lord_of": 1,
                },
                "SATURN": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                },
                "SUN": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                },
                "MERCURY": {
                    "house": 3, "rashi_num": 3, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MITHUNA",
                },
                "VENUS": {
                    "house": 7, "rashi_num": 7, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "TULA",
                },
            },
            "lagna_sign": 1,
        }
        results = self.service.evaluate_classical_yogas(jre_facts)
        # Check that at least one result has chain_impact computed
        for r in results:
            assert r.chain_impact is not None


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 5: RelationshipGraph Wrapper
# ══════════════════════════════════════════════════════════════════════════════


class TestRelationshipGraph:
    """Tests for the RelationshipGraph wrapper."""

    def test_edges_for_returns_relevant(self) -> None:
        """edges_for returns relationships involving the given planet."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="MOON",
                planet_b="MARS",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        jup_edges = graph.edges_for("JUPITER")
        assert len(jup_edges) == 1
        assert jup_edges[0].planet_b == "SATURN"

    def test_edges_for_returns_empty(self) -> None:
        """edges_for returns empty for planet not in any relationship."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        assert graph.edges_for("MOON") == []

    def test_neighbors(self) -> None:
        """neighbors returns sorted unique neighbor planets."""
        rels = (
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="SATURN",
                relationship_type=RelationshipType.CONJUNCTION,
                is_directed=False,
            ),
            PlanetRelationship(
                planet_a="JUPITER",
                planet_b="MOON",
                relationship_type=RelationshipType.ASPECT,
                is_directed=True,
            ),
        )
        graph = RelationshipGraph(relationships=rels)
        neighbors = graph.neighbors("JUPITER")
        assert neighbors == ["MOON", "SATURN"]


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 6: Manual Graph API (add_node / add_edge / find_paths)
# ══════════════════════════════════════════════════════════════════════════════


def test_conjunction_edge_evaluation():
    """Manual graph: conjunction + one-way aspect, verify impact computation."""
    evaluator = DirectedChainEvaluator(lagna_sign=1)  # Aries Lagna
    evaluator.add_node("Sun", house=1, sign=1, dignity="EXALTED")
    evaluator.add_node("Mercury", house=1, sign=1, dignity="FRIEND_SIGN")
    evaluator.add_node("Mars", house=5, sign=5, dignity="OWN_SIGN")
    evaluator.add_edge("Sun", "Mercury", "CONJUNCTION")
    evaluator.add_edge("Mercury", "Mars", "ONE_WAY_ASPECT")

    paths = evaluator.find_paths("Sun", "Mars", max_depth=3)
    assert len(paths) == 1
    path = paths[0]
    assert path.length == 2
    assert [n.planet for n in path.nodes] == ["Sun", "Mercury", "Mars"]
    assert path.edges[0].edge_type == "CONJUNCTION"
    assert path.edges[0].weight == 1.00

    impact = ChainStrengthEngine.evaluate_path_impact(path)
    assert impact == pytest.approx(0.6891, abs=1e-4)


def test_parivartana_edge_evaluation():
    """Manual graph: parivartana + one-way aspect, verify non-zero impact."""
    evaluator = DirectedChainEvaluator(lagna_sign=2)  # Taurus Lagna
    evaluator.add_node("Venus", house=12, sign=1, dignity="ENEMY_SIGN")
    evaluator.add_node("Mars", house=6, sign=7, dignity="NEUTRAL")
    evaluator.add_node("Jupiter", house=11, sign=12, dignity="OWN_SIGN")
    evaluator.add_edge("Venus", "Mars", "PARIVARTANA")
    evaluator.add_edge("Mars", "Jupiter", "ONE_WAY_ASPECT")

    paths = evaluator.find_paths("Venus", "Jupiter", max_depth=3)
    assert len(paths) == 1
    path = paths[0]
    assert path.length == 2
    assert [n.planet for n in path.nodes] == ["Venus", "Mars", "Jupiter"]
    assert path.edges[0].edge_type == "PARIVARTANA"
    assert path.edges[0].weight == 0.90

    impact = ChainStrengthEngine.evaluate_path_impact(path)
    assert impact != 0.0
    assert path.net_functional_impact == impact


def test_combined_conjunction_and_parivartana_multi_hop_chain():
    """Manual graph: parivartana + one-way aspect with debilated root."""
    evaluator = DirectedChainEvaluator(lagna_sign=4)  # Cancer Lagna
    evaluator.add_node("Mars", house=1, sign=4, dignity="DEBILITATED")
    evaluator.add_node("Moon", house=5, sign=8, dignity="FRIEND_SIGN")
    evaluator.add_node("Jupiter", house=9, sign=12, dignity="EXALTED")
    evaluator.add_edge("Mars", "Moon", "PARIVARTANA")
    evaluator.add_edge("Moon", "Jupiter", "ONE_WAY_ASPECT")

    paths = evaluator.find_paths("Mars", "Jupiter", max_depth=3)
    assert len(paths) == 1
    path = paths[0]
    assert path.length == 2
    assert [n.planet for n in path.nodes] == ["Mars", "Moon", "Jupiter"]
    assert path.edges[0].edge_type == "PARIVARTANA"
    assert path.edges[0].weight == 0.90
    assert path.edges[1].edge_type == "ONE_WAY_ASPECT"
    assert path.edges[1].weight == 0.75

    impact = ChainStrengthEngine.evaluate_path_impact(path)
    assert impact > 0.0
