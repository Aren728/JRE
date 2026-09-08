"""JRE Integrations — Numerology Engine.

Implements the Pythagorean numerology system for calculating:
  - Life Path Number (from birth date)
  - Destiny/Expression Number (from full name)
  - Soul Urge Number (from vowels in name)

All calculations use deterministic integer arithmetic.
No LLM generation — meanings are sourced from lookup dictionaries.

Source: Pythagorean numerology tradition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── Letter-to-Number Mapping (Pythagorean) ───────────────

LETTER_VALUES: dict[str, int] = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "I": 9,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "O": 6,
    "P": 7,
    "Q": 8,
    "R": 9,
    "S": 1,
    "T": 2,
    "U": 3,
    "V": 4,
    "W": 5,
    "X": 6,
    "Y": 7,
    "Z": 8,
}

# Vowels for Soul Urge calculation
VOWELS = set("AEIOU")

# Master numbers (not reduced)
MASTER_NUMBERS = {11, 22, 33}

# ── Life Path Meanings ───────────────────────────────────

LIFE_PATH_MEANINGS: dict[int, str] = {
    1: "A natural leader with strong independence and initiative. You are driven to achieve your goals and inspire others.",
    2: "A diplomatic peacemaker with sensitivity and intuition. You excel in partnerships and bringing harmony.",
    3: "A creative communicator with artistic talent. You express yourself freely and inspire joy in others.",
    4: "A practical builder with strong work ethic. You create stability and order through discipline.",
    5: "An adventurous自由 spirit seeking change and freedom. You embrace life's variety with enthusiasm.",
    6: "A nurturing caregiver with deep sense of responsibility. You bring comfort and healing to others.",
    7: "A spiritual seeker with analytical mind. You pursue truth and wisdom through introspection.",
    8: "A powerful achiever with material success potential. You manifest abundance through determination.",
    9: "A compassionate humanitarian with universal love. You serve others and inspire positive change.",
    11: "A spiritual messenger with heightened intuition. You inspire others through visionary insights.",
    22: "A master builder with great humanitarian vision. You manifest large-scale positive change.",
    33: "A spiritual teacher with unconditional love. You guide others through compassion and wisdom.",
}

# ── Destiny Number Meanings ──────────────────────────────

DESTINY_MEANINGS: dict[int, str] = {
    1: "Your destiny is to lead and innovate. You are meant to pioneer new paths and inspire independence.",
    2: "Your destiny is to cooperate and harmonize. You are meant to build bridges and create peace.",
    3: "Your destiny is to create and express. You are meant to bring joy through art and communication.",
    4: "Your destiny is to build and stabilize. You are meant to create lasting foundations for others.",
    5: "Your destiny is to explore and adapt. You are meant to experience life's diversity and share wisdom.",
    6: "Your destiny is to nurture and heal. You are meant to bring comfort and teach responsibility.",
    7: "Your destiny is to seek truth and wisdom. You are meant to explore the deeper mysteries of life.",
    8: "Your destiny is to achieve and prosper. You are meant to manifest abundance and lead with authority.",
    9: "Your destiny is to serve and inspire. You are meant to uplift humanity through compassion.",
    11: "Your destiny is to inspire and illuminate. You are meant to bring spiritual awakening to others.",
    22: "Your destiny is to build and transform. You are meant to create lasting positive change on a large scale.",
    33: "Your destiny is to teach and heal. You are meant to embody unconditional love and spiritual wisdom.",
}

# ── Soul Urge Meanings ───────────────────────────────────

SOUL_URGE_MEANINGS: dict[int, str] = {
    1: "Your heart desires independence and leadership. You yearn to be recognized for your unique identity.",
    2: "Your heart desires harmony and partnership. You yearn for deep connection and peaceful relationships.",
    3: "Your heart desires creative expression. You yearn to share your ideas and bring joy to others.",
    4: "Your heart desires stability and security. You yearn for a solid foundation and orderly life.",
    5: "Your heart desires freedom and adventure. You yearn for excitement and new experiences.",
    6: "Your heart desires love and family. You yearn to nurture others and create a harmonious home.",
    7: "Your heart desires spiritual understanding. You yearn for inner peace and deeper knowledge.",
    8: "Your heart desires success and recognition. You yearn for achievement and material abundance.",
    9: "Your heart desires to help humanity. You yearn to make a difference and serve a greater cause.",
    11: "Your heart desires spiritual connection. You yearn to inspire others through intuition and insight.",
    22: "Your heart desires to make a lasting impact. You yearn to build something meaningful for humanity.",
    33: "Your heart desires to heal and teach. You yearn to spread love and spiritual wisdom.",
}


# ── Helper Functions ─────────────────────────────────────


def _reduce_to_single(n: int) -> int:
    """Reduce a number to single digit, preserving master numbers."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def _sum_digits(n: int) -> int:
    """Sum all digits of a number."""
    return sum(int(d) for d in str(abs(n)))


