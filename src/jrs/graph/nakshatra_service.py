"""JRS Graph — Nakshatra Relationship Service (RI-012 Phase D).

Detects Nakshatra-based planetary relationships:
- NAKSHATRA_PARIVARTANA: Mutual Nakshatra lord exchange (A in B's Nakshatra, B in A's).
- NAKSHATRA_LORD: One-directional Nakshatra dependency (A in Nakshatra ruled by B).

Uses the classical Vimshottari Nakshatra lord cycle (BPHS Ch 46):
    Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
    (repeated 3× over 27 Nakshatras).

Source: Brihat Parashara Hora Shastra (BPHS) Chapter 46.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── Constants ─────────────────────────────────────────────────────────────────

# Vimshottari Nakshatra lord cycle (9 rulers, repeated 3× over 27 Nakshatras)
_NAKSHATRA_LORD_CYCLE: tuple[str, ...] = (
    "KETU", "VENUS", "SUN", "MOON", "MARS",
    "RAHU", "JUPITER", "SATURN", "MERCURY",
)

# One Nakshatra arc in degrees (360 / 27 = 13°20′)
NAKSHATRA_ARC: float = 360.0 / 27.0

# Edge weights for Nakshatra relationships
NAKSHATRA_PARIVARTANA_WEIGHT: float = 0.85
NAKSHATRA_LORD_WEIGHT: float = 0.65


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NakshatraEdge:
    """Immutable Nakshatra-based relationship edge.

    Attributes:
        source: Source planet name.
        target: Target planet name.
        edge_type: 'NAKSHATRA_PARIVARTANA' or 'NAKSHATRA_LORD'.
        weight: Base weight for this edge type.
        source_nakshatra: Nakshatra name occupied by source planet.
        target_nakshatra: Nakshatra name occupied by target planet.
    """

    source: str
    target: str
    edge_type: str
    weight: float
    source_nakshatra: str
    target_nakshatra: str


# ── Service ──────────────────────────────────────────────────────────────────


class NakshatraRelationshipService:
    """Detects Nakshatra-based planetary relationships.

    Uses the Vimshottari Nakshatra lord cycle to determine which planet
    rules each Nakshatra, then detects mutual exchanges and one-directional
    dependencies.
    """

    @staticmethod
    def get_nakshatra_lord(longitude: float) -> str:
        """Determine the Nakshatra lord for a given planetary longitude.

        Args:
            longitude: Planetary longitude in degrees (0.0–360.0).

        Returns:
            Uppercase planet name of the Nakshatra lord.
        """
        folded = longitude % 360.0
        nakshatra_index = int((folded * 27.0) // 360.0) % 27
        lord_index = nakshatra_index % 9
        return _NAKSHATRA_LORD_CYCLE[lord_index]

    @staticmethod
    def get_nakshatra_name(longitude: float) -> str:
        """Determine the Nakshatra name for a given planetary longitude.

        Args:
            longitude: Planetary longitude in degrees (0.0–360.0).

        Returns:
            Nakshatra name (e.g., 'ASHWINI', 'BHARANI', ...).
        """
        folded = longitude % 360.0
        nakshatra_index = int((folded * 27.0) // 360.0) % 27
        return NAKSHATRA_NAMES[nakshatra_index]

    def detect_relationships(
        self,
        planet_positions: dict[str, float],
    ) -> list[NakshatraEdge]:
        """Detect Nakshatra-based relationships from planetary longitudes.

        For each pair of planets (A, B):
        - If A is in B's Nakshatra AND B is in A's Nakshatra →
          NAKSHATRA_PARIVARTANA (bidirectional, weight=0.85).
        - Else if A is in B's Nakshatra →
          NAKSHATRA_LORD (directed A→B, weight=0.65).

        Args:
            planet_positions: Mapping of planet name → longitude in degrees.

        Returns:
            List of NakshatraEdge objects for all detected relationships.
        """
        edges: list[NakshatraEdge] = []

        # Build mapping: planet → Nakshatra lord of its Nakshatra
        planet_to_lord: dict[str, str] = {}
        planet_to_nakshatra: dict[str, str] = {}
        for planet, longitude in planet_positions.items():
            lord = self.get_nakshatra_lord(longitude)
            nakshatra = self.get_nakshatra_name(longitude)
            planet_to_lord[planet] = lord
            planet_to_nakshatra[planet] = nakshatra

        # Check for mutual exchanges (Parivartana)
        checked_pairs: set[tuple[str, str]] = set()
        for planet_a, lord_a in planet_to_lord.items():
            # lord_a is the planet that rules planet_a's Nakshatra
            if lord_a not in planet_positions:
                continue
            if lord_a == planet_a:
                continue  # Planet in its own Nakshatra — not a relationship

            # Check if lord_a's Nakshatra is ruled by planet_a (reciprocal)
            lord_a_lord = planet_to_lord.get(lord_a)
            if lord_a_lord == planet_a:
                pair = tuple(sorted([planet_a, lord_a]))
                if pair not in checked_pairs:
                    checked_pairs.add(pair)
                    edges.append(NakshatraEdge(
                        source=planet_a,
                        target=lord_a,
                        edge_type="NAKSHATRA_PARIVARTANA",
                        weight=NAKSHATRA_PARIVARTANA_WEIGHT,
                        source_nakshatra=planet_to_nakshatra[planet_a],
                        target_nakshatra=planet_to_nakshatra[lord_a],
                    ))

        # Check for one-directional Nakshatra lord dependencies
        parivartana_pairs = {frozenset(pair) for pair in checked_pairs}
        for planet_a, lord_a in planet_to_lord.items():
            if lord_a not in planet_positions:
                continue
            if lord_a == planet_a:
                continue
            pair_key = frozenset([planet_a, lord_a])
            if pair_key in parivartana_pairs:
                continue  # Already recorded as Parivartana

            # One-directional: A's Nakshatra lord is B
            edges.append(NakshatraEdge(
                source=planet_a,
                target=lord_a,
                edge_type="NAKSHATRA_LORD",
                weight=NAKSHATRA_LORD_WEIGHT,
                source_nakshatra=planet_to_nakshatra[planet_a],
                target_nakshatra=planet_to_nakshatra[lord_a],
            ))

        return edges


# ── Nakshatra Names ──────────────────────────────────────────────────────────

NAKSHATRA_NAMES: tuple[str, ...] = (
    "ASHWINI", "BHARANI", "KRITTIKA", "ROHINI", "MRIGASHIRA",
    "ARDRA", "PUNARVASU", "PUSHYA", "ASHLESHA", "MAGHA",
    "PURVA_PHALGUNI", "UTTARA_PHALGUNI", "HASTA", "CHITRA", "SWATI",
    "VISHAKHA", "ANURADHA", "JYESHTHA", "MULA", "PURVA_ASHADHA",
    "UTTARA_ASHADHA", "SHRAVANA", "DHANISHTHA", "SHATABHISHA",
    "PURVA_BHADRAPADA", "UTTARA_BHADRAPADA", "REVATI",
)
