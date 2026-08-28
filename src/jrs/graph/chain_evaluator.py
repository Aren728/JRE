"""JRS Graph — Directed Chain Evaluator (RI-011 Phase B).

Traverses multi-hop relational chains across planets using depth-bounded
Depth-First Search (DFS) with per-path loop suppression. Consumes existing
``PlanetRelationship`` objects from the structural layer to seed edges,
then discovers 1-hop, 2-hop, and 3-hop paths through the planetary graph.

Source: Brihat Parashara Hora Shastra (BPHS) Chapters 33–34.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional

from ..structural.models import PlanetRelationship, RelationshipType
from .functional_lordship import (
    FunctionalLordshipClassifier,
    FunctionalRole,
    LordshipProfile,
)


# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum traversal depth (k ≤ 3)
MAX_CHAIN_DEPTH: int = 3

# Standard Vimshottari sign ownership: 1-indexed rashi number → owning planet
_SIGN_LORDS: dict[int, str] = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

# Exaltation signs (1-indexed rashi number)
_EXALTATION: dict[str, int] = {
    "SUN": 1, "MOON": 2, "MARS": 10, "MERCURY": 6,
    "JUPITER": 4, "VENUS": 12, "SATURN": 7,
}

# Own signs (1-indexed rashi numbers)
_OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "SUN": (5,), "MOON": (4,), "MARS": (1, 8), "MERCURY": (3, 6),
    "JUPITER": (9, 12), "VENUS": (2, 7), "SATURN": (10, 11),
}

# Debilitation signs (1-indexed rashi number)
_DEBILITATION: dict[str, int] = {
    "SUN": 7, "MOON": 8, "MARS": 4, "MERCURY": 12,
    "JUPITER": 10, "VENUS": 6, "SATURN": 1,
}

# Friend/enemy mapping (simplified: classical relationship pairs)
_FRIENDS: dict[str, frozenset[str]] = {
    "SUN": frozenset({"MOON", "MARS", "JUPITER"}),
    "MOON": frozenset({"SUN", "MERCURY"}),
    "MARS": frozenset({"SUN", "MOON", "JUPITER"}),
    "MERCURY": frozenset({"SUN", "VENUS"}),
    "JUPITER": frozenset({"SUN", "MOON", "MARS"}),
    "VENUS": frozenset({"MERCURY", "SATURN"}),
    "SATURN": frozenset({"MERCURY", "VENUS"}),
}

_ENEMIES: dict[str, frozenset[str]] = {
    "SUN": frozenset({"VENUS", "SATURN", "RAHU", "KETU"}),
    "MOON": frozenset({"RAHU", "KETU"}),
    "MARS": frozenset({"MERCURY", "RAHU", "KETU"}),
    "MERCURY": frozenset({"MOON", "RAHU", "KETU"}),
    "JUPITER": frozenset({"MERCURY", "VENUS", "RAHU", "KETU"}),
    "VENUS": frozenset({"SUN", "MOON", "RAHU", "KETU"}),
    "SATURN": frozenset({"SUN", "MOON", "MARS", "RAHU", "KETU"}),
}


# ── Enums ─────────────────────────────────────────────────────────────────────

class EdgeType(StrEnum):
    """Types of directed relational edges between planets."""

    CONJUNCTION = "CONJUNCTION"
    MUTUAL_ASPECT = "MUTUAL_ASPECT"
    ONE_WAY_ASPECT = "ONE_WAY_ASPECT"
    DISPOSITOR = "DISPOSITOR"
    PARIVARTANA = "PARIVARTANA"


class Dignity(StrEnum):
    """Planetary dignity states (BPHS Ch 3)."""

    EXALTED = "EXALTED"
    OWN_SIGN = "OWN_SIGN"
    FRIEND_SIGN = "FRIEND_SIGN"
    ENEMY_SIGN = "ENEMY_SIGN"
    DEBILITATED = "DEBILITATED"


# ── Constants (after enum definitions) ────────────────────────────────────────

# Edge base weights per BPHS relational strength
EDGE_WEIGHTS: dict[EdgeType, float] = {
    EdgeType.CONJUNCTION: 1.00,
    EdgeType.PARIVARTANA: 0.90,
    EdgeType.MUTUAL_ASPECT: 0.85,
    EdgeType.ONE_WAY_ASPECT: 0.75,
    EdgeType.DISPOSITOR: 0.60,
}

# Dignity strength scores (BPHS Ch 3)
DIGNITY_SCORES: dict[Dignity, float] = {
    Dignity.EXALTED: 1.50,
    Dignity.OWN_SIGN: 1.25,
    Dignity.FRIEND_SIGN: 1.00,
    Dignity.ENEMY_SIGN: 0.75,
    Dignity.DEBILITATED: 0.50,
}

# Retrograde and combust multipliers
RETROGRADE_MULTIPLIER: float = 1.20
COMBUST_MULTIPLIER: float = 0.40

# Functional role weights for chain root node
_ROLE_WEIGHTS: dict[FunctionalRole, float] = {
    FunctionalRole.YOGAKARAKA: 1.50,
    FunctionalRole.BENEFIC: 1.00,
    FunctionalRole.NEUTRAL: 0.00,
    FunctionalRole.MALEFIC: -1.00,
}


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChainNode:
    """Immutable node in a relational chain.

    Attributes:
        planet: Planet name (e.g., ``"JUPITER"``).
        house: House number (1–12) relative to the Lagna.
        sign: Sign number (1–12) where the planet is placed.
        dignity: Dignity state of the planet.
        is_retrograde: Whether the planet is in retrograde motion.
        is_combust: Whether the planet is combust (too close to the Sun).
        functional_role: Functional lordship classification.
        base_weight: Functional role weight for chain propagation.
    """

    planet: str
    house: int
    sign: int
    dignity: Dignity
    is_retrograde: bool
    is_combust: bool
    functional_role: FunctionalRole
    base_weight: float


@dataclass(frozen=True)
class ChainEdge:
    """Immutable directed edge between two ChainNodes.

    Attributes:
        source: Source planet name.
        target: Target planet name.
        edge_type: Type of relational connection.
        weight: Base weight for this edge type.
    """

    source: str
    target: str
    edge_type: EdgeType
    weight: float


@dataclass(frozen=True)
class ChainPath:
    """Immutable path through the relational chain graph.

    Attributes:
        nodes: Ordered sequence of ChainNodes in the path.
        edges: Ordered sequence of ChainEdges connecting the nodes.
        length: Number of hops (edges) in the path.
        net_functional_impact: Computed net functional impact of this path
            (initially 0.0; computed by ChainStrengthEngine).
    """

    nodes: tuple[ChainNode, ...]
    edges: tuple[ChainEdge, ...]
    length: int
    net_functional_impact: float = 0.0


# ── Graph Wrapper ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RelationshipGraph:
    """Lightweight wrapper over a list of PlanetRelationship edges.

    Consumes existing ``PlanetRelationship`` objects from the structural
    layer and provides convenient accessors for the chain evaluator.
    """

    relationships: tuple[PlanetRelationship, ...] = ()

    def edges_for(self, planet: str) -> list[PlanetRelationship]:
        """Return all relationships where *planet* is source or target."""
        return [
            r for r in self.relationships
            if r.planet_a == planet or r.planet_b == planet
        ]

    def neighbors(self, planet: str) -> list[str]:
        """Return unique neighbor planet names for *planet*."""
        neighbors: set[str] = set()
        for r in self.relationships:
            if r.planet_a == planet:
                neighbors.add(r.planet_b)
            elif r.planet_b == planet:
                neighbors.add(r.planet_a)
        return sorted(neighbors)


# ── Chain Evaluator ───────────────────────────────────────────────────────────

class DirectedChainEvaluator:
    """Depth-bounded DFS evaluator for multi-hop planetary chains.

    Traverses the relational graph starting from each planet, discovering
    paths up to ``max_depth`` hops with per-path loop suppression (no
    planet visited twice in a single path).

    Args:
        max_depth: Maximum chain depth in hops (default: 3).
    """

    def __init__(self, max_depth: int = MAX_CHAIN_DEPTH) -> None:
        self._max_depth = max_depth
        self._lordship_classifier = FunctionalLordshipClassifier()

    # ── Public API ────────────────────────────────────────────────────────

    def evaluate(
        self,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> list[ChainPath]:
        """Discover all chain paths up to ``max_depth`` hops.

        Args:
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data. Expected keys:
                ``planets`` (dict of planet → data), ``lagna_sign`` (int 1–12).

        Returns:
            List of ``ChainPath`` objects for all discovered paths.
        """
        planets = jre_facts.get("planets", {})
        lagna_sign = jre_facts.get("lagna_sign", 1)

        if not planets:
            return []

        # Build ChainNode for each planet
        node_map: dict[str, ChainNode] = {}
        for pname, pdata in planets.items():
            node_map[pname] = self._build_node(pname, pdata, lagna_sign)

        # Discover all paths via DFS from each planet
        all_paths: list[ChainPath] = []
        for pname in sorted(node_map.keys()):
            self._dfs(
                current=pname,
                nodes=[node_map[pname]],
                edges=[],
                visited=frozenset({pname}),
                graph=graph,
                node_map=node_map,
                depth=0,
                paths=all_paths,
            )

        return all_paths

    def evaluate_from(
        self,
        source_planet: str,
        graph: RelationshipGraph,
        jre_facts: dict[str, Any],
    ) -> list[ChainPath]:
        """Discover chain paths starting from a specific planet.

        Args:
            source_planet: Starting planet name.
            graph: ``RelationshipGraph`` containing planetary relationships.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            List of ``ChainPath`` objects originating from *source_planet*.
        """
        planets = jre_facts.get("planets", {})
        lagna_sign = jre_facts.get("lagna_sign", 1)

        if not planets or source_planet not in planets:
            return []

        node_map: dict[str, ChainNode] = {}
        for pname, pdata in planets.items():
            node_map[pname] = self._build_node(pname, pdata, lagna_sign)

        all_paths: list[ChainPath] = []
        self._dfs(
            current=source_planet,
            nodes=[node_map[source_planet]],
            edges=[],
            visited=frozenset({source_planet}),
            graph=graph,
            node_map=node_map,
            depth=0,
            paths=all_paths,
        )

        return all_paths

    # ── DFS Traversal ─────────────────────────────────────────────────────

    def _dfs(
        self,
        current: str,
        nodes: list[ChainNode],
        edges: list[ChainEdge],
        visited: frozenset[str],
        graph: RelationshipGraph,
        node_map: dict[str, ChainNode],
        depth: int,
        paths: list[ChainPath],
    ) -> None:
        """Recursive depth-first search with loop suppression.

        Args:
            current: Current planet name.
            nodes: Accumulated nodes in the current path.
            edges: Accumulated edges in the current path.
            visited: Set of planets already visited in this path.
            graph: The relationship graph.
            node_map: Planet → ChainNode mapping.
            depth: Current depth (0-indexed).
            paths: Accumulator for discovered paths.
        """
        # Record the current path (non-zero length)
        if edges:
            path = ChainPath(
                nodes=tuple(nodes),
                edges=tuple(edges),
                length=len(edges),
            )
            paths.append(path)

        # Stop if max depth reached
        if depth >= self._max_depth:
            return

        # Explore neighbors
        for rel in graph.edges_for(current):
            # Determine target planet
            target = rel.planet_b if rel.planet_a == current else rel.planet_a

            # Loop suppression: skip already-visited planets
            if target in visited:
                continue

            # Skip if target not in node_map
            if target not in node_map:
                continue

            # Map relationship type to chain edge type
            edge_type = self._map_edge_type(rel, current)
            if edge_type is None:
                continue

            edge = ChainEdge(
                source=current,
                target=target,
                edge_type=edge_type,
                weight=EDGE_WEIGHTS[edge_type],
            )

            self._dfs(
                current=target,
                nodes=[*nodes, node_map[target]],
                edges=[*edges, edge],
                visited=visited | {target},
                graph=graph,
                node_map=node_map,
                depth=depth + 1,
                paths=paths,
            )

    # ── Edge Type Mapping ─────────────────────────────────────────────────

    @staticmethod
    def _map_edge_type(
        rel: PlanetRelationship,
        current_planet: str,
    ) -> Optional[EdgeType]:
        """Map a PlanetRelationship to a ChainEdge edge type.

        Args:
            rel: The source PlanetRelationship.
            current_planet: The current traversal planet (for directionality).

        Returns:
            Mapped EdgeType, or None if the relationship should be skipped
            (e.g., transit relationships or node-only connections).
        """
        # Skip transit relationships (not natal)
        if rel.relationship_type in (
            RelationshipType.TRANSIT_ASPECT,
            RelationshipType.TRANSIT_CONJUNCTION,
        ):
            return None

        if rel.relationship_type == RelationshipType.CONJUNCTION:
            return EdgeType.CONJUNCTION

        if rel.relationship_type == RelationshipType.EXCHANGE:
            return EdgeType.PARIVARTANA

        if rel.relationship_type == RelationshipType.DISPOSITOR:
            return EdgeType.DISPOSITOR

        if rel.relationship_type == RelationshipType.ASPECT:
            # Determine if mutual or one-way
            # is_directed=True means A aspects B (but B may not aspect A back)
            if rel.is_directed:
                return EdgeType.ONE_WAY_ASPECT
            return EdgeType.MUTUAL_ASPECT

        return None

    # ── Node Building ─────────────────────────────────────────────────────

    def _build_node(
        self,
        planet: str,
        pdata: dict[str, Any],
        lagna_sign: int,
    ) -> ChainNode:
        """Build a ChainNode from JRE planet data.

        Args:
            planet: Planet name.
            pdata: Planet data dictionary from JRE facts.
            lagna_sign: Lagna sign number (1–12).

        Returns:
            ChainNode with computed dignity, role, and weight.
        """
        # Extract basic data
        house = pdata.get("house", 0)
        sign_num = pdata.get("rashi_num", pdata.get("sign_num", 0))
        is_retrograde = pdata.get("retrograde", False)
        is_combust = pdata.get("combust", False)

        # Compute dignity
        dignity = self._compute_dignity(planet, sign_num)

        # Classify functional role
        profile = self._lordship_classifier.classify(planet, lagna_sign)

        return ChainNode(
            planet=planet,
            house=house,
            sign=sign_num,
            dignity=dignity,
            is_retrograde=is_retrograde,
            is_combust=is_combust,
            functional_role=profile.functional_role,
            base_weight=profile.base_weight,
        )

    @staticmethod
    def _compute_dignity(planet: str, sign_num: int) -> Dignity:
        """Compute planetary dignity from sign placement.

        Args:
            planet: Planet name.
            sign_num: Sign number (1–12) where the planet is placed.

        Returns:
            Dignity enum value.
        """
        if sign_num <= 0:
            return Dignity.FRIEND_SIGN  # Default for unknown sign

        exalt_sign = _EXALTATION.get(planet)
        if exalt_sign is not None and sign_num == exalt_sign:
            return Dignity.EXALTED

        deb_sign = _DEBILITATION.get(planet)
        if deb_sign is not None and sign_num == deb_sign:
            return Dignity.DEBILITATED

        own_signs = _OWN_SIGNS.get(planet, ())
        if sign_num in own_signs:
            return Dignity.OWN_SIGN

        # Check friend/enemy via sign lord
        sign_lord = _SIGN_LORDS.get(sign_num)
        if sign_lord is not None:
            if sign_lord in _FRIENDS.get(planet, frozenset()):
                return Dignity.FRIEND_SIGN
            if sign_lord in _ENEMIES.get(planet, frozenset()):
                return Dignity.ENEMY_SIGN

        return Dignity.FRIEND_SIGN  # Default neutral-positive
