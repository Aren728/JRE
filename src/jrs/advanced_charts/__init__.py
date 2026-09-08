"""JRE Advanced Charts — Divisional Charts, Shadbala, and Ashtakavarga engines.

Public API:

Divisional Charts:
  compute_divisional_chart  — Compute a single divisional chart
  compute_all_divisional_charts — Compute multiple divisional charts
  divisional_chart_to_dict  — Serialize DivisionalChart to dict
  DivisionalChart          — Data class for a complete divisional chart
  DivisionalPlanet         — Data class for planet position in a division
  CHART_META               — Metadata for all supported divisions

Shadbala:
  calculate_shadbala       — Calculate Shadbala from JRE facts packet (adapter)
  compute_shadbala         — Compute six-fold strength for all planets
  shadbala_to_dict         — Serialize ShadbalaResult to dict
  PlanetStrength           — Data class for a single planet's strength
  ShadbalaResult           — Data class for complete Shadbala result

Ashtakavarga:
  calculate_ashtakavarga   — Calculate Ashtakavarga from JRE facts packet (adapter)
  compute_ashtakavarga     — Compute BAV and SAV for all planets
  ashtakavarga_to_dict     — Serialize AshtakavargaResult to dict
  BAVResult                — Data class for Bhinna Ashtakavarga result
  AshtakavargaResult       — Data class for complete Ashtakavarga result

Divisional Charts:
  calculate_divisional_positions — Calculate divisional positions from JRE facts (adapter)
  compute_divisional_chart  — Compute a single divisional chart
  compute_all_divisional_charts — Compute multiple divisional charts
  divisional_chart_to_dict  — Serialize DivisionalChart to dict
  DivisionalChart          — Data class for a complete divisional chart
  DivisionalPlanet         — Data class for planet position in a division
  CHART_META               — Metadata for all supported divisions
"""

from __future__ import annotations

from .ashtakavarga import (
    AshtakavargaResult,
    BAVResult,
    ashtakavarga_to_dict,
    calculate_ashtakavarga,
    compute_ashtakavarga,
)
from .divisional import (
    CHART_META,
    DivisionalChart,
    DivisionalPlanet,
    calculate_divisional_positions,
    compute_all_divisional_charts,
    compute_divisional_chart,
    divisional_chart_to_dict,
)
from .shadbala import (
    PlanetStrength,
    ShadbalaResult,
    calculate_shadbala,
    compute_shadbala,
    shadbala_to_dict,
)

__all__ = [
    # Divisional Charts
    "calculate_divisional_positions",
    "compute_divisional_chart",
    "compute_all_divisional_charts",
    "divisional_chart_to_dict",
    "DivisionalChart",
    "DivisionalPlanet",
    "CHART_META",
    # Shadbala
    "calculate_shadbala",
    "compute_shadbala",
    "shadbala_to_dict",
    "PlanetStrength",
    "ShadbalaResult",
    # Ashtakavarga
    "calculate_ashtakavarga",
    "compute_ashtakavarga",
    "ashtakavarga_to_dict",
    "BAVResult",
    "AshtakavargaResult",
]
