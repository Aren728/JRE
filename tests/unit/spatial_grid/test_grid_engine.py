"""Tests for the spatial grid engine (schema + indexing arithmetic)."""

from __future__ import annotations

import pytest

from spatial_grid import (
    GRID_VERSION,
    CellId,
    CellType,
    GridCell,
    SpatialGridConfig,
    SpatialGridEngine,
    SpatialGridSchema,
)

# --------------------------------------------------------------------------- #
# CellId
# --------------------------------------------------------------------------- #


class TestCellId:
    def test_from_indices_format(self) -> None:
        assert CellId.from_indices(0, 0).value == f"{GRID_VERSION}:0-0"
        assert CellId.from_indices(118, 257).value == f"{GRID_VERSION}:118-257"

    def test_indices_round_trip(self) -> None:
        cid = CellId.from_indices(42, 359)
        assert cid.cell_row() == 42
        assert cid.cell_column() == 359

    def test_parse_valid(self) -> None:
        cid = CellId.parse(f"{GRID_VERSION}:7-11")
        assert (cid.cell_row(), cid.cell_column()) == (7, 11)

    def test_parse_rejects_wrong_version(self) -> None:
        with pytest.raises(ValueError, match="grid version"):
            CellId.parse("9.9.9:0-0")

    def test_parse_rejects_bad_shape(self) -> None:
        with pytest.raises(ValueError):
            CellId.parse(f"{GRID_VERSION}:1-2-3")
        with pytest.raises(ValueError):
            CellId.parse("no-colon")

    def test_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="row"):
            CellId.from_indices(180, 0)
        with pytest.raises(ValueError, match="column"):
            CellId.from_indices(0, 360)
        with pytest.raises(ValueError):
            CellId.from_indices(-1, 0)

    def test_hashable_and_sortable(self) -> None:
        ids = {CellId.from_indices(1, 1), CellId.from_indices(1, 1), CellId.from_indices(0, 0)}
        assert len(ids) == 2
        assert sorted(ids)[0] == CellId.from_indices(0, 0)


# --------------------------------------------------------------------------- #
# GridCell / SpatialGridConfig codecs
# --------------------------------------------------------------------------- #


class TestGridCellCodec:
    def test_round_trip(self) -> None:
        cell = GridCell(
            cell_id=CellId.from_indices(10, 20),
            row=10,
            column=20,
            center_latitude=-79.5,
            center_longitude=-159.5,
            cell_type=CellType.OCCUPIED,
            point_count=3,
            payload={"city": "Delhi"},
        )
        data = cell.to_dict()
        assert data["grid_version"] == GRID_VERSION
        restored = GridCell.from_dict(data)
        assert restored == cell

    def test_from_dict_rejects_version_mismatch(self) -> None:
        data = GridCell(
            cell_id=CellId.from_indices(0, 0),
            row=0,
            column=0,
            center_latitude=-89.5,
            center_longitude=-179.5,
        ).to_dict()
        data["grid_version"] = "0.0.1"
        with pytest.raises(ValueError, match="not supported"):
            GridCell.from_dict(data)


class TestSpatialGridConfig:
    def test_defaults(self) -> None:
        config = SpatialGridConfig()
        assert config.grid_version == GRID_VERSION == "1.0.0"
        assert config.cell_size_degrees == 1.0
        assert (config.latitude_divisions, config.longitude_divisions) == (180, 360)
        assert config.wrap_longitude is True

    def test_round_trip(self) -> None:
        config = SpatialGridConfig()
        assert SpatialGridConfig.from_dict(config.to_dict()) == config

    def test_invalid_cell_size(self) -> None:
        with pytest.raises(ValueError):
            SpatialGridConfig(cell_size_degrees=0.0)


# --------------------------------------------------------------------------- #
# SpatialGridSchema helpers
# --------------------------------------------------------------------------- #


