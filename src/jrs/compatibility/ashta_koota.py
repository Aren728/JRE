"""JRE Compatibility — Ashta Koota (Eight-Factor) Matching Engine.

Implements the classical Parashari Ashta Koota guna milan system for
marriage compatibility assessment based on the 27 Nakshatras.

The 8 factors and their maximum points:
  1. Varna (1 pt) — Spiritual compatibility
  2. Vashya (2 pts) — Mutual attraction
  3. Tara (3 pts) — Birth star compatibility
  4. Yoni (4 pts) — Physical compatibility
  5. Graha Maitri (5 pts) — Planetary friendship
  6. Gana (6 pts) — Behavioral temperament
  7. Bhakoot (7 pts) — Love & family compatibility
  8. Nadi (8 pts) — Health & progeny

Total maximum: 36 points

Source: BPHS Ch 36; Phaladeepika Ch 14; Mangala Prakash.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── Nakshatra Constants ──────────────────────────────────

NAKSHATRAS: list[str] = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# ── Varna (Spiritual Compatibility) ──────────────────────
# Brahmin (4) > Kshatriya (3) > Vaishya (2) > Shudra (1)
# Higher varna of bride = 1 pt, equal = 1 pt, lower = 0 pts

VARNA_MAP: dict[str, int] = {
    # Brahmin (spiritual)
    "ASHWINI": 4,
    "PUNARVASU": 4,
    "PUSHA": 4,
    "HASTA": 4,
    "SWATI": 4,
    "REVATI": 4,
    # Kshatriya (warrior)
    "BHARANI": 3,
    "KRITTIKA": 3,
    "ARIDRA": 3,
    "ASHLESHA": 3,
    "MAGHA": 3,
    "PURVA PHALGUNI": 3,
    # Vaishya (merchant)
    "ROHINI": 2,
    "MRIGASHIRA": 2,
    "UTTARA PHALGUNI": 2,
    "CHITRA": 2,
    "VISHAKHA": 2,
    "ANURADHA": 2,
    # Shudra (service)
    "JYESHTHA": 1,
    "MULA": 1,
    "PURVA ASHADHA": 1,
    "UTTARA ASHADHA": 1,
    "SHRAVANA": 1,
    "DHANISHTA": 1,
    "SHATABHISHA": 1,
    "PURVA BHADRAPADA": 1,
    "UTTARA BHADRAPADA": 1,
}


def _get_varna(nakshatra: str) -> int:
    """Get varna category for a nakshatra."""
    return VARNA_MAP.get(nakshatra.upper(), 1)


def _calc_varna(nak_a: str, nak_b: str) -> int:
    """Calculate Varna score (0 or 1).

    Groom's varna >= Bride's varna = 1 point.
    """
    varna_a = _get_varna(nak_a)
    varna_b = _get_varna(nak_b)
    # In traditional matching, groom's varna should be >= bride's
    # Here we check if person A (groom) has higher or equal varna
    return 1 if varna_a >= varna_b else 0


# ── Vashya (Mutual Attraction) ───────────────────────────
# Based on animal signs assigned to nakshatras

YONI_ANIMALS: list[str] = [
    "Horse",
    "Elephant",
    "Sheep",
    "Serpent",
    "Serpent",
    "Dog",
    "Cat",
    "Sheep",
    "Cat",
    "Rat",
    "Rat",
    "Cow",
    "Buffalo",
    "Tiger",
    "Buffalo",
    "Tiger",
    "Hare",
    "Hare",
    "Dog",
    "Monkey",
    "Mongoose",
    "Monkey",
    "Lion",
    "Horse",
    "Lion",
    "Cow",
    "Elephant",
]

# Vashya categories based on yoni animals
VASHYA_CATEGORIES: dict[str, list[str]] = {
    "Chatushpad": ["Horse", "Sheep", "Monkey", "Mongoose"],  # Quadrupeds
    "Manav": ["Elephant"],  # Human
    "Jalachara": ["Serpent"],  # Water animals
    "Vanachara": ["Tiger", "Lion"],  # Wild animals
    "Keet": ["Rat", "Hare", "Cat", "Dog", "Buffalo", "Cow"],  # Small animals
}

# Vashya compatibility matrix (simplified)
# Same category = 2 pts, Friendly categories = 1 pt, Enemy = 0
VASHYA_FRIENDLY: dict[str, list[str]] = {
    "Chatushpad": ["Manav"],
    "Manav": ["Chatushpad"],
    "Jalachara": ["Vanachara"],
    "Vanachara": ["Jalachara"],
    "Keet": ["Keet"],
}


def _get_yoni_category(animal: str) -> str:
    """Get vashya category for an animal."""
    for category, animals in VASHYA_CATEGORIES.items():
        if animal in animals:
            return category
    return "Keet"


def _calc_vashya(nak_a: str, nak_b: str) -> int:
    """Calculate Vashya score (0-2).

    Same animal = 2, Same category = 1, Friendly = 1, Enemy = 0.
    """
    idx_a = NAKSHATRAS.index(nak_a) if nak_a in NAKSHATRAS else 0
    idx_b = NAKSHATRAS.index(nak_b) if nak_b in NAKSHATRAS else 0

    animal_a = YONI_ANIMALS[idx_a]
    animal_b = YONI_ANIMALS[idx_b]

    # Same animal = 2 points
    if animal_a == animal_b:
        return 2

    cat_a = _get_yoni_category(animal_a)
    cat_b = _get_yoni_category(animal_b)

    # Same category = 1 point
    if cat_a == cat_b:
        return 1

    # Friendly categories = 1 point
    if cat_b in VASHYA_FRIENDLY.get(cat_a, []):
        return 1

    return 0


# ── Tara (Birth Star Compatibility) ──────────────────────
# Count from groom's nakshatra to bride's and vice versa
# Remainder when divided by 9: 3, 5, 7 are inauspicious


def _calc_tara(nak_a: str, nak_b: str) -> int:
    """Calculate Tara score (0 or 3).

    If remainder is 1, 2, 4, 6, 8, 9 = auspicious (3 pts)
    If remainder is 3, 5, 7 = inauspicious (0 pts)
    """
    idx_a = NAKSHATRAS.index(nak_a) if nak_a in NAKSHATRAS else 0
    idx_b = NAKSHATRAS.index(nak_b) if nak_b in NAKSHATRAS else 0

    # Count from A to B
    diff_ab = ((idx_b - idx_a) % 27) + 1
    # Count from B to A
    diff_ba = ((idx_a - idx_b) % 27) + 1

    remainder_ab = diff_ab % 9
    remainder_ba = diff_ba % 9

    # Both remainders should be auspicious
    inauspicious = {3, 5, 7}
    if remainder_ab not in inauspicious and remainder_ba not in inauspicious:
        return 3

    return 0


# ── Yoni (Physical Compatibility) ────────────────────────
# Based on yoni animals - some are compatible, some are enemies

YONI_ENEMIES: dict[str, str] = {
    "Horse": "Buffalo",
    "Buffalo": "Horse",
    "Tiger": "Cow",
    "Cow": "Tiger",
    "Rat": "Cat",
    "Cat": "Rat",
    "Hare": "Dog",
    "Dog": "Hare",
    "Elephant": "Lion",
    "Lion": "Elephant",
    "Monkey": "Mongoose",
    "Mongoose": "Monkey",
    "Sheep": "Serpent",
    "Serpent": "Sheep",
}


def _calc_yoni(nak_a: str, nak_b: str) -> int:
    """Calculate Yoni score (0-4).

    Same animal = 4, Male-Female pair = 3, Friendly = 2, Neutral = 1, Enemy = 0.
    """
    idx_a = NAKSHATRAS.index(nak_a) if nak_a in NAKSHATRAS else 0
    idx_b = NAKSHATRAS.index(nak_b) if nak_b in NAKSHATRAS else 0

    animal_a = YONI_ANIMALS[idx_a]
    animal_b = YONI_ANIMALS[idx_b]

    # Same animal = 4 points
    if animal_a == animal_b:
        return 4

    # Enemy animals = 0 points
    if YONI_ENEMIES.get(animal_a) == animal_b:
        return 0

    # Friendly animals (same category) = 2 points
    cat_a = _get_yoni_category(animal_a)
    cat_b = _get_yoni_category(animal_b)
    if cat_a == cat_b:
        return 2

    # Neutral = 1 point
    return 1


# ── Graha Maitri (Planetary Friendship) ──────────────────
# Based on the ruling planets of nakshatras

NAKSHATRA_LORDS: list[str] = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

# Planetary friendship matrix
PLANET_FRIENDS: dict[str, list[str]] = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Saturn", "Mercury", "Venus"],
    "Ketu": ["Mars", "Jupiter"],
}

PLANET_ENEMIES: dict[str, list[str]] = {
    "Sun": ["Venus", "Saturn", "Rahu"],
    "Moon": ["Rahu", "Ketu"],
    "Mars": ["Mercury", "Rahu", "Ketu"],
    "Mercury": ["Moon"],
    "Jupiter": ["Venus", "Mercury"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Venus", "Mercury"],
}


def _calc_graha_maitri(nak_a: str, nak_b: str) -> int:
    """Calculate Graha Maitri score (0-5).

    Based on planetary lord friendship.
    """
    idx_a = NAKSHATRAS.index(nak_a) if nak_a in NAKSHATRAS else 0
    idx_b = NAKSHATRAS.index(nak_b) if nak_b in NAKSHATRAS else 0

    lord_a = NAKSHATRA_LORDS[idx_a]
    lord_b = NAKSHATRA_LORDS[idx_b]

    # Same planet = 5 points
    if lord_a == lord_b:
        return 5

    # Mutual friends = 4 points
    if lord_b in PLANET_FRIENDS.get(lord_a, []) and lord_a in PLANET_FRIENDS.get(lord_b, []):
        return 4

    # One-way friendship = 3 points
    if lord_b in PLANET_FRIENDS.get(lord_a, []) or lord_a in PLANET_FRIENDS.get(lord_b, []):
        return 3

    # Neutral = 2 points
    if lord_b not in PLANET_ENEMIES.get(lord_a, []) and lord_a not in PLANET_ENEMIES.get(
        lord_b, []
    ):
        return 2

    # One-way enemy = 1 point
    if lord_b in PLANET_ENEMIES.get(lord_a, []) or lord_a in PLANET_ENEMIES.get(lord_b, []):
        return 1

    # Mutual enemies = 0 points
    return 0


# ── Gana (Behavioral Temperament) ────────────────────────
# Deva (divine), Manushya (human), Rakshasa (demon)

GANA_MAP: dict[str, str] = {
    "ASHWINI": "Deva",
    "BHARANI": "Manushya",
    "KRITTIKA": "Rakshasa",
    "ROHINI": "Manushya",
    "MRIGASHIRA": "Deva",
    "ARIDRA": "Rakshasa",
    "PUNARVASU": "Deva",
    "PUSHA": "Deva",
    "ASHLESHA": "Rakshasa",
    "MAGHA": "Rakshasa",
    "PURVA PHALGUNI": "Manushya",
    "UTTARA PHALGUNI": "Manushya",
    "HASTA": "Deva",
    "CHITRA": "Rakshasa",
    "SWATI": "Deva",
    "VISHAKHA": "Rakshasa",
    "ANURADHA": "Deva",
    "JYESHTHA": "Rakshasa",
    "MULA": "Rakshasa",
    "PURVA ASHADHA": "Manushya",
    "UTTARA ASHADHA": "Manushya",
    "SHRAVANA": "Deva",
    "DHANISHTA": "Rakshasa",
    "SHATABHISHA": "Rakshasa",
    "PURVA BHADRAPADA": "Manushya",
    "UTTARA BHADRAPADA": "Manushya",
    "REVATI": "Deva",
}

# Gana compatibility matrix
GANA_SCORES: dict[tuple[str, str], int] = {
    ("Deva", "Deva"): 6,
    ("Deva", "Manushya"): 5,
    ("Deva", "Rakshasa"): 1,
    ("Manushya", "Deva"): 6,
    ("Manushya", "Manushya"): 6,
    ("Manushya", "Rakshasa"): 0,
    ("Rakshasa", "Deva"): 0,
    ("Rakshasa", "Manushya"): 0,
    ("Rakshasa", "Rakshasa"): 6,
}


def _calc_gana(nak_a: str, nak_b: str) -> int:
    """Calculate Gana score (0 or 6).

    Same gana = 6, Deva-Manushya = 5, Rakshasa with non-Rakshasa = 0.
    """
    gana_a = GANA_MAP.get(nak_a.upper(), "Manushya")
    gana_b = GANA_MAP.get(nak_b.upper(), "Manushya")

    return GANA_SCORES.get((gana_a, gana_b), 0)


# ── Bhakoot (Love & Family Compatibility) ────────────────
# Based on the relative position of nakshatras


def _calc_bhakoot(nak_a: str, nak_b: str) -> int:
    """Calculate Bhakoot score (0 or 7).

    Based on counting from groom's nakshatra to bride's:
    - 2, 3, 4, 5, 6, 7, 8, 12 = 7 points
    - 1, 9, 10, 11 = 0 points (Bhakoot dosha)
    """
    idx_a = NAKSHATRAS.index(nak_a) if nak_a in NAKSHATRAS else 0
    idx_b = NAKSHATRAS.index(nak_b) if nak_b in NAKSHATRAS else 0

    # Count from A to B
    diff = ((idx_b - idx_a) % 27) + 1

    # Positions that cause Bhakoot dosha
    bhakoot_dosha = {1, 9, 10, 11}

    return 0 if diff in bhakoot_dosha else 7


# ── Nadi (Health & Progeny) ──────────────────────────────
# Aadi, Madhya, Antya - same nadi = Nadi dosha (0 pts)

NADI_MAP: dict[str, str] = {
    "ASHWINI": "Aadi",
    "BHARANI": "Madhya",
    "KRITTIKA": "Antya",
    "ROHINI": "Aadi",
    "MRIGASHIRA": "Madhya",
    "ARIDRA": "Antya",
    "PUNARVASU": "Aadi",
    "PUSHA": "Madhya",
    "ASHLESHA": "Antya",
    "MAGHA": "Aadi",
    "PURVA PHALGUNI": "Madhya",
    "UTTARA PHALGUNI": "Antya",
    "HASTA": "Aadi",
    "CHITRA": "Madhya",
    "SWATI": "Antya",
    "VISHAKHA": "Aadi",
    "ANURADHA": "Madhya",
    "JYESHTHA": "Antya",
    "MULA": "Aadi",
    "PURVA ASHADHA": "Madhya",
    "UTTARA ASHADHA": "Antya",
    "SHRAVANA": "Aadi",
    "DHANISHTA": "Madhya",
    "SHATABHISHA": "Antya",
    "PURVA BHADRAPADA": "Aadi",
    "UTTARA BHADRAPADA": "Madhya",
    "REVATI": "Antya",
}


def _calc_nadi(nak_a: str, nak_b: str) -> int:
    """Calculate Nadi score (0 or 8).

    Same nadi = 0 (Nadi dosha), Different nadi = 8 points.
    """
    nadi_a = NADI_MAP.get(nak_a.upper(), "Aadi")
    nadi_b = NADI_MAP.get(nak_b.upper(), "Aadi")

    return 0 if nadi_a == nadi_b else 8


# ── Main Calculation ─────────────────────────────────────


@dataclass
class KootaResult:
    """Result for a single Koota factor."""

    name: str
    score: int
    max_points: int
    description: str


@dataclass
class AshtaKootaResult:
    """Complete Ashta Koota compatibility result."""

    person_a_nakshatra: str
    person_b_nakshatra: str
    total_score: int
    max_score: int
    kootas: list[KootaResult]
    assessment: str
    assessment_details: str
    has_nadi_dosha: bool
    has_bhakoot_dosha: bool


def calculate_ashta_koota(
    person_a_nakshatra: str,
    person_b_nakshatra: str,
) -> AshtaKootaResult:
    """Calculate Ashta Koota compatibility between two nakshatras.

    Args:
        person_a_nakshatra: First person's nakshatra (e.g., "Ashwini").
        person_b_nakshatra: Second person's nakshatra (e.g., "Rohini").

    Returns:
        AshtaKootaResult with total score, individual kootas, and assessment.

    Raises:
        ValueError: If either nakshatra is invalid.
    """
    # Normalize nakshatra names
    nak_a = person_a_nakshatra.strip().title()
    nak_b = person_b_nakshatra.strip().title()

    # Validate
    if nak_a not in NAKSHATRAS:
        raise ValueError(f"Invalid nakshatra: {person_a_nakshatra}. Valid options: {NAKSHATRAS}")
    if nak_b not in NAKSHATRAS:
        raise ValueError(f"Invalid nakshatra: {person_b_nakshatra}. Valid options: {NAKSHATRAS}")

    # Calculate each Koota
    kootas = [
        KootaResult(
            name="Varna",
            score=_calc_varna(nak_a, nak_b),
            max_points=1,
            description="Spiritual compatibility and ego harmony",
        ),
        KootaResult(
            name="Vashya",
            score=_calc_vashya(nak_a, nak_b),
            max_points=2,
            description="Mutual attraction and dominance balance",
        ),
        KootaResult(
            name="Tara",
            score=_calc_tara(nak_a, nak_b),
            max_points=3,
            description="Birth star compatibility and health",
        ),
        KootaResult(
            name="Yoni",
            score=_calc_yoni(nak_a, nak_b),
            max_points=4,
            description="Physical compatibility and temperament",
        ),
        KootaResult(
            name="Graha Maitri",
            score=_calc_graha_maitri(nak_a, nak_b),
            max_points=5,
            description="Planetary friendship and mental compatibility",
        ),
        KootaResult(
            name="Gana",
            score=_calc_gana(nak_a, nak_b),
            max_points=6,
            description="Behavioral temperament and nature",
        ),
        KootaResult(
            name="Bhakoot",
            score=_calc_bhakoot(nak_a, nak_b),
            max_points=7,
            description="Love, family, and emotional compatibility",
        ),
        KootaResult(
            name="Nadi",
            score=_calc_nadi(nak_a, nak_b),
            max_points=8,
            description="Health, genetics, and progeny",
        ),
    ]

    total = sum(k.score for k in kootas)
    max_score = sum(k.max_points for k in kootas)

    # Check for doshas
    has_nadi_dosha = _calc_nadi(nak_a, nak_b) == 0
    has_bhakoot_dosha = _calc_bhakoot(nak_a, nak_b) == 0

    # Generate assessment
    pct = total / max_score
    if pct >= 0.85:
        assessment = "Excellent Match"
        details = (
            "This pairing shows exceptional compatibility across all dimensions. "
            "The stars are strongly aligned for a harmonious and lasting partnership."
        )
    elif pct >= 0.70:
        assessment = "Very Good Match"
        details = (
            "A strong match with good compatibility in most areas. "
            "Minor differences exist but can be easily navigated with mutual understanding."
        )
    elif pct >= 0.55:
        assessment = "Good Match"
        details = (
            "A moderate to good match with solid potential. "
            "Some areas require conscious effort, but the foundation is strong."
        )
    elif pct >= 0.40:
        assessment = "Average Match"
        details = (
            "A challenging match that requires significant effort from both partners. "
            "With dedication and classical remedies, the relationship can still thrive."
        )
    else:
        assessment = "Requires Remedies"
        details = (
            "This pairing has significant challenges. "
            "Classical texts recommend specific remedies and careful consideration."
        )

    # Add dosha warnings
    if has_nadi_dosha:
        details += (
            " Note: Nadi Dosha is present. Classical remedies such as "
            "Nadi Dosha Nivaran Puja are recommended."
        )
    if has_bhakoot_dosha:
        details += (
            " Note: Bhakoot Dosha is present. This may affect family harmony. "
            "Remedies through propitiation of the ruling deities are advised."
        )

    return AshtaKootaResult(
        person_a_nakshatra=nak_a,
        person_b_nakshatra=nak_b,
        total_score=total,
        max_score=max_score,
        kootas=kootas,
        assessment=assessment,
        assessment_details=details,
        has_nadi_dosha=has_nadi_dosha,
        has_bhakoot_dosha=has_bhakoot_dosha,
    )


def ashta_koota_to_dict(result: AshtaKootaResult) -> dict[str, Any]:
    """Convert AshtaKootaResult to JSON-serializable dict.

    Args:
        result: AshtaKootaResult from calculate_ashta_koota.

    Returns:
        JSON-serializable dictionary.
    """
    return {
        "person_a_nakshatra": result.person_a_nakshatra,
        "person_b_nakshatra": result.person_b_nakshatra,
        "total_score": result.total_score,
        "max_score": result.max_score,
        "kootas": [
            {
                "name": k.name,
                "score": k.score,
                "max_points": k.max_points,
                "description": k.description,
            }
            for k in result.kootas
        ],
        "assessment": result.assessment,
        "assessment_details": result.assessment_details,
        "has_nadi_dosha": result.has_nadi_dosha,
        "has_bhakoot_dosha": result.has_bhakoot_dosha,
    }
