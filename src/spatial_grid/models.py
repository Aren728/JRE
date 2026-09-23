"""Schema and type definitions for the spatial grid engine.

Pure data definitions only: enums, frozen dataclasses, validation and
(de)serialization codecs. No indexing arithmetic lives here (see
``engine.py``) and no I/O of any kind — mirroring the JRE-002 models /
service separation.

Schema conventions follow ``src/astronomy/models.py``: ``StrEnum`` for
JSON-string enums, frozen dataclasses with explicit ``to_dict``/``from_dict``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

#: Schema version stamped into every serialized cell/config. Bump on any
#: change that alters the wire format or the cell-id encoding.
GRID_VERSION: str = "1.0.0"

#: Grid covers latitudes in [-90, 90] and longitudes in [-180, 180).
LAT_MIN: float = -90.0
LAT_MAX: float = 90.0
LON_MIN: float = -180.0
LON_MAX: float = 180.0

#: Number of cells along each axis (fixed 1° schema: 180 rows x 360 columns).
LATITUDE_DIVISIONS: int = 180
LONGITUDE_DIVISIONS: int = 360

#: lon 0..360 wraps to the cell column adjacent to lon -180 (antimeridian).
_LON_COLUMNS: int = LONGITUDE_DIVISIONS - 1  # 359


class CellType(StrEnum):
    """Classification of a grid cell's occupancy."""

    EMPTY = "EMPTY"
    OCCUPIED = "OCCUPIED"
    AGGREGATE = "AGGREGATE"  # cell holds an aggregated/partial payload


@dataclass(frozen=True, order=True)
class CellId:
    """Canonical cell identifier: ``"{GRID_VERSION}:{row}-{col}"`` (1° schema).

    A frozen value object (not an enum: ids are open-ended, one per cell).
    Instances hash and compare by their string value, so they work directly
    as dict keys and sort deterministically.
    """

    value: str

    def cell_row(self) -> int:
        """Row index in [0, 180)."""
        return int(self.value.split(":")[1].split("-")[0])

    def cell_column(self) -> int:
        """Column index in [0, 360)."""
        return int(self.value.split(":")[1].split("-")[1])

    @staticmethod
    def from_indices(row: int, column: int) -> CellId:
        """Build a cell id from grid indices; raises ``ValueError`` out of range."""
        _validate_row(row)
        _validate_column(column)
        return CellId(f"{GRID_VERSION}:{row}-{column}")

    @staticmethod
    def parse(raw: str) -> CellId:
        """Parse and validate a serialized cell id."""
        parts = raw.split(":")
        if len(parts) != 2 or parts[0] != GRID_VERSION:
            raise ValueError(f"cell id {raw!r} does not match grid version {GRID_VERSION!r}")
        indices = parts[1].split("-")
        if len(indices) != 2:
            raise ValueError(f"cell id {raw!r} must encode row-column indices")
        row, column = int(indices[0]), int(indices[1])
        _validate_row(row)
        _validate_column(column)
        return CellId(raw)


def _validate_row(row: int) -> None:
    if not 0 <= row < LATITUDE_DIVISIONS:
        raise ValueError(f"row {row} out of range [0, {LATITUDE_DIVISIONS})")


def _validate_column(column: int) -> None:
    if not 0 <= column < LONGITUDE_DIVISIONS:
        raise ValueError(f"column {column} out of range [0, {LONGITUDE_DIVISIONS})")


@dataclass(frozen=True)
class GridCell:
    """One indexed grid cell.

    ``payload`` is opaque to the engine (the caller's domain data);
    ``point_count`` is maintained by the engine on insertion.
    """

    cell_id: CellId
    row: int
    column: int
    center_latitude: float
    center_longitude: float
    cell_type: CellType = CellType.EMPTY
    point_count: int = 0
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_version": GRID_VERSION,
            "cell_id": self.cell_id.value,
            "row": self.row,
            "column": self.column,
            "center_latitude": self.center_latitude,
            "center_longitude": self.center_longitude,
            "cell_type": self.cell_type.value,
            "point_count": self.point_count,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GridCell:
        version = data.get("grid_version")
        if version is not None and version != GRID_VERSION:
            raise ValueError(f"grid version {version!r} not supported (expected {GRID_VERSION!r})")
        cell_id = CellId.parse(data["cell_id"])
        return cls(
            cell_id=cell_id,
            row=int(data.get("row", cell_id.cell_row())),
            column=int(data.get("column", cell_id.cell_column())),
            center_latitude=float(data["center_latitude"]),
            center_longitude=float(data["center_longitude"]),
            cell_type=CellType(data.get("cell_type", CellType.EMPTY.value)),
            point_count=int(data.get("point_count", 0)),
            payload=data.get("payload"),
        )