def _letter_value(letter: str) -> int:
    """Get numerical value of a letter."""
    return LETTER_VALUES.get(letter.upper(), 0)


# ── Core Calculations ────────────────────────────────────


def _calculate_life_path(birth_date: str) -> int:
    """Calculate Life Path Number from birth date.

    Args:
        birth_date: Date in YYYY-MM-DD format.

    Returns:
        Life Path number (1-9 or master number 11, 22, 33).
    """
    # Parse date components
    parts = birth_date.replace("/", "-").split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {birth_date}. Use YYYY-MM-DD.")

    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])

    # Sum each component
    year_sum = _sum_digits(year)
    month_sum = _sum_digits(month)
    day_sum = _sum_digits(day)

    # Sum all components
    total = year_sum + month_sum + day_sum

    # Reduce to single digit or master number
    return _reduce_to_single(total)


def _calculate_destiny(full_name: str) -> int:
    """Calculate Destiny/Expression Number from full name.

    Args:
        full_name: Full name (first, middle, last).

    Returns:
        Destiny number (1-9 or master number).
    """
    # Sum all letter values
    total = 0
    for char in full_name.upper():
        total += _letter_value(char)

    # Reduce to single digit or master number
    return _reduce_to_single(total)


def _calculate_soul_urge(full_name: str) -> int:
    """Calculate Soul Urge/Heart's Desire Number from vowels in name.

    Args:
        full_name: Full name (first, middle, last).

    Returns:
        Soul Urge number (1-9 or master number).
    """
    # Sum vowel letter values
    total = 0
    for char in full_name.upper():
        if char in VOWELS:
            total += _letter_value(char)

    # Reduce to single digit or master number
    return _reduce_to_single(total)


# ── Data Structures ──────────────────────────────────────


@dataclass
class NumerologyResult:
    """Complete numerology reading result."""

    birth_date: str
    full_name: str
    life_path: int
    life_path_meaning: str
    destiny: int
    destiny_meaning: str
    soul_urge: int
    soul_urge_meaning: str


# ── Main Function ─────────────────────────────────────────


def calculate_numerology(
    birth_date: str,
    full_name: str,
) -> NumerologyResult:
    """Calculate numerology numbers from birth date and name.

    Uses the Pythagorean system (A=1, B=2, ..., I=9, J=1, ...).

    Args:
        birth_date: Date in YYYY-MM-DD format (e.g., "1990-05-15").
        full_name: Full name including first, middle, and last names.

    Returns:
        NumerologyResult with Life Path, Destiny, and Soul Urge numbers.

    Raises:
        ValueError: If date format is invalid or name is empty.
    """
    # Validate inputs
    if not full_name or not full_name.strip():
        raise ValueError("Full name cannot be empty.")

    # Clean name (remove extra spaces)
    clean_name = " ".join(full_name.strip().split())

    # Calculate numbers
    life_path = _calculate_life_path(birth_date)
    destiny = _calculate_destiny(clean_name)
    soul_urge = _calculate_soul_urge(clean_name)

    # Get meanings
    life_path_meaning = LIFE_PATH_MEANINGS.get(life_path, "A unique spiritual path.")
    destiny_meaning = DESTINY_MEANINGS.get(destiny, "A unique destiny awaits.")
    soul_urge_meaning = SOUL_URGE_MEANINGS.get(soul_urge, "A unique heart's desire.")

    return NumerologyResult(
        birth_date=birth_date,
        full_name=clean_name,
        life_path=life_path,
        life_path_meaning=life_path_meaning,
        destiny=destiny,
        destiny_meaning=destiny_meaning,
        soul_urge=soul_urge,
        soul_urge_meaning=soul_urge_meaning,
    )


def numerology_to_dict(result: NumerologyResult) -> dict[str, Any]:
    """Convert NumerologyResult to JSON-serializable dict.

    Args:
        result: NumerologyResult from calculate_numerology.

    Returns:
        JSON-serializable dictionary.
    """
    return {
        "birth_date": result.birth_date,
        "full_name": result.full_name,
        "life_path": {
            "number": result.life_path,
            "meaning": result.life_path_meaning,
        },
        "destiny": {
            "number": result.destiny,
            "meaning": result.destiny_meaning,
        },
        "soul_urge": {
            "number": result.soul_urge,
            "meaning": result.soul_urge_meaning,
        },
    }
