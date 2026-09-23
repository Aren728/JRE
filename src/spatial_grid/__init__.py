"""Spatial grid engine (spatial indexing for geospatial and celestial queries).

Public API:
- ``SpatialGridConfig`` — immutable grid configuration (schema)
- ``SpatialGridSchema`` — schema/type definitions (grid cell model, codecs)
- ``SpatialGridEngine`` — point insertion, cell lookup and cell enumeration
"""

from __future__ import annotations

from .engine import SpatialGridEngine
from .models import (
    GRID_VERSION,
    CellId,
    CellType,
    GridCell,
    SpatialGridConfig,
    SpatialGridSchema,
)

__all__ = [
    "GRID_VERSION",
    "CellId",
    "CellType",
    "GridCell",
    "SpatialGridConfig",
    "SpatialGridEngine",
    "SpatialGridSchema",
]