@dataclass(frozen=True)
class SpatialGridConfig:
    """Immutable configuration snapshot for the grid engine.

    The v1 schema is a fixed 1° equirectangular grid (180x360). Fields that
    would change the output (origin, cell size, wrapping) are recorded here
    so any future refinement is a versioned decision, never implicit.
    """

    grid_version: str = GRID_VERSION
    cell_size_degrees: float = 1.0
    latitude_divisions: int = LATITUDE_DIVISIONS
    longitude_divisions: int = LONGITUDE_DIVISIONS
    wrap_longitude: bool = True
    allow_out_of_range: bool = False

    def __post_init__(self) -> None:
        if self.cell_size_degrees <= 0:
            raise ValueError("cell_size_degrees must be positive")
        if self.latitude_divisions <= 0 or self.longitude_divisions <= 0:
            raise ValueError("grid divisions must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_version": self.grid_version,
            "cell_size_degrees": self.cell_size_degrees,
            "latitude_divisions": self.latitude_divisions,
            "longitude_divisions": self.longitude_divisions,
            "wrap_longitude": self.wrap_longitude,
            "allow_out_of_range": self.allow_out_of_range,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpatialGridConfig:
        config = cls(
            grid_version=data.get("grid_version", GRID_VERSION),
            cell_size_degrees=float(data.get("cell_size_degrees", 1.0)),
            latitude_divisions=int(data.get("latitude_divisions", LATITUDE_DIVISIONS)),
            longitude_divisions=int(data.get("longitude_divisions", LONGITUDE_DIVISIONS)),
            wrap_longitude=bool(data.get("wrap_longitude", True)),
            allow_out_of_range=bool(data.get("allow_out_of_range", False)),
        )
        if config.grid_version != GRID_VERSION:
            raise ValueError(f"grid version {config.grid_version!r} not supported")
        return config


class SpatialGridSchema:
    """Schema helpers: round-trip codecs and derived type descriptors.

    Kept as a stateless facade (rather than module functions) so consumers
    import one schema/type symbol alongside the engine class.
    """

    @staticmethod
    def encode_cell(cell: GridCell) -> dict[str, Any]:
        """Serialize a cell to its wire representation."""
        return cell.to_dict()

    @staticmethod
    def decode_cell(data: dict[str, Any]) -> GridCell:
        """Validate and deserialize a cell from its wire representation."""
        return GridCell.from_dict(data)

    @staticmethod
    def encode_config(config: SpatialGridConfig) -> dict[str, Any]:
        return config.to_dict()

    @staticmethod
    def decode_config(data: dict[str, Any]) -> SpatialGridConfig:
        return SpatialGridConfig.from_dict(data)

    @staticmethod
    def cell_center(row: int, column: int) -> tuple[float, float]:
        """Center coordinates of a cell: ``(-89.5 + row, -179.5 + column)``."""
        _validate_row(row)
        _validate_column(column)
        return LAT_MIN + 0.5 + row, LON_MIN + 0.5 + column

    @staticmethod
    def normalize_longitude(longitude: float) -> float:
        """Wrap a longitude into [LON_MIN, LON_MAX)."""
        wrapped = (longitude - LON_MIN) % (LON_MAX - LON_MIN) + LON_MIN
        # Map a +180.0 remainder onto the -180 edge so the range is half-open.
        if wrapped >= LON_MAX:
            wrapped -= LON_MAX - LON_MIN
        return wrapped

    @staticmethod
    def column_for_longitude(longitude: float) -> int:
        """Column index in [0, 360) for any longitude, antimeridian-wrapped."""
        normalized = SpatialGridSchema.normalize_longitude(longitude)
        return min(int(normalized - LON_MIN), _LON_COLUMNS)

    @staticmethod
    def row_for_latitude(latitude: float) -> int:
        """Row index in [0, 180) for a latitude in [LAT_MIN, LAT_MAX]."""
        return min(int(latitude - LAT_MIN), LATITUDE_DIVISIONS - 1)
