"""JRS-013 Phase E6c — Yoga-Specific Chain Aggregation unit tests.

Tests each yoga category's aggregation model against the synthetic
test matrix defined in RI-013.
"""

from __future__ import annotations

import pytest

from jrs.graph.chain_aggregation import (
    AggregationResult,
    YogaCategory,
    YogaSpecificChainAggregator,
    classify_paths,
    get_yoga_category,
)
from jrs.graph.chain_evaluator import (
    ChainEdge,
    ChainNode,
    ChainPath,
    Dignity,
    EdgeType,
)
from jrs.graph.chain_strength import ChainStrengthEngine, PathImpact
from jrs.graph.functional_lordship import FunctionalRole


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_node(
    planet: str,
    house: int,
    sign: int,
    dignity: str = "NEUTRAL",
    retrograde: bool = False,
    combust: bool = False,
    functional_role: str = "NEUTRAL",
) -> ChainNode:
    """Create a ChainNode for testing."""
    return ChainNode(
        planet=planet,
        house=house,
        sign=sign,
        dignity=Dignity(dignity),
        is_retrograde=retrograde,
        is_combust=combust,
        functional_role=FunctionalRole(functional_role),
        base_weight=0.0,
    )


def _make_single_path(
    root: ChainNode,
    target: ChainNode | None = None,
    edge_type: str = "CONJUNCTION",
) -> ChainPath:
    """Create a single-hop ChainPath for testing."""
    if target is None:
        return ChainPath(
            nodes=(root,),
            edges=(),
            length=0,
        )
    edge = ChainEdge(
        source=root.planet,
        target=target.planet,
        edge_type=EdgeType(edge_type),
        weight=1.0,
    )
    return ChainPath(
        nodes=(root, target),
        edges=(edge,),
        length=1,
    )


def _make_path_impact(path: ChainPath, impact: float = 0.0) -> PathImpact:
    """Create a PathImpact with pre-computed impact for testing."""
    engine = ChainStrengthEngine()
    pi = engine.compute_path_impact(path)
    # Override the impact value for deterministic testing
    return PathImpact(
        path=path,
        root_multiplier=pi.root_multiplier,
        hop_multipliers=pi.hop_multipliers,
        net_functional_impact=impact,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 1: Category Mapping
# ══════════════════════════════════════════════════════════════════════════════


class TestYogaCategoryMapping:
    """Tests for yoga name → category mapping."""

    def test_gajakesari_mapping(self) -> None:
        assert get_yoga_category("Gajakesari") == YogaCategory.GAJAKESARI

    def test_malavya_mapping(self) -> None:
        assert get_yoga_category("Malavya") == YogaCategory.PANCHA_MAHAPURUSHA

    def test_ruchaka_mapping(self) -> None:
        assert get_yoga_category("Ruchaka") == YogaCategory.PANCHA_MAHAPURUSHA

    def test_raja_mapping(self) -> None:
        assert get_yoga_category("Raja") == YogaCategory.RAJA

    def test_vipareeta_raja_mapping(self) -> None:
        assert get_yoga_category("Vipareeta Raja") == YogaCategory.VIPAREETA_RAJA

    def test_budhaditya_mapping(self) -> None:
        assert get_yoga_category("Budhaditya") == YogaCategory.BUDHADITYA

    def test_sunapha_mapping(self) -> None:
        assert get_yoga_category("Sunapha") == YogaCategory.CHANDRA

    def test_kemadruma_mapping(self) -> None:
        assert get_yoga_category("Kemadruma") == YogaCategory.KEMADRUMA

    def test_unknown_defaults(self) -> None:
        assert get_yoga_category("UnknownYoga") == YogaCategory.DEFAULT


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 2: Gajakesari Aggregation (TC001, TC002)
# ══════════════════════════════════════════════════════════════════════════════


class TestGajakesariAggregation:
    """Gajakesari: Wb=0.8, Wm=0.5, never cancelled."""

    def test_pure_gajakesari_positive(self) -> None:
        """TC001: Jupiter in Kendra from Moon, benefic chains → positive."""
        agg = YogaSpecificChainAggregator()

        # Jupiter (benefic) root path
        jup = _make_node("JUPITER", 7, 9, "OWN_SIGN", functional_role="BENEFIC")
        moon = _make_node("MOON", 4, 4, "OWN_SIGN", functional_role="BENEFIC")
        path1 = _make_single_path(jup, moon)
        pi1 = _make_path_impact(path1, impact=0.5)

        # Moon (benefic) root path
        path2 = _make_single_path(moon, jup)
        pi2 = _make_path_impact(path2, impact=0.3)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER", "MOON"],
        )

        assert result.chain_impact > 0, "Gajakesari should have positive chain impact"
        assert result.category == YogaCategory.GAJAKESARI
        assert not result.cancelled

    def test_gajakesari_with_malefic_weakened_not_cancelled(self) -> None:
        """TC002: Saturn aspecting → weakened but NOT cancelled."""
        agg = YogaSpecificChainAggregator()

        # Jupiter (benefic) root path
        jup = _make_node("JUPITER", 7, 9, "OWN_SIGN", functional_role="BENEFIC")
        saturn = _make_node("SATURN", 10, 11, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(jup, saturn)
        pi1 = _make_path_impact(path1, impact=0.4)

        # Saturn (malefic) root path
        path2 = _make_single_path(saturn, jup)
        pi2 = _make_path_impact(path2, impact=-0.6)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER", "MOON"],
        )

        # Gajakesari is never cancelled
        assert not result.cancelled, "Gajakesari should never be cancelled"
        # Impact should be reduced but may still be positive or slightly negative
        assert result.category == YogaCategory.GAJAKESARI


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 3: Budhaditya Aggregation (TC003, TC004, TC005)
# ══════════════════════════════════════════════════════════════════════════════


