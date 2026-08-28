"""JRS Graph — Cascading Strength & Propagation Engine (RI-011 Phase B).

Computes the net functional impact of multi-hop planetary chains using
the cascading strength propagation formula from BPHS. Each chain path
is evaluated by combining node dignity multipliers, retrograde/combust
modifiers, and edge weights with a 0.70 per-hop damping factor.

Source: Brihat Parashara Hora Shastra (BPHS) Chapters 33–34.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .chain_evaluator import (
    ChainEdge,
    ChainNode,
    ChainPath,
    DIGNITY_SCORES,
    DirectedChainEvaluator,
    Dignity,
    EdgeType,
    RelationshipGraph,
)
from .chain_evaluator import (
    COMBUST_MULTIPLIER,
    RETROGRADE_MULTIPLIER,
)
from .functional_lordship import FunctionalRole


# ── Constants ─────────────────────────────────────────────────────────────────

# Per-hop damping factor (BPHS Ch 34 cascading attenuation)
HOP_DAMPING: float = 0.70

# Functional role base weights (F_role)
_ROLE_WEIGHTS: dict[FunctionalRole, float] = {
    FunctionalRole.YOGAKARAKA: 1.50,
    FunctionalRole.BENEFIC: 1.00,
    FunctionalRole.NEUTRAL: 0.00,
    FunctionalRole.MALEFIC: -1.00,
}


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NodeMultiplier:
    """Immutable node multiplier result.

    Attributes:
        planet: Planet name.
        dignity_score: Dignity component of the multiplier.
        retrograde_multiplier: Retrograde component (1.20 if retro, else 1.00).
        combust_multiplier: Combust component (0.40 if combust, else 1.00).
        net_multiplier: Product of all three components.
    """

    planet: str
    dignity_score: float
    retrograde_multiplier: float
    combust_multiplier: float
    net_multiplier: float


@dataclass(frozen=True)
class PathImpact:
    """Immutable path impact result.

    Attributes:
        path: The original ChainPath.
        root_multiplier: NodeMultiplier for the root (N_0) node.
        hop_multipliers: Tuple of NodeMultiplier for each subsequent node.
        net_functional_impact: Final computed ΔI(P).
    """

    path: ChainPath
    root_multiplier: NodeMultiplier
    hop_multipliers: tuple[NodeMultiplier, ...]
    net_functional_impact: float


# ── Chain Strength Engine ─────────────────────────────────────────────────────

class ChainStrengthEngine:
    """Compute cascading strength for multi-hop planetary chains.

    Implements the path propagation formula:

    .. math::

        \\Delta I(P) = F_{role}(N_0) \\times M_{node}(N_0)
        \\times \\prod_{i=1}^{k} \\left( W_{edge}(E_i) \\times M_{node}(N_i)
        \\times 0.70 \\right)

    Where:

    - :math:`F_{role}(N_0)` is the functional role weight of the root node
      (``+1.50`` for YOGAKARAKA, ``+1.00`` for BENEFIC, ``0.00`` for NEUTRAL,
      ``-1.00`` for MALEFIC).
    - :math:`M_{node}(N_i) = S_{dignity} \\times M_{retro} \\times M_{combust}`
    - :math:`W_{edge}(E_i)` is the edge weight.
    - ``0.70`` is the per-hop damping factor.
    """

    def __init__(self) -> None:
        self._evaluator = DirectedChainEvaluator()

    def compute_node_multiplier(self, node: ChainNode) -> NodeMultiplier:
        """Compute the multiplier for a single chain node.

        Formula: M_node(N_i) = S_dignity × M_retro × M_combust

        Args:
            node: ChainNode to evaluate.

        Returns:
            Immutable ``NodeMultiplier`` with component scores.
        """
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

    def compute_path_impact(self, path: ChainPath) -> PathImpact:
        """Compute the net functional impact of a single chain path.

        Uses the cascading propagation formula:

        ΔI(P) = F_role(N_0) × M_node(N_0) × ∏_{i=1}^{k} (W_edge(E_i) × M_node(N_i) × 0.70)

        Args:
            path: ChainPath to evaluate.

        Returns:
            Immutable ``PathImpact`` with computed impact.
        """
        if not path.nodes:
            return PathImpact(
                path=path,
                root_multiplier=NodeMultiplier(
                    planet="", dignity_score=0.0, retrograde_multiplier=1.0,
                    combust_multiplier=1.0, net_multiplier=0.0,
                ),
                hop_multipliers=(),
                net_functional_impact=0.0,
            )

        root_node = path.nodes[0]
        root_mult = self.compute_node_multiplier(root_node)
        f_role = _ROLE_WEIGHTS.get(root_node.functional_role, 0.0)

        # Start with root: F_role(N_0) × M_node(N_0)
        impact = f_role * root_mult.net_multiplier

        # Multiply by each hop: W_edge(E_i) × M_node(N_i) × 0.70
        hop_mults: list[NodeMultiplier] = []
        for i, edge in enumerate(path.edges):
            if i + 1 < len(path.nodes):
                next_node = path.nodes[i + 1]
                next_mult = self.compute_node_multiplier(next_node)
                hop_mults.append(next_mult)
                impact *= edge.weight * next_mult.net_multiplier * HOP_DAMPING

        return PathImpact(
            path=path,
            root_multiplier=root_mult,
            hop_multipliers=tuple(hop_mults),
            net_functional_impact=impact,
        )

    def evaluate_all_paths(
        self,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> list[PathImpact]:
        """Evaluate all chain paths and compute their net functional impact.

        Args:
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            List of ``PathImpact`` objects sorted by absolute impact (descending).
        """
        paths = self._evaluator.evaluate(graph, jre_facts)
        impacts = [self.compute_path_impact(p) for p in paths]
        # Sort by absolute impact descending (strongest paths first)
        return sorted(impacts, key=lambda pi: abs(pi.net_functional_impact), reverse=True)

    def evaluate_from_planet(
        self,
        source_planet: str,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> list[PathImpact]:
        """Evaluate chain paths starting from a specific planet.

        Args:
            source_planet: Starting planet name.
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            List of ``PathImpact`` objects sorted by absolute impact (descending).
        """
        paths = self._evaluator.evaluate_from(source_planet, graph, jre_facts)
        impacts = [self.compute_path_impact(p) for p in paths]
        return sorted(impacts, key=lambda pi: abs(pi.net_functional_impact), reverse=True)

    def compute_aggregate_impact(
        self,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> float:
        """Compute aggregate functional impact across all chain paths.

        Uses the sum of all path impacts as the aggregate metric.

        Args:
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            Sum of all path net functional impacts.
        """
        impacts = self.evaluate_all_paths(graph, jre_facts)
        return sum(pi.net_functional_impact for pi in impacts)

    @staticmethod
    def evaluate_path_impact(path: ChainPath) -> float:
        """Evaluate the net functional impact of a single chain path.

        This is a convenience static method that creates a temporary engine
        instance and returns just the float impact value.

        Args:
            path: ChainPath to evaluate.

        Returns:
            Net functional impact as a float.
        """
        engine = ChainStrengthEngine()
        result = engine.compute_path_impact(path)
        return result.net_functional_impact

    def get_strongest_chain(
        self,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> PathImpact | None:
        """Return the single chain path with the highest absolute impact.

        Args:
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            ``PathImpact`` with the highest absolute impact, or ``None``
            if no paths exist.
        """
        impacts = self.evaluate_all_paths(graph, jre_facts)
        return impacts[0] if impacts else None