class TestSpatialGridSchema:
    def test_cell_centers(self) -> None:
        assert SpatialGridSchema.cell_center(0, 0) == (-89.5, -179.5)
        assert SpatialGridSchema.cell_center(179, 359) == (89.5, 179.5)
        assert SpatialGridSchema.cell_center(118, 257) == (28.5, 77.5)  # Delhi (28.6N) cell center

    def test_center_round_trip(self) -> None:
        for row, column in ((0, 0), (89, 179), (118, 257), (179, 359)):
            lat, lon = SpatialGridSchema.cell_center(row, column)
            assert SpatialGridSchema.row_for_latitude(lat) == row
            assert SpatialGridSchema.column_for_longitude(lon) == column

    def test_normalize_longitude(self) -> None:
        assert SpatialGridSchema.normalize_longitude(0.0) == 0.0
        assert SpatialGridSchema.normalize_longitude(180.0) == -180.0
        assert SpatialGridSchema.normalize_longitude(-180.0) == -180.0
        assert SpatialGridSchema.normalize_longitude(190.0) == -170.0
        assert SpatialGridSchema.normalize_longitude(-190.0) == 170.0
        assert SpatialGridSchema.normalize_longitude(720.0) == 0.0

    def test_column_for_longitude(self) -> None:
        # The [-1, 0) band is column 179 (adjacent to Greenwich, not the dateline).
        assert SpatialGridSchema.column_for_longitude(-1.0) == 179
        assert SpatialGridSchema.column_for_longitude(-0.25) == 179
        assert SpatialGridSchema.column_for_longitude(0.0) == 180
        assert SpatialGridSchema.column_for_longitude(179.5) == 359
        assert SpatialGridSchema.column_for_longitude(-179.5) == 0
        assert SpatialGridSchema.column_for_longitude(78.5) == 258

    def test_row_for_latitude(self) -> None:
        assert SpatialGridSchema.row_for_latitude(-90.0) == 0
        assert SpatialGridSchema.row_for_latitude(28.6) == 118
        assert SpatialGridSchema.row_for_latitude(90.0) == 179  # clamped edge

    def test_schema_codecs(self) -> None:
        config = SpatialGridConfig()
        assert SpatialGridSchema.decode_config(SpatialGridSchema.encode_config(config)) == config
        cell = GridCell(
            cell_id=CellId.from_indices(5, 5),
            row=5,
            column=5,
            center_latitude=-84.5,
            center_longitude=-174.5,
        )
        assert SpatialGridSchema.decode_cell(SpatialGridSchema.encode_cell(cell)) == cell


# --------------------------------------------------------------------------- #
# SpatialGridEngine
# --------------------------------------------------------------------------- #


