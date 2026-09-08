"""JRE Compatibility — Ashta Koota Matching Engine.

Public API:

  calculate_ashta_koota — Calculate 8-factor compatibility
  ashta_koota_to_dict   — Serialize AshtaKootaResult to dict
  KootaResult           — Data class for single Koota factor
  AshtaKootaResult      — Data class for complete result
"""

from .ashta_koota import (
    AshtaKootaResult,
    KootaResult,
    ashta_koota_to_dict,
    calculate_ashta_koota,
)

__all__ = [
    "calculate_ashta_koota",
    "ashta_koota_to_dict",
    "KootaResult",
    "AshtaKootaResult",
]
