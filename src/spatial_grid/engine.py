"""Indexing arithmetic for the spatial grid engine.

Owns the mutation-free index math (point -> cell mapping, neighbor
enumeration) plus the point-buffer bookkeeping. Pure data lives in
``models.py`` — this module only orchestrates it, mirroring the JRE-002
models/service separation.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .models import (
    GRID_VERSION,
    LON_MAX,
    LON_MIN,
    CellId,
    CellType,
    GridCell,
    SpatialGridConfig,
    SpatialGridSchema,
)


class SpatialGridEngine:
    """Fixed 1° equirectangular grid: insert points, resolve cells, walk neighbors.

    A fresh engine starts EMPTY everywhere; the first insertion promotes a
    cell to OCCUPIED and maintains its ``point_count``. Aggregation payloads
    (``CellType.AGGREGATE``) may be attached by callers carrying domain data.
    """

    def __init__(self, config: SpatialGridConfig | None = None) -> None:
        self._config = config if config is not None else SpatialGridConfig()
        if self._config.grid_version != GRID_VERSION:
            raise ValueError(
                f"grid version {self._config.grid_version!r} not supported "
                f"(expected {GRID_VERSION!r})"
            )
        if not self._config.wrap_longitude:
            raise NotImplementedError("non-wrapping longitude schema is deferred (v1 wraps)")
        self._points: dict[CellId, list[tuple[float, float]]] = {}
        self._payloads: dict[CellId, dict[str, Any]] = {}
        self._aggregates: set[CellId] = set()

    # -- properties -----------------------------------------------------

    @property
    def config(self) -> SpatialGridConfig:
        return self._config

    def __len__(self) -> int:
        """Number of occupied cells."""
        return len(self._points)

    # -- insertion ------------------------------------------------------

    def insert_point(
        self,
        latitude: float,
        longitude: float,
        payload: dict[str, Any] | None = None,
    ) -> CellId:
        """Insert a point; returns the cell id it landed in.

        Raises ``ValueError`` for out-of-range coordinates unless the config
        allows them (in which case they are clamped to the edge cells).
        """
        row, column = self._indices_for(latitude, longitude)
        cell_id = CellId.from_indices(row, column)
        self._points.setdefault(cell_id, []).append((latitude, longitude))
        if payload:
            self._payloads[cell_id] = payload
        return cell_id

    def mark_aggregate(self, cell_id: CellId, payload: dict[str, Any] | None = None) -> None:
        """Promote a cell to AGGREGATE (it carries an aggregated/partial payload)."""
        if cell_id not in self._points:
            self._points[cell_id] = []
        self._aggregates.add(cell_id)
        if payload:
            self._payloads[cell_id] = payload

    # -- lookup ---------------------------------------------------------

    def cell_for(self, latitude: float, longitude: float) -> GridCell:
        """Materialized cell (with occupancy state) for the given coordinates."""
        row, column = self._indices_for(latitude, longitude)
        return self._materialize(CellId.from_indices(row, column))

    def get_cell(self, cell_id: CellId) -> GridCell:
        """Materialized cell for a known id."""
        return self._materialize(cell_id)

    def neighbor_cells(self, row: int, column: int) -> tuple[GridCell, ...]:
        """The 8 surrounding cells, dropping those off the pole edges.

        Longitude neighbors wrap across the antimeridian.
        """
        neighbors: list[GridCell] = []
        for d_row in (-1, 0, 1):
            for d_column in (-1, 0, 1):
                if d_row == 0 and d_column == 0:
                    continue
                n_row = row + d_row
                if not 0 <= n_row < self._config.latitude_divisions:
                    continue
                n_column = (column + d_column) % self._config.longitude_divisions
                neighbors.append(self._materialize(CellId.from_indices(n_row, n_column)))
        return tuple(neighbors)

    def occupied_cells(self) -> tuple[GridCell, ...]:
        """All OCCUPIED/AGGREGATE cells, ordered row-major (numeric row, then column)."""
        cells = [
            self._materialize(cell_id)
            for cell_id in sorted(self._points, key=lambda c: (c.cell_row(), c.cell_column()))
        ]
        return tuple(cells)

    def iter_cells(self) -> Iterator[GridCell]:
        """Row-major iteration over every cell in the grid (64800 total)."""
        for row in range(self._config.latitude_divisions):
            for column in range(self._config.longitude_divisions):
                yield self._materialize(CellId.from_indices(row, column))

    def to_dict(self) -> dict[str, Any]:
        """Wire snapshot: config plus every non-empty cell."""
        return {
            "config": self._config.to_dict(),
            "cells": [
                self._materialize(cell_id).to_dict()
                for cell_id in sorted(self._points, key=lambda c: (c.cell_row(), c.cell_column()))
            ],
        }

    # -- internals ------------------------------------------------------

    def _indices_for(self, latitude: float, longitude: float) -> tuple[int, int]:
        if not -90.0 <= latitude <= 90.0:
            if not self._config.allow_out_of_range:
                raise ValueError(f"latitude {latitude} out of range [-90, 90]")
            latitude = min(max(latitude, -90.0), 90.0)
        if not LON_MIN <= longitude < LON_MAX:
            if not self._config.allow_out_of_range:
                raise ValueError(f"longitude {longitude} out of range [-180, 180)")
            longitude = SpatialGridSchema.normalize_longitude(longitude)
        row = SpatialGridSchema.row_for_latitude(latitude)
        column = SpatialGridSchema.column_for_longitude(longitude)
        return row, column

    def _materialize(self, cell_id: CellId) -> GridCell:
        points = self._points.get(cell_id)
        row, column = cell_id.cell_row(), cell_id.cell_column()
        center_lat, center_lon = SpatialGridSchema.cell_center(row, column)
        if cell_id in self._aggregates:
            cell_type = CellType.AGGREGATE
        elif points:
            cell_type = CellType.OCCUPIED
        else:
            cell_type = CellType.EMPTY
        return GridCell(
            cell_id=cell_id,
            row=cell_id.cell_row(),
            column=cell_id.cell_column(),
            center_latitude=center_lat,
            center_longitude=center_lon,
            cell_type=cell_type,
            point_count=len(points) if points else 0,
            payload=self._payloads.get(cell_id),
        )