class TestSpatialGridEngine:
    def test_fresh_engine_is_empty(self) -> None:
        engine = SpatialGridEngine()
        assert len(engine) == 0
        cell = engine.cell_for(10.0, 10.0)
        assert cell.cell_type == CellType.EMPTY
        assert cell.point_count == 0

    def test_insert_and_count(self) -> None:
        engine = SpatialGridEngine()
        cid = engine.insert_point(28.6, 77.2, payload={"city": "Delhi"})
        assert cid == CellId.from_indices(118, 257)
        assert len(engine) == 1
        cell = engine.get_cell(cid)
        assert cell.cell_type == CellType.OCCUPIED
        assert cell.point_count == 1
        assert cell.payload == {"city": "Delhi"}

    def test_multiple_points_same_cell(self) -> None:
        engine = SpatialGridEngine()
        engine.insert_point(28.61, 77.21)
        engine.insert_point(28.62, 77.22)
        cid = engine.insert_point(28.63, 77.23)
        assert engine.get_cell(cid).point_count == 3
        assert len(engine) == 1

    def test_cell_for_matches_insert(self) -> None:
        engine = SpatialGridEngine()
        cid = engine.insert_point(-33.87, 151.21)  # Sydney
        assert engine.cell_for(-33.9, 151.25).cell_id == cid

    def test_out_of_range_rejected(self) -> None:
        engine = SpatialGridEngine()
        with pytest.raises(ValueError, match="latitude"):
            engine.insert_point(91.0, 0.0)
        with pytest.raises(ValueError, match="longitude"):
            engine.insert_point(0.0, 180.0)  # half-open upper edge

    def test_clamped_mode(self) -> None:
        engine = SpatialGridEngine(SpatialGridConfig(allow_out_of_range=True))
        cid = engine.insert_point(95.0, 200.0)
        assert cid == CellId.from_indices(179, 20)

    def test_antimeridian_edges(self) -> None:
        engine = SpatialGridEngine()
        # -180 is the in-range edge of column 0.
        assert engine.cell_for(0.0, -180.0).column == 0
        # +180 is outside the half-open range; schema-level wrap maps it there.
        assert SpatialGridSchema.column_for_longitude(180.0) == 0
        with pytest.raises(ValueError, match="longitude"):
            engine.insert_point(0.0, 180.0)

    def test_occupied_cells_row_major(self) -> None:
        engine = SpatialGridEngine()
        engine.insert_point(10.0, 10.0)
        engine.insert_point(-10.0, -10.0)
        engine.insert_point(0.0, 0.0)
        cells = engine.occupied_cells()
        assert cells[0].center_latitude == pytest.approx(-9.5, abs=1e-9)
        assert cells[-1].center_latitude == pytest.approx(10.5, abs=1e-9)

    def test_occupied_cells_row_major_numeric_not_lexicographic(self) -> None:
        # Regression: string-sorted ids put row 100 before row 90 —
        # ordering must be numeric row-major.
        engine = SpatialGridEngine()
        engine.insert_point(0.0, 0.0)  # row 90
        engine.insert_point(10.0, 0.0)  # row 100
        cells = engine.occupied_cells()
        assert [c.row for c in cells] == [90, 100]

    def test_snapshot_round_trip(self) -> None:
        engine = SpatialGridEngine()
        engine.insert_point(28.6, 77.2, payload={"city": "Delhi"})
        engine.mark_aggregate(CellId.from_indices(50, 50), payload={"aggregate": True})
        snap = engine.to_dict()
        assert snap["config"]["grid_version"] == GRID_VERSION
        assert len(snap["cells"]) == 2
        # Both occupied and aggregate cells materialize from the snapshot ids.
        restored = [GridCell.from_dict(c) for c in snap["cells"]]
        assert {c.cell_id for c in restored} == {
            CellId.from_indices(118, 257),
            CellId.from_indices(50, 50),
        }

    def test_neighbor_count_by_position(self) -> None:
        engine = SpatialGridEngine()
        assert len(engine.neighbor_cells(5, 5)) == 8
        assert len(engine.neighbor_cells(0, 5)) == 5  # south pole edge row
        assert len(engine.neighbor_cells(179, 5)) == 5  # north pole edge row

    def test_neighbor_longitude_wraps_across_antimeridian(self) -> None:
        engine = SpatialGridEngine()
        neighbors = engine.neighbor_cells(45, 0)
        west = next(c for c in neighbors if c.column == 359)
        assert west.cell_id == CellId.from_indices(44, 359)

    def test_aggregate_promotion(self) -> None:
        engine = SpatialGridEngine()
        cid = CellId.from_indices(30, 30)
        engine.mark_aggregate(cid)
        assert engine.get_cell(cid).cell_type == CellType.AGGREGATE
        assert engine.get_cell(cid).point_count == 0

    def test_iter_cells_is_row_major_full(self) -> None:
        engine = SpatialGridEngine()
        it = engine.iter_cells()
        first, second = next(it), next(it)
        assert first == GridCell(
            cell_id=CellId.from_indices(0, 0),
            row=0,
            column=0,
            center_latitude=-89.5,
            center_longitude=-179.5,
        )
        assert second.column == 1

    def test_config_version_enforced(self) -> None:
        with pytest.raises(ValueError, match="not supported"):
            SpatialGridEngine(SpatialGridConfig(grid_version="0.9.0"))