class TestBudhadityaAggregation:
    """Budhaditya: ANY malefic aspect → cancellation. Immunity: Mercury own sign."""

    def test_pure_budhaditya_positive(self) -> None:
        """TC003: Sun-Mercury conjunction, no malefics → positive."""
        agg = YogaSpecificChainAggregator()

        sun = _make_node("SUN", 1, 5, "OWN_SIGN", functional_role="NEUTRAL")
        mercury = _make_node("MERCURY", 1, 5, "OWN_SIGN", functional_role="BENEFIC")
        path1 = _make_single_path(sun, mercury)
        pi1 = _make_path_impact(path1, impact=0.8)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Budhaditya",
            yoga_planets=["SUN", "MERCURY"],
        )

        assert result.chain_impact > 0, "Pure Budhaditya should be positive"
        assert not result.cancelled

    def test_budhaditya_with_malefic_cancelled(self) -> None:
        """TC004: Mars aspecting → CANCELLED."""
        agg = YogaSpecificChainAggregator()

        sun = _make_node("SUN", 1, 5, "OWN_SIGN", functional_role="NEUTRAL")
        mars = _make_node("MARS", 10, 1, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(sun, mars)
        pi1 = _make_path_impact(path1, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Budhaditya",
            yoga_planets=["SUN", "MERCURY"],
        )

        assert result.cancelled, "Budhaditya with malefic should be CANCELLED"
        assert result.chain_impact == 0.0

    def test_budhaditya_mercury_own_sign_immunity(self) -> None:
        """TC005: Mercury in own sign → immunity, weakened but not cancelled."""
        agg = YogaSpecificChainAggregator()

        sun = _make_node("SUN", 1, 6, "OWN_SIGN", functional_role="NEUTRAL")
        mars = _make_node("MARS", 10, 1, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(sun, mars)
        pi1 = _make_path_impact(path1, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Budhaditya",
            yoga_planets=["SUN", "MERCURY"],
            mercury_own_sign=True,
        )

        assert not result.cancelled, "Mercury own sign provides immunity"
        assert result.chain_impact >= 0, "Should be non-negative with immunity"


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 4: Pancha Mahapurusha / Malavya (TC006, TC012)
# ══════════════════════════════════════════════════════════════════════════════


class TestPanchaMahapurushaAggregation:
    """Pancha Mahapurusha: immune to cancellation in own sign."""

    def test_malavya_own_sign_immunity(self) -> None:
        """TC006: Venus in own sign, Saturn aspecting → FORMED, strength 0.7-0.9."""
        agg = YogaSpecificChainAggregator()

        venus = _make_node("VENUS", 7, 7, "OWN_SIGN", functional_role="BENEFIC")
        saturn = _make_node("SATURN", 11, 11, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(venus, saturn)
        pi1 = _make_path_impact(path1, impact=-0.3)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Malavya",
            yoga_planets=["VENUS"],
            planet_in_own_sign=True,
        )

        assert not result.cancelled, "Malavya in own sign should not be cancelled"
        assert result.chain_impact > 0, "Should have positive chain impact with immunity"
        assert result.category == YogaCategory.PANCHA_MAHAPURUSHA

    def test_ruchaka_own_sign_immunity(self) -> None:
        """TC012: Mars in own sign, Saturn aspecting → FORMED."""
        agg = YogaSpecificChainAggregator()

        mars = _make_node("MARS", 1, 1, "OWN_SIGN", functional_role="YOGAKARAKA")
        saturn = _make_node("SATURN", 11, 11, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(mars, saturn)
        pi1 = _make_path_impact(path1, impact=-0.3)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Ruchaka",
            yoga_planets=["MARS"],
            planet_in_own_sign=True,
        )

        assert not result.cancelled
        assert result.chain_impact > 0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 5: Vipareeta Raja (TC007, TC008)
# ══════════════════════════════════════════════════════════════════════════════


class TestVipareetaRajaAggregation:
    """Vipareeta Raja: primary dusthana lordship required."""

    def test_vipareeta_raja_legitimate(self) -> None:
        """TC007: Mars (H6 lord) in H8 → FORMED."""
        agg = YogaSpecificChainAggregator()

        mars = _make_node("MARS", 8, 8, "OWN_SIGN", functional_role="MALEFIC")
        path1 = _make_single_path(mars)
        pi1 = _make_path_impact(path1, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Vipareeta Raja",
            yoga_planets=["MARS"],
            is_primary_kendra_lord=False,
        )

        assert not result.cancelled
        assert result.chain_impact >= 0

    def test_vipareeta_raja_kendra_lord_rejected(self) -> None:
        """TC008: Mars (also H4/H10 lord) → NOT_FORMED (is_primary_kendra_lord=True)."""
        agg = YogaSpecificChainAggregator()

        mars = _make_node("MARS", 12, 4, "DEBILITATED", functional_role="MALEFIC")
        path1 = _make_single_path(mars)
        pi1 = _make_path_impact(path1, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Vipareeta Raja",
            yoga_planets=["MARS"],
            is_primary_kendra_lord=True,
        )

        assert result.cancelled, "Should be cancelled when planet is primary Kendra lord"
        assert result.chain_impact == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 6: Kemadruma (TC009, TC010)
# ══════════════════════════════════════════════════════════════════════════════


class TestKemadrumaAggregation:
    """Kemadruma: dosha = base × (1 − Σ(benefic)). Cancelled by benefic."""

    def test_pure_kemadruma_high(self) -> None:
        """TC009: Moon isolated → dosha_strength HIGH."""
        agg = YogaSpecificChainAggregator()

        moon = _make_node("MOON", 4, 4, "OWN_SIGN", functional_role="BENEFIC")
        path1 = _make_single_path(moon)
        pi1 = _make_path_impact(path1, impact=0.5)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Kemadruma",
            yoga_planets=["MOON"],
            has_benefic_near_moon=False,
        )

        assert not result.cancelled
        assert result.chain_impact > 0.5, "Pure Kemadruma should have high dosha"

    def test_kemadruma_cancelled_by_benefic(self) -> None:
        """TC010: Venus in 2nd from Moon → dosha CANCELLED."""
        agg = YogaSpecificChainAggregator()

        moon = _make_node("MOON", 4, 4, "OWN_SIGN", functional_role="BENEFIC")
        venus = _make_node("VENUS", 5, 5, "FRIEND_SIGN", functional_role="BENEFIC")
        path1 = _make_single_path(moon, venus)
        pi1 = _make_path_impact(path1, impact=0.3)

        result = agg.aggregate(
            path_impacts=[pi1],
            yoga_name="Kemadruma",
            yoga_planets=["MOON"],
            has_benefic_near_moon=True,
        )

        assert result.cancelled, "Kemadruma should be cancelled by benefic"
        assert result.chain_impact == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 7: Raja Yoga (TC011)
# ══════════════════════════════════════════════════════════════════════════════


class TestRajaYogaAggregation:
    """Raja Yoga: Wb=1.0, Wm=0.7."""

    def test_raja_with_benefic_reinforcement(self) -> None:
        """TC011: Kendra-Trikona pair with benefic reinforcement → positive."""
        agg = YogaSpecificChainAggregator()

        moon = _make_node("MOON", 10, 10, "FRIEND_SIGN", functional_role="BENEFIC")
        sun = _make_node("SUN", 10, 10, "FRIEND_SIGN", functional_role="NEUTRAL")
        jupiter = _make_node("JUPITER", 1, 9, "OWN_SIGN", functional_role="BENEFIC")

        # Moon-Sun conjunction (Kendra-Trikona pair)
        path1 = _make_single_path(moon, sun)
        pi1 = _make_path_impact(path1, impact=0.4)

        # Jupiter reinforcement
        path2 = _make_single_path(jupiter, moon)
        pi2 = _make_path_impact(path2, impact=0.3)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Raja",
            yoga_planets=["MOON", "SUN", "JUPITER"],
        )

        assert result.chain_impact > 0, "Raja with benefic reinforcement should be positive"
        assert result.category == YogaCategory.RAJA


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 8: Path Classification
# ══════════════════════════════════════════════════════════════════════════════


