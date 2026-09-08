"""JRE Parihara — Remedies Engine.

Public API:

  generate_remedies  — Generate classical Vedic remedies from JRE facts
  remedy_to_dict     — Serialize RemedyResult to dict
  PlanetRemedy       — Data class for single planet remedy
  RemedyResult       — Data class for complete remedy result
"""

from .remedy_engine import (
    PlanetRemedy,
    RemedyResult,
    generate_remedies,
    remedy_to_dict,
)

__all__ = [
    "generate_remedies",
    "remedy_to_dict",
    "PlanetRemedy",
    "RemedyResult",
]
