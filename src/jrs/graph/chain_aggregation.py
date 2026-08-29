"""JRS Graph — Yoga-Specific Chain Aggregation Engine (RI-013 Phase E6c).

Replaces the undifferentiated chain aggregation with category-specific models
that correctly handle benefic/malefic influences according to classical rules.

The core problem (Phase E6a): the old ``ChainStrengthEngine.compute_aggregate_impact``
sums all path impacts where sign = F_role(N₀) (functional lordship). In charts where
4+ planets are classified MALEFIC, the aggregate is guaranteed negative regardless
of which yoga is evaluated.

The fix: each yoga category has its own aggregation formula with:
- Category-specific benefic/malefic weights
- Relevance filtering (only yoga-participating planets)
- Immunity conditions (own sign, exaltation)
- Cancellation thresholds

Source: RI-013 — Yoga-Specific Chain Aggregation Rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .chain_evaluator import (
    ChainNode,
    ChainPath,
    Dignity,
    EdgeType,
)
from .chain_strength import (
    ChainStrengthEngine,
    HOP_DAMPING,
    NAKSHATRA_EDGE_ATTENUATION,
    NodeMultiplier,
    PathImpact,
)

# ── Natural Benefic/Malefic Classification (BPHS Ch 2) ──────────────────────

NATURAL_BENEFICS: frozenset[str] = frozenset(
    {"JUPITER", "VENUS", "MOON", "MERCURY"}
)
NATURAL_MALEFICS: frozenset[str] = frozenset(
    {"SUN", "MARS", "SATURN", "RAHU", "KETU"}
)


# ── Yoga Category Enum ───────────────────────────────────────────────────────

class YogaCategory(StrEnum):
    """Yoga categories with distinct chain aggregation models."""

    GAJAKESARI = "GAJAKESARI"
    BUDHADITYA = "BUDHADITYA"
    PANCHA_MAHAPURUSHA = "PANCHA_MAHAPURUSHA"
    RAJA = "RAJA"
    VIPAREETA_RAJA = "VIPAREETA_RAJA"
    KEMADRUMA = "KEMADRUMA"
    CHANDRA = "CHANDRA"
    DHANA = "DHANA"
    DEFAULT = "DEFAULT"


# ── Category Weights ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CategoryWeights:
    """Aggregation weights for a yoga category.

    Attributes:
        w_benefic: Weight for paths rooted in natural benefics.
        w_malefic: Weight for paths rooted in natural malefics.
        never_cancelled: If True, this yoga cannot be fully cancelled by chains.
        malefic_cancels: If True, ANY malefic aspect → complete cancellation.
        immunity_own_sign: If True, own-sign provides cancellation immunity.
    """

    w_benefic: float = 1.0
    w_malefic: float = 0.7
    never_cancelled: bool = False
    malefic_cancels: bool = False
    immunity_own_sign: bool = False


CATEGORY_WEIGHTS: dict[YogaCategory, CategoryWeights] = {
    YogaCategory.GAJAKESARI: CategoryWeights(
        w_benefic=0.8, w_malefic=0.5, never_cancelled=True,
    ),
    YogaCategory.BUDHADITYA: CategoryWeights(
        w_benefic=1.0, w_malefic=999.0, malefic_cancels=True,
        immunity_own_sign=True,
    ),
    YogaCategory.PANCHA_MAHAPURUSHA: CategoryWeights(
        w_benefic=0.0, w_malefic=0.3, immunity_own_sign=True,
    ),
    YogaCategory.RAJA: CategoryWeights(
        w_benefic=1.0, w_malefic=0.7,
    ),
    YogaCategory.VIPAREETA_RAJA: CategoryWeights(
        w_benefic=0.0, w_malefic=0.3, never_cancelled=True,
    ),
    YogaCategory.KEMADRUMA: CategoryWeights(
        w_benefic=1.0, w_malefic=0.0, never_cancelled=True,
    ),
    YogaCategory.CHANDRA: CategoryWeights(
        w_benefic=0.6, w_malefic=0.8,
    ),
    YogaCategory.DHANA: CategoryWeights(
        w_benefic=1.0, w_malefic=0.8,
    ),
    YogaCategory.DEFAULT: CategoryWeights(
        w_benefic=1.0, w_malefic=0.7,
    ),
}


# ── Yoga Name → Category Mapping ─────────────────────────────────────────────

_YOGA_CATEGORY_MAP: dict[str, YogaCategory] = {
    "GAJAKESARI": YogaCategory.GAJAKESARI,
    "BUDHADITYA": YogaCategory.BUDHADITYA,
    "RUCHAKA": YogaCategory.PANCHA_MAHAPURUSHA,
    "BHADRA": YogaCategory.PANCHA_MAHAPURUSHA,
    "HAMSA": YogaCategory.PANCHA_MAHAPURUSHA,
    "MALAVYA": YogaCategory.PANCHA_MAHAPURUSHA,
    "SASA": YogaCategory.PANCHA_MAHAPURUSHA,
    # Compound names (used in test matrix and engine)
    "PANCHA MAHAPURUSHA MALAVYA": YogaCategory.PANCHA_MAHAPURUSHA,
    "PANCHA MAHAPURUSHA RUCHAKA": YogaCategory.PANCHA_MAHAPURUSHA,
    "PANCHA MAHAPURUSHA BHADRA": YogaCategory.PANCHA_MAHAPURUSHA,
    "PANCHA MAHAPURUSHA HAMSA": YogaCategory.PANCHA_MAHAPURUSHA,
    "PANCHA MAHAPURUSHA SASA": YogaCategory.PANCHA_MAHAPURUSHA,
    "PANCHA MAHAPURUSHA": YogaCategory.PANCHA_MAHAPURUSHA,
    "RAJA": YogaCategory.RAJA,
    "VIPAREETA RAJA": YogaCategory.VIPAREETA_RAJA,
    "KEMADRUMA": YogaCategory.KEMADRUMA,
    "SUNAPHA": YogaCategory.CHANDRA,
    "ANAPHA": YogaCategory.CHANDRA,
    "DHUDHARA": YogaCategory.CHANDRA,
    "DHANA": YogaCategory.DHANA,
    "NEECHA BHANGA": YogaCategory.DEFAULT,
}


def get_yoga_category(yoga_name: str) -> YogaCategory:
    """Map a yoga name to its aggregation category.

    Args:
        yoga_name: Name of the yoga (e.g., "Gajakesari", "Malavya").

    Returns:
        The YogaCategory for chain aggregation.
    """
    key = yoga_name.upper().replace("_", " ").strip()
    # Direct match
    if key in _YOGA_CATEGORY_MAP:
        return _YOGA_CATEGORY_MAP[key]
    # Substring match (e.g., "Pancha Mahapurusha Malavya" → "Pancha Mahapurusha")
    for map_key, cat in _YOGA_CATEGORY_MAP.items():
        if map_key in key:
            return cat
    return YogaCategory.DEFAULT


# ── Path Magnitude Recomputation ─────────────────────────────────────────────

def _compute_node_multiplier(node: ChainNode) -> NodeMultiplier:
    """Compute the node multiplier (dignity × retro × combust).

    This recomputes the multiplier without the functional role sign,
    so we can apply category-specific weights separately.
    """
    from .chain_evaluator import DIGNITY_SCORES, COMBUST_MULTIPLIER, RETROGRADE_MULTIPLIER

    dignity_score = DIGNITY_SCORES.get(node.dignity, 1.00)
    retro_mult = RETROGRADE_MULTIPLIER if node.is_retrograde else 1.00
    combust_mult = COMBUST_MULTIPLIER if node.is_combust else 1.00
    net = dignity_score * retro_mult * combust_mult

    return NodeMultiplier(
        planet=node.planet,
        dignity_score=dignity_score,
        retrograde_multiplier=retro_mult,
        combust_multiplier=combust_mult,
        net_multiplier=net,
    )


def _compute_path_magnitude(path: ChainPath) -> float:
    """Compute the absolute magnitude of a chain path.

    This is the path impact WITHOUT the F_role(N₀) sign.
    It represents the raw structural strength of the chain.

    Formula: |ΔI(P)| = M_node(N₀) × ∏_{i=1}^{k} (W_edge(E_i) × M_node(N_i) × 0.70)
    """
    if not path.nodes:
        return 0.0

    root_mult = _compute_node_multiplier(path.nodes[0])
    magnitude = root_mult.net_multiplier

    for i, edge in enumerate(path.edges):
        if i + 1 < len(path.nodes):
            next_mult = _compute_node_multiplier(path.nodes[i + 1])
            nak_att = NAKSHATRA_EDGE_ATTENUATION.get(edge.edge_type, 1.00)
            magnitude *= edge.weight * next_mult.net_multiplier * HOP_DAMPING * nak_att

    return abs(magnitude)


# ── Path Classification ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ClassifiedPath:
    """A chain path classified as benefic/malefic/neutral by natural nature."""

    path_impact: PathImpact
    magnitude: float
    classification: str  # "benefic", "malefic", "neutral"
    involves_malefic: bool = False  # True if ANY node in path is malefic


def classify_paths(
    path_impacts: list[PathImpact],
    yoga_planets: list[str],
    require_yoga_root: bool = True,
) -> list[ClassifiedPath]:
    """Classify chain paths by natural benefic/malefic nature.

    By default, only paths rooted in yoga-participating planets are included.
    Set require_yoga_root=False to include all paths (for models that need
    the full chain magnitude, like Pancha Mahapurusha).

    Classification is based on the root node's NATURAL nature (BPHS Ch 2),
    not its functional lordship.

    Args:
        path_impacts: Pre-computed PathImpact objects from ChainStrengthEngine.
        yoga_planets: Planet names involved in the yoga.
        require_yoga_root: If True (default), only include paths rooted in
            yoga planets. If False, include all paths.

    Returns:
        List of ClassifiedPath objects for yoga-relevant paths.
    """
    yoga_set = frozenset(p.upper() for p in yoga_planets) if yoga_planets else frozenset()

    classified: list[ClassifiedPath] = []
    for pi in path_impacts:
        if not pi.path.nodes:
            continue

        root_planet = pi.path.nodes[0].planet.upper()

        # Relevance filter
        if require_yoga_root and root_planet not in yoga_set:
            continue

        # Natural classification (BPHS Ch 2)
        if root_planet in NATURAL_BENEFICS:
            cls = "benefic"
        elif root_planet in NATURAL_MALEFICS:
            cls = "malefic"
        else:
            cls = "neutral"

        magnitude = _compute_path_magnitude(pi.path)

        # Check if ANY node in the path involves a malefic planet
        involves_malefic = any(
            node.planet.upper() in NATURAL_MALEFICS for node in pi.path.nodes
        )

        classified.append(ClassifiedPath(
            path_impact=pi,
            magnitude=magnitude,
            classification=cls,
            involves_malefic=involves_malefic,
        ))

    return classified


# ── Main Aggregator ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AggregationResult:
    """Result of yoga-specific chain aggregation.

    Attributes:
        chain_impact: Net chain impact value (positive = benefic reinforcement).
        category: The yoga category used for aggregation.
        benefic_sum: Sum of weighted benefic path magnitudes.
        malefic_sum: Sum of weighted malefic path magnitudes.
        total_paths: Total number of paths evaluated.
        benefic_paths: Number of benefic-rooted paths.
        malefic_paths: Number of malefic-rooted paths.
        cancelled: Whether the yoga is cancelled by chain aggregation.
        cancellation_reason: Reason for cancellation, if any.
    """

    chain_impact: float
    category: YogaCategory
    benefic_sum: float = 0.0
    malefic_sum: float = 0.0
    total_paths: int = 0
    benefic_paths: int = 0
    malefic_paths: int = 0
    cancelled: bool = False
    cancellation_reason: str | None = None


class YogaSpecificChainAggregator:
    """Yoga-specific chain aggregation engine (RI-013).

    Replaces the undifferentiated ``ChainStrengthEngine.compute_aggregate_impact``
    with category-specific models that correctly handle benefic/malefic influences.

    Usage::

        aggregator = YogaSpecificChainAggregator()
        result = aggregator.aggregate(
            path_impacts=chain_strength_engine.evaluate_all_paths(graph, jre_facts),
            yoga_name="Gajakesari",
            yoga_planets=["JUPITER", "MOON"],
        )
        print(result.chain_impact)  # Positive for Gajakesari
    """

    def aggregate(
        self,
        path_impacts: list[PathImpact],
        yoga_name: str,
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Aggregate chain impacts using yoga-specific model.

        Args:
            path_impacts: Pre-computed PathImpact objects from ChainStrengthEngine.
            yoga_name: Name of the yoga being evaluated.
            yoga_planets: Planet names involved in the yoga.
            **kwargs: Category-specific parameters (e.g., is_primary_kendra_lord,
                      has_benefic_near_moon, planet_in_own_sign).

        Returns:
            AggregationResult with category-specific chain impact.
        """
        category = get_yoga_category(yoga_name)

        # Dispatch to category-specific method
        if category == YogaCategory.VIPAREETA_RAJA:
            return self._aggregate_vipareeta_raja(
                path_impacts, yoga_planets, **kwargs,
            )
        if category == YogaCategory.KEMADRUMA:
            return self._aggregate_kemadruma(
                path_impacts, yoga_planets, **kwargs,
            )
        if category == YogaCategory.PANCHA_MAHAPURUSHA:
            # Pancha Mahapurusha: filter to yoga-rooted paths, then check
            # for external malefics in the chain.
            classified = classify_paths(path_impacts, yoga_planets)
            return self._aggregate_pancha_mahapurusha_from_classified(
                classified, yoga_planets, **kwargs,
            )
        if category == YogaCategory.BUDHADITYA:
            return self._aggregate_budhaditya(
                path_impacts, yoga_planets, **kwargs,
            )

        # Default: weighted sum model (Gajakesari, Raja, Chandra, Dhana, etc.)
        return self._aggregate_weighted(path_impacts, yoga_name, yoga_planets, **kwargs)

    # ── Weighted Sum Model (Gajakesari, Raja, Chandra, Dhana) ───────────

    def _aggregate_weighted(
        self,
        path_impacts: list[PathImpact],
        yoga_name: str,
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Weighted sum model: net = Σ(benefic × Wb) − Σ(malefic × Wm).

        For paths rooted in benefics: if the chain contains an external malefic
        (non-root), the malefic weight applies to that portion.
        For paths rooted in malefics: the malefic weight applies fully.
        """
        category = get_yoga_category(yoga_name)
        weights = CATEGORY_WEIGHTS[category]
        yoga_set = frozenset(p.upper() for p in yoga_planets) if yoga_planets else frozenset()

        classified = classify_paths(path_impacts, yoga_planets)

        benefic_sum = 0.0
        malefic_sum = 0.0
        benefic_count = 0
        malefic_count = 0

        for cp in classified:
            root_planet = (
                cp.path_impact.path.nodes[0].planet.upper()
                if cp.path_impact.path.nodes else ""
            )

            if cp.classification == "benefic":
                # Check if chain contains external malefic (non-root, non-yoga planet)
                has_external_malefic = any(
                    node.planet.upper() in NATURAL_MALEFICS
                    and node.planet.upper() != root_planet
                    and node.planet.upper() not in yoga_set
                    for node in cp.path_impact.path.nodes
                )
                if has_external_malefic and weights.w_malefic > 0:
                    # Chain has malefic influence — apply malefic weight
                    malefic_sum += cp.magnitude * weights.w_malefic
                    malefic_count += 1
                else:
                    benefic_sum += cp.magnitude * weights.w_benefic
                    benefic_count += 1
            elif cp.classification == "malefic":
                malefic_sum += cp.magnitude * weights.w_malefic
                malefic_count += 1

        chain_impact = benefic_sum - malefic_sum

        # Check cancellation (only for categories that can be cancelled)
        cancelled = False
        cancellation_reason = None
        if weights.malefic_cancels and malefic_count > 0:
            # Budhaditya: ANY external malefic aspect → cancellation
            immunity = kwargs.get("mercury_own_sign", False)
            if not immunity:
                cancelled = True
                cancellation_reason = (
                    f"Malefic aspect detected ({malefic_count} malefic paths) — "
                    f"{yoga_name} cancelled per BPHS"
                )
            else:
                malefic_sum *= 0.5
                chain_impact = benefic_sum - malefic_sum

        return AggregationResult(
            chain_impact=round(chain_impact, 6),
            category=category,
            benefic_sum=round(benefic_sum, 6),
            malefic_sum=round(malefic_sum, 6),
            total_paths=len(classified),
            benefic_paths=benefic_count,
            malefic_paths=malefic_count,
            cancelled=cancelled,
            cancellation_reason=cancellation_reason,
        )

    # ── Pancha Mahapurusha Model ────────────────────────────────────────

    def _aggregate_pancha_mahapurusha_from_classified(
        self,
        classified: list[ClassifiedPath],
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Pancha Mahapurusha model: net = formation × (1 − 0.3 × malefic_count).

        Uses ALL paths (not just yoga-rooted) for magnitude calculation.
        If planet_in_own_sign → immune to cancellation.
        """
        planet_in_own_sign = kwargs.get("planet_in_own_sign", False)

        malefic_count = 0
        total_magnitude = 0.0

        for cp in classified:
            total_magnitude += cp.magnitude
            if cp.classification == "malefic":
                malefic_count += 1

        # Base formation score from total chain magnitude
        formation = min(1.0, total_magnitude) if total_magnitude > 0 else 0.5

        # Apply malefic reduction
        if planet_in_own_sign:
            # Immunity: malefics reduce by only 20% instead of 30%
            reduction = 0.2 * malefic_count
        else:
            reduction = 0.3 * malefic_count

        chain_impact = formation * (1.0 - reduction)

        # Clamp to [0, 1]
        chain_impact = max(0.0, min(1.0, chain_impact))

        cancelled = False
        cancellation_reason = None
        if not planet_in_own_sign and chain_impact <= 0.0:
            cancelled = True
            cancellation_reason = (
                f"Malefic aspects ({malefic_count}) exceed formation strength — "
                f"Pancha Mahapurusha weakened"
            )

        return AggregationResult(
            chain_impact=round(chain_impact, 6),
            category=YogaCategory.PANCHA_MAHAPURUSHA,
            benefic_sum=round(sum(cp.magnitude for cp in classified if cp.classification == "benefic"), 6),
            malefic_sum=round(sum(cp.magnitude for cp in classified if cp.classification == "malefic"), 6),
            total_paths=len(classified),
            benefic_paths=sum(1 for cp in classified if cp.classification == "benefic"),
            malefic_paths=malefic_count,
            cancelled=cancelled,
            cancellation_reason=cancellation_reason,
        )

    # ── Budhaditya Model ────────────────────────────────────────────────

    def _aggregate_budhaditya(
        self,
        path_impacts: list[PathImpact],
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Budhaditya model: ANY external malefic aspect → complete cancellation.

        Immunity: Mercury in own sign → malefics reduce by 50% instead.
        Note: SUN is part of the yoga (Sun-Mercury conjunction) and is NOT
        counted as a malefic aspect — only external malefics trigger cancellation.
        """
        weights = CATEGORY_WEIGHTS[YogaCategory.BUDHADITYA]
        classified = classify_paths(path_impacts, yoga_planets)

        mercury_own_sign = kwargs.get("mercury_own_sign", False)
        yoga_set = frozenset(p.upper() for p in yoga_planets)

        benefic_sum = 0.0
        malefic_sum = 0.0
        external_malefic_count = 0

        for cp in classified:
            root_planet = cp.path_impact.path.nodes[0].planet.upper() if cp.path_impact.path.nodes else ""
            is_yoga_root = root_planet in yoga_set

            # Check for external malefic (non-root node is malefic)
            has_external_malefic = any(
                node.planet.upper() in NATURAL_MALEFICS and node.planet.upper() != root_planet
                for node in cp.path_impact.path.nodes
            )

            if has_external_malefic:
                external_malefic_count += 1
                if mercury_own_sign:
                    # Immunity: reduce malefic weight by 50%
                    malefic_sum += cp.magnitude * 0.5
                else:
                    malefic_sum += cp.magnitude * 999.0  # effectively infinite
            else:
                # No external malefic — count as benefic contribution
                benefic_sum += cp.magnitude * weights.w_benefic

        chain_impact = benefic_sum - malefic_sum

        # Check for external malefic involvement in ANY path
        # A malefic is "external" if it's NOT the root yoga planet
        external_malefic_paths = 0
        for cp in classified:
            if not cp.involves_malefic:
                continue
            root = cp.path_impact.path.nodes[0].planet.upper() if cp.path_impact.path.nodes else ""
            # Check if any NON-ROOT node is a malefic
            has_external_malefic = any(
                node.planet.upper() in NATURAL_MALEFICS and node.planet.upper() != root
                for node in cp.path_impact.path.nodes
            )
            if has_external_malefic:
                external_malefic_paths += 1

        cancelled = False
        cancellation_reason = None
        if not mercury_own_sign and external_malefic_paths > 0:
            cancelled = True
            cancellation_reason = (
                f"External malefic aspect detected ({external_malefic_paths} paths) — "
                f"Budhaditya cancelled per BPHS Ch 12"
            )
        elif mercury_own_sign and external_malefic_paths > 0:
            chain_impact = max(0.0, benefic_sum - malefic_sum)

        return AggregationResult(
            chain_impact=round(max(0.0, chain_impact) if not cancelled else 0.0, 6),
            category=YogaCategory.BUDHADITYA,
            benefic_sum=round(benefic_sum, 6),
            malefic_sum=round(malefic_sum, 6),
            total_paths=len(classified),
            benefic_paths=sum(1 for cp in classified if cp.classification == "benefic"),
            malefic_paths=external_malefic_count,
            cancelled=cancelled,
            cancellation_reason=cancellation_reason,
        )

    # ── Vipareeta Raja Model ────────────────────────────────────────────

    def _aggregate_vipareeta_raja(
        self,
        path_impacts: list[PathImpact],
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Vipareeta Raja model: primary dusthana lordship required.

        If is_primary_kendra_lord → return 0.0 (cannot trigger Vipareeta).
        Never fully cancelled — only weakened by malefic aspects.
        """
        is_primary_kendra_lord = kwargs.get("is_primary_kendra_lord", False)

        if is_primary_kendra_lord:
            return AggregationResult(
                chain_impact=0.0,
                category=YogaCategory.VIPAREETA_RAJA,
                cancelled=True,
                cancellation_reason=(
                    "Planet is primarily a Kendra lord — Vipareeta Raja requires "
                    "primary dusthana lordship (BPHS Ch 42)"
                ),
            )

        classified = classify_paths(path_impacts, yoga_planets)

        malefic_count = sum(1 for cp in classified if cp.classification == "malefic")
        total_magnitude = sum(cp.magnitude for cp in classified)

        # Vipareeta Raja: base strength reduced by malefic aspects
        base = min(1.0, total_magnitude) if total_magnitude > 0 else 0.5
        chain_impact = base * (1.0 - 0.3 * malefic_count)
        chain_impact = max(0.0, chain_impact)

        return AggregationResult(
            chain_impact=round(chain_impact, 6),
            category=YogaCategory.VIPAREETA_RAJA,
            total_paths=len(classified),
            benefic_paths=sum(1 for cp in classified if cp.classification == "benefic"),
            malefic_paths=malefic_count,
        )

    # ── Kemadruma Model ─────────────────────────────────────────────────

    def _aggregate_kemadruma(
        self,
        path_impacts: list[PathImpact],
        yoga_planets: list[str],
        **kwargs: Any,
    ) -> AggregationResult:
        """Kemadruma model: dosha = base × (1 − normalized_benefic).

        If has_benefic_in_2nd_or_12th → dosha cancelled (return 0.0).
        Malefic chains are irrelevant — only benefics reduce dosha.
        """
        has_benefic_near_moon = kwargs.get("has_benefic_near_moon", False)

        if has_benefic_near_moon:
            return AggregationResult(
                chain_impact=0.0,
                category=YogaCategory.KEMADRUMA,
                cancelled=True,
                cancellation_reason=(
                    "Benefic in 2nd/12th from Moon — Kemadruma cancelled per BPHS Ch 11"
                ),
            )

        classified = classify_paths(path_impacts, yoga_planets)

        benefic_count = sum(1 for cp in classified if cp.classification == "benefic")

        # Dosha reduction: each benefic path reduces dosha by 0.3
        # 0 benefic paths → dosha = 1.0 (full isolation)
        # 1 benefic path  → dosha = 0.7
        # 2 benefic paths → dosha = 0.4
        # 3+ benefic paths → dosha ≈ 0 (cancelled)
        dosha_reduction = 0.3 * benefic_count
        chain_impact = max(0.0, min(1.0, 1.0 - dosha_reduction))

        return AggregationResult(
            chain_impact=round(chain_impact, 6),
            category=YogaCategory.KEMADRUMA,
            benefic_sum=round(float(benefic_count), 6),
            total_paths=len(classified),
            benefic_paths=benefic_count,
        )