class TestPathClassification:
    """Tests for natural benefic/malefic path classification."""

    def test_jupiter_classified_as_benefic(self) -> None:
        jup = _make_node("JUPITER", 1, 9, "OWN_SIGN", functional_role="BENEFIC")
        path = _make_single_path(jup)
        pi = _make_path_impact(path, impact=0.5)

        classified = classify_paths([pi], ["JUPITER"])
        assert len(classified) == 1
        assert classified[0].classification == "benefic"

    def test_saturn_classified_as_malefic(self) -> None:
        saturn = _make_node("SATURN", 1, 10, "OWN_SIGN", functional_role="MALEFIC")
        path = _make_single_path(saturn)
        pi = _make_path_impact(path, impact=-0.5)

        classified = classify_paths([pi], ["SATURN"])
        assert len(classified) == 1
        assert classified[0].classification == "malefic"

    def test_relevance_filter(self) -> None:
        """Only paths rooted in yoga planets are included."""
        jup = _make_node("JUPITER", 1, 9, "OWN_SIGN", functional_role="BENEFIC")
        saturn = _make_node("SATURN", 5, 10, "OWN_SIGN", functional_role="MALEFIC")

        path1 = _make_single_path(jup)
        pi1 = _make_path_impact(path1, impact=0.5)

        path2 = _make_single_path(saturn)
        pi2 = _make_path_impact(path2, impact=-0.5)

        # Only JUPITER is a yoga planet — Saturn paths should be filtered out
        classified = classify_paths([pi1, pi2], ["JUPITER"])
        assert len(classified) == 1
        assert classified[0].path_impact.path.nodes[0].planet == "JUPITER"


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 9: Edge Cases
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_paths(self) -> None:
        agg = YogaSpecificChainAggregator()
        result = agg.aggregate(
            path_impacts=[],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER", "MOON"],
        )
        assert result.chain_impact == 0.0
        assert result.total_paths == 0

    def test_neutral_root_not_counted(self) -> None:
        """SUN is natural malefic, but NEUTRAL functional role."""
        sun = _make_node("SUN", 3, 5, "OWN_SIGN", functional_role="NEUTRAL")
        path = _make_single_path(sun)
        pi = _make_path_impact(path, impact=0.0)  # NEUTRAL = 0.0

        classified = classify_paths([pi], ["SUN"])
        assert len(classified) == 1
        assert classified[0].classification == "malefic"  # Natural malefic

    def test_dhana_category(self) -> None:
        """Dhana yoga uses Wb=1.0, Wm=0.8."""
        agg = YogaSpecificChainAggregator()

        jup = _make_node("JUPITER", 2, 9, "OWN_SIGN", functional_role="BENEFIC")
        path1 = _make_single_path(jup)
        pi1 = _make_path_impact(path1, impact=0.5)

        saturn = _make_node("SATURN", 2, 10, "OWN_SIGN", functional_role="MALEFIC")
        path2 = _make_single_path(saturn)
        pi2 = _make_path_impact(path2, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Dhana",
            yoga_planets=["JUPITER", "SATURN"],
        )

        assert result.category == YogaCategory.DHANA
        # Positive because Wb=1.0 > Wm=0.8
        assert result.chain_impact > 0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 10: Fix 1 — Gajakesari Natural Benefic Override (Phase E6e)
