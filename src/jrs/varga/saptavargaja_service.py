"""JRS-078 Saptavargaja Bala Service — 7-Varga Dignity Evaluation.

Evaluates planetary dignity across 7 Vargas (divisional charts) and computes
a composite Saptavargaja Bala score.

Point Matrix (BPHS Ch 3, Phaladeepika Ch 2):
    Moolatrikona:  5.0
    Own sign:      4.0
    Great Friend:  3.5
    Friend:        3.0
    Neutral:       2.0
    Enemy:         1.0
    Great Enemy:   0.5
    Debilitated:   0.0

Classification:
    >= 25: Very Strong
    18–24: Moderate
    < 18:  Weak

Source: BPHS Ch 3 (Varga), Ch 45 (Saptavargaja); Phaladeepika Ch 2;
        Jataka Parijata Ch 3.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class DignityLevel(StrEnum):
    """Dignity classification for Saptavargaja Bala score."""
    VERY_STRONG = "VERY_STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


@dataclass(frozen=True)
class SaptavargajaScore:
    """Saptavargaja Bala score for a single planet across 7 Vargas."""
    planet: str
    total_score: float
    dignity_level: DignityLevel
    varga_scores: dict[str, float]
    moolatrikona_count: int = 0
    own_sign_count: int = 0
    friend_count: int = 0
    enemy_count: int = 0
    neutral_count: int = 0
    debilitated_count: int = 0


# ── Point Matrix ──────────────────────────────────────────────────────
# Classical dignity strength weights for Saptavargaja Bala (BPHS Ch 3)
DIGNITY_POINTS: dict[str, float] = {
    "MOOLATRIKONA": 5.0,
    "OWN": 4.0,
    "GREAT_FRIEND": 3.5,
    "FRIEND": 3.0,
    "NEUTRAL": 2.0,
    "ENEMY": 1.0,
    "GREAT_ENEMY": 0.5,
    "DEBILITATED": 0.0,
}

# ── Classification Thresholds ────────────────────────────────────────
SCORE_VERY_STRONG: float = 25.0
SCORE_MODERATE: float = 18.0

# ── Vargas Evaluated ─────────────────────────────────────────────────
VARGA_NAMES: tuple[str, ...] = ("D1", "D2", "D3", "D7", "D9", "D12", "D30")

# ── Exaltation Signs (1-indexed rashi number) ────────────────────────
_EXALTATION: dict[str, int] = {
    "SUN": 1,       # Aries
    "MOON": 2,      # Taurus
    "MARS": 10,     # Capricorn
    "MERCURY": 6,   # Virgo
    "JUPITER": 4,   # Cancer
    "VENUS": 12,    # Pisces
    "SATURN": 7,    # Libra
}

# ── Moolatrikona Signs (1-indexed rashi number) ─────────────────────
# BPHS Ch 3: Moolatrikona is between 0°20' and the start of the sign
_MOOLATRIKONA: dict[str, int] = {
    "SUN": 5,       # Leo (0°20'–20°)
    "MOON": 2,      # Taurus (4°–20°)
    "MARS": 1,      # Aries (0°20'–12°)
    "MERCURY": 6,   # Virgo (16°–20°)
    "JUPITER": 9,   # Sagittarius (0°20'–10°)
    "VENUS": 7,     # Libra (0°20'–15°)
    "SATURN": 11,   # Aquarius (0°20'–20°)
}

# ── Own Signs (1-indexed rashi numbers) ─────────────────────────────
_OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "SUN": (5,),
    "MOON": (4,),
    "MARS": (1, 8),
    "MERCURY": (3, 6),
    "JUPITER": (9, 12),
    "VENUS": (2, 7),
    "SATURN": (10, 11),
}

# ── Debilitation Signs (1-indexed rashi number) ─────────────────────
_DEBILITATION: dict[str, int] = {
    "SUN": 7,       # Libra
    "MOON": 8,      # Scorpio
    "MARS": 4,      # Cancer
    "MERCURY": 12,  # Pisces
    "JUPITER": 10,  # Capricorn
    "VENUS": 6,     # Virgo
    "SATURN": 1,    # Aries
}

# ── Friendship Table (BPHS Ch 2) ────────────────────────────────────
# Great Friends, Friends, Neutral, Enemies, Great Enemies
_FRIENDSHIP: dict[str, dict[str, str]] = {
    "SUN": {
        "MOON": "FRIEND", "MARS": "FRIEND", "JUPITER": "FRIEND",
        "MERCURY": "ENEMY", "VENUS": "ENEMY", "SATURN": "ENEMY",
    },
    "MOON": {
        "SUN": "FRIEND", "MARS": "ENEMY", "JUPITER": "FRIEND",
        "MERCURY": "ENEMY", "VENUS": "FRIEND", "SATURN": "ENEMY",
    },
    "MARS": {
        "SUN": "FRIEND", "MOON": "ENEMY", "JUPITER": "FRIEND",
        "MERCURY": "ENEMY", "VENUS": "ENEMY", "SATURN": "FRIEND",
    },
    "MERCURY": {
        "SUN": "ENEMY", "MOON": "ENEMY", "MARS": "ENEMY",
        "JUPITER": "FRIEND", "VENUS": "FRIEND", "SATURN": "FRIEND",
    },
    "JUPITER": {
        "SUN": "FRIEND", "MOON": "FRIEND", "MARS": "FRIEND",
        "MERCURY": "ENEMY", "VENUS": "ENEMY", "SATURN": "ENEMY",
    },
    "VENUS": {
        "SUN": "ENEMY", "MOON": "FRIEND", "MARS": "ENEMY",
        "MERCURY": "FRIEND", "JUPITER": "ENEMY", "SATURN": "FRIEND",
    },
    "SATURN": {
        "SUN": "ENEMY", "MOON": "ENEMY", "MARS": "FRIEND",
        "MERCURY": "FRIEND", "JUPITER": "ENEMY", "VENUS": "FRIEND",
    },
}

# ── Great Friend / Great Enemy overrides ────────────────────────────
_GREAT_FRIENDS: dict[str, frozenset[str]] = {
    "SUN": frozenset({"JUPITER", "MOON", "MARS"}),
    "MOON": frozenset({"SUN", "JUPITER"}),
    "MARS": frozenset({"JUPITER", "SUN"}),
    "MERCURY": frozenset({"SATURN"}),
    "JUPITER": frozenset({"SUN", "MOON", "MARS"}),
    "VENUS": frozenset({"MERCURY", "SATURN"}),
    "SATURN": frozenset({"MERCURY", "VENUS"}),
}

_GREAT_ENEMIES: dict[str, frozenset[str]] = {
    "SUN": frozenset({"VENUS", "SATURN"}),
    "MOON": frozenset({"MARS", "SATURN"}),
    "MARS": frozenset({"MERCURY", "VENUS"}),
    "MERCURY": frozenset({"SUN", "MOON"}),
    "JUPITER": frozenset({"VENUS", "SATURN"}),
    "VENUS": frozenset({"SUN", "JUPITER"}),
    "SATURN": frozenset({"SUN", "MOON", "JUPITER"}),
}


def _rashi_to_index(rashi_str: str) -> int | None:
    """Convert Rashi string to 0-based index."""
    _RASHI_ORDER: list[str] = [
        "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
        "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
    ]
    try:
        return _RASHI_ORDER.index(rashi_str)
    except ValueError:
        return None


def _get_dignity(planet: str, rashi_num: int) -> str:
    """Determine planet's dignity for a given rashi number.

    Returns one of: MOOLATRIKONA, OWN, GREAT_FRIEND, FRIEND, NEUTRAL,
    ENEMY, GREAT_ENEMY, DEBILITATED.
    """
    # 1. Exaltation
    if rashi_num == _EXALTATION.get(planet, -1):
        return "MOOLATRIKONA"  # Exaltation is highest dignity

    # 2. Moolatrikona
    if rashi_num == _MOOLATRIKONA.get(planet, -1):
        return "MOOLATRIKONA"

    # 3. Own sign
    if rashi_num in _OWN_SIGNS.get(planet, ()):
        return "OWN"

    # 4. Debilitation
    if rashi_num == _DEBILITATION.get(planet, -1):
        return "DEBILITATED"

    # 5. Friendship-based dignity
    # The sign lord determines the friendship relationship
    _SIGN_LORDS: dict[int, str] = {
        1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
        6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
        11: "SATURN", 12: "JUPITER",
    }
    sign_lord = _SIGN_LORDS.get(rashi_num)
    if sign_lord is None or sign_lord == planet:
        return "NEUTRAL"

    # Check Great Friend / Great Enemy overrides
    if planet in _GREAT_FRIENDS and sign_lord in _GREAT_FRIENDS[planet]:
        return "GREAT_FRIEND"
    if planet in _GREAT_ENEMIES and sign_lord in _GREAT_ENEMIES[planet]:
        return "GREAT_ENEMY"

    # Check basic friendship
    rel = _FRIENDSHIP.get(planet, {}).get(sign_lord, "NEUTRAL")
    return rel


class SaptavargajaBalaService:
    """Evaluates dignity across 7 Vargas and computes Saptavargaja Bala.

    The Saptavargaja Bala is a composite score reflecting a planet's dignity
    across 7 divisional charts (D1, D2, D3, D7, D9, D12, D30).

    Each varga contributes a point based on the planet's dignity in that varga.
    Total score is classified as Very Strong (>=25), Moderate (18-24), or
    Weak (<18).
    """

    def evaluate_planet(
        self,
        planet: str,
        planet_facts: dict[str, Any],
    ) -> SaptavargajaScore:
        """Evaluate Saptavargaja Bala for a single planet.

        Args:
            planet: Planet name (e.g., "JUPITER").
            planet_facts: Dictionary with varga sign data:
                {
                    "rashi_num": int,           # D1 rashi number
                    "planet_d2_sign": str,      # D2 sign name
                    "planet_d3_sign": str,      # D3 sign name
                    "planet_d7_sign": str,      # D7 sign name
                    "planet_d9_sign": str,      # D9 sign name
                    "planet_d12_sign": str,     # D12 sign name
                    "planet_d30_sign": str,     # D30 sign name
                }

        Returns:
            SaptavargajaScore with total score and per-varga breakdown.
        """
        varga_scores: dict[str, float] = {}
        moolatrikona_count = 0
        own_sign_count = 0
        friend_count = 0
        enemy_count = 0
        neutral_count = 0
        debilitated_count = 0

        for varga in VARGA_NAMES:
            # Get the rashi number for this varga
            rashi_num = self._get_varga_rashi_num(planet, varga, planet_facts)
            if rashi_num is None:
                # Varga data not available — skip (no contribution)
                continue

            # Determine dignity
            dignity = _get_dignity(planet, rashi_num)
            point = DIGNITY_POINTS[dignity]
            varga_scores[varga] = point

            # Count categories
            if dignity == "MOOLATRIKONA":
                moolatrikona_count += 1
            elif dignity == "OWN":
                own_sign_count += 1
            elif dignity in ("FRIEND", "GREAT_FRIEND"):
                friend_count += 1
            elif dignity in ("ENEMY", "GREAT_ENEMY"):
                enemy_count += 1
            elif dignity == "NEUTRAL":
                neutral_count += 1
            elif dignity == "DEBILITATED":
                debilitated_count += 1

        total_score = sum(varga_scores.values())
        dignity_level = self._classify_score(total_score)

        return SaptavargajaScore(
            planet=planet,
            total_score=total_score,
            dignity_level=dignity_level,
            varga_scores=varga_scores,
            moolatrikona_count=moolatrikona_count,
            own_sign_count=own_sign_count,
            friend_count=friend_count,
            enemy_count=enemy_count,
            neutral_count=neutral_count,
            debilitated_count=debilitated_count,
        )

    def evaluate_all_planets(
        self,
        jre_facts: dict[str, Any],
    ) -> dict[str, SaptavargajaScore]:
        """Evaluate Saptavargaja Bala for all planets in the chart.

        Args:
            jre_facts: JRE facts dictionary with planet data and varga signs.

        Returns:
            Dictionary mapping planet names to their SaptavargajaScore.
        """
        planets = jre_facts.get("planets", {})
        scores: dict[str, SaptavargajaScore] = {}

        for planet, p_data in planets.items():
            scores[planet] = self.evaluate_planet(planet, p_data)

        return scores

    def get_strongest_planet(
        self,
        jre_facts: dict[str, Any],
    ) -> tuple[str, SaptavargajaScore] | None:
        """Find the planet with the highest Saptavargaja Bala score.

        Args:
            jre_facts: JRE facts dictionary.

        Returns:
            Tuple of (planet_name, score) or None if no planets.
        """
        scores = self.evaluate_all_planets(jre_facts)
        if not scores:
            return None
        return max(scores.items(), key=lambda item: item[1].total_score)

    # ── Private helpers ──

    @staticmethod
    def _get_varga_rashi_num(
        planet: str,
        varga: str,
        planet_facts: dict[str, Any],
    ) -> int | None:
        """Get the rashi number for a planet in a specific varga."""
        _RASHI_ORDER: list[str] = [
            "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
            "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
        ]

        if varga == "D1":
            return planet_facts.get("rashi_num")

        # For other vargas, get sign name and convert to rashi number
        sign_key = f"planet_{varga.lower()}_sign"
        sign_name = planet_facts.get(sign_key)
        if sign_name is None:
            return None
        try:
            return _RASHI_ORDER.index(sign_name) + 1
        except ValueError:
            return None

    @staticmethod
    def _classify_score(total_score: float) -> DignityLevel:
        """Classify total Saptavargaja Bala score."""
        if total_score >= SCORE_VERY_STRONG:
            return DignityLevel.VERY_STRONG
        elif total_score >= SCORE_MODERATE:
            return DignityLevel.MODERATE
        else:
            return DignityLevel.WEAK
