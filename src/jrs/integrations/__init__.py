"""JRE Integrations — Numerology and other integrations.

Public API:

  calculate_numerology — Calculate numerology from birth date and name
  numerology_to_dict   — Serialize NumerologyResult to dict
  NumerologyResult     — Data class for numerology result
"""

from .numerology import (
    NumerologyResult,
    calculate_numerology,
    numerology_to_dict,
)

__all__ = [
    "calculate_numerology",
    "numerology_to_dict",
    "NumerologyResult",
]