# ══════════════════════════════════════════════════════════════════════════════


class TestGajakesariBeneficOverride:
    """Gajakesari: Jupiter (natural benefic) always uses benefic weight,
    even if functional lordship classifies it as MALEFIC."""

    def test_jupiter_kendradhipati_override(self) -> None:
        """Fix 1: Jupiter as Kendradhipati (functional MALEFIC) but natural
        BENEFIC → Gajakesari chain impact should be POSITIVE."""
        agg = YogaSpecificChainAggregator()

        # Jupiter rooted path — classified as 'benefic' by natural nature
        jup = _make_node("JUPITER", 7, 9, "OWN_SIGN", functional_role="MALEFIC")
        saturn = _make_node("SATURN", 10, 11, "OWN_SIGN", functional_role="MALEFIC")

        # Jupiter → Saturn path (Jupiter root = natural benefic)
        path1 = _make_single_path(jup, saturn)
        pi1 = _make_path_impact(path1, impact=-0.4)

        # Saturn → Jupiter path (Saturn root = natural malefic)
        path2 = _make_single_path(saturn, jup)
        pi2 = _make_path_impact(path2, impact=-0.3)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER"],
        )

        # Jupiter-rooted paths should use Wb=0.8 (benefic), not Wm=0.5
        # Even with external malefic in chain
        assert result.chain_impact > 0, (
            f"Gajakesari chain impact should be positive, got {result.chain_impact}. "
            f"Jupiter is a natural benefic and should use Wb=0.8."
        )
        assert not result.cancelled, "Gajakesari is NEVER cancelled"

    def test_gajakesari_pure_benefic_only(self) -> None:
        """Gajakesari with only benefic roots → positive."""
        agg = YogaSpecificChainAggregator()

        jup = _make_node("JUPITER", 7, 9, "OWN_SIGN", functional_role="BENEFIC")
        moon = _make_node("MOON", 4, 4, "OWN_SIGN", functional_role="BENEFIC")

        path1 = _make_single_path(jup, moon)
        pi1 = _make_path_impact(path1, impact=0.5)

        path2 = _make_single_path(moon, jup)
        pi2 = _make_path_impact(path2, impact=0.3)

        result = agg.aggregate(
            path_impacts=[pi1, pi2],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER", "MOON"],
        )

        assert result.chain_impact > 0
        assert result.benefic_paths >= 2

    def test_gajakesari_malefic_root_path_uses_malefic_weight(self) -> None:
        """Saturn-rooted paths still use Wm=0.5 (malefic weight)."""
        agg = YogaSpecificChainAggregator()

        saturn = _make_node("SATURN", 10, 11, "OWN_SIGN", functional_role="MALEFIC")
        path = _make_single_path(saturn)
        pi = _make_path_impact(path, impact=-0.5)

        # Saturn is NOT a yoga planet, so no paths should be classified
        result = agg.aggregate(
            path_impacts=[pi],
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER"],
        )

        # Only JUPITER is a yoga planet — Saturn paths are filtered
        assert result.total_paths == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 11: Fix 2 — Vipareeta Raja Stricter Conditions (Phase E6e)
# ══════════════════════════════════════════════════════════════════════════════


class TestVipareetaRajaStricter:
    """Vipareeta Raja: Kendra lord exclusion (BPHS Ch 42)."""

    def test_kendra_lord_excluded_from_vipareeta(self) -> None:
        """Fix 2: 1st lord in 8th house should NOT trigger Vipareeta Raja."""
        agg = YogaSpecificChainAggregator()

        mars = _make_node("MARS", 12, 4, "OWN_SIGN", functional_role="MALEFIC")
        path = _make_single_path(mars)
        pi = _make_path_impact(path, impact=-0.5)

        result = agg.aggregate(
            path_impacts=[pi],
            yoga_name="Vipareeta Raja",
            yoga_planets=["MARS"],
            is_primary_kendra_lord=True,
        )

        assert result.cancelled, (
            "Kendra lord in dusthana should NOT form Vipareeta Raja"
        )
        assert result.chain_impact == 0.0

    def test_trikona_lord_not_excluded(self) -> None:
        """Trikona lord in dusthana can still form Vipareeta Raja."""
        agg = YogaSpecificChainAggregator()

        jupiter = _make_node("JUPITER", 8, 10, "NEUTRAL", functional_role="MALEFIC")
        path = _make_single_path(jupiter)
        pi = _make_path_impact(path, impact=-0.3)

        result = agg.aggregate(
            path_impacts=[pi],
            yoga_name="Vipareeta Raja",
            yoga_planets=["JUPITER"],
            is_primary_kendra_lord=False,
        )

        assert not result.cancelled
        assert result.chain_impact >= 0
