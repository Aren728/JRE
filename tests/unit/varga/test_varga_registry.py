"""Registry integrity tests (normative specification §19-§20).

The frozen 14-varga catalog: per-varga versioned method identities (never
one generic ``parashara-v1``), D20 carries two distinct methods that never
merge, D27 is absent, D30 is the explicit unequal table, D60 is the
explicit BPHS remainder method.
"""

from __future__ import annotations

import pytest

from varga import (
    VARGA_IDS,
    BoundaryConvention,
    ExplicitTableParams,
    FixedStartParams,
    MappingStrategy,
    ModalityStartParams,
    OddEvenStartParams,
    RelativeModalityParams,
    SubdivisionStrategy,
    VargaCalculationMethod,
    VargaDefinition,
    available_method_ids,
    canonical_method_id,
    get_varga_definition,
)
from varga.errors import InvalidVargaRequestError

V1_EXPECTED = {
    "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
    "D20", "D24", "D30", "D40", "D45", "D60",
}

#: varga_id -> (division count, subdivision strategy, mapping strategy)
EXPECTED_ARCHITECTURE: dict[str, tuple[int, SubdivisionStrategy, MappingStrategy]] = {
    "D2": (2, SubdivisionStrategy.UNIFORM, MappingStrategy.SPECIALIZED),
    "D3": (3, SubdivisionStrategy.UNIFORM, MappingStrategy.TRINAL_SEQUENCE),
    "D4": (4, SubdivisionStrategy.UNIFORM, MappingStrategy.KENDRA_SEQUENCE),
    "D7": (7, SubdivisionStrategy.UNIFORM, MappingStrategy.ODD_EVEN_START),
    "D9": (9, SubdivisionStrategy.UNIFORM, MappingStrategy.MODALITY_START),
    "D10": (10, SubdivisionStrategy.UNIFORM, MappingStrategy.ODD_EVEN_START),
    "D12": (12, SubdivisionStrategy.UNIFORM, MappingStrategy.SELF_SEQUENCE),
    "D16": (16, SubdivisionStrategy.UNIFORM, MappingStrategy.MODALITY_START),
    "D20": (20, SubdivisionStrategy.UNIFORM, MappingStrategy.MODALITY_START),
    "D24": (24, SubdivisionStrategy.UNIFORM, MappingStrategy.ODD_EVEN_START),
    "D30": (30, SubdivisionStrategy.UNEQUAL_TABLE, MappingStrategy.EXPLICIT_TABLE),
    "D40": (40, SubdivisionStrategy.UNIFORM, MappingStrategy.ODD_EVEN_START),
    "D45": (45, SubdivisionStrategy.UNIFORM, MappingStrategy.MODALITY_START),
    "D60": (60, SubdivisionStrategy.SPECIALIZED, MappingStrategy.SPECIALIZED),
}


def test_v1_scope_and_definitions() -> None:
    assert set(VARGA_IDS) == V1_EXPECTED
    for varga_id in V1_EXPECTED:
        definition = get_varga_definition(varga_id)
        assert isinstance(definition, VargaDefinition)
        assert definition.varga_id == varga_id
        divisions, subdivision, mapping = EXPECTED_ARCHITECTURE[varga_id]
        assert definition.division_number == divisions
        assert definition.calculation_method.subdivision_strategy is subdivision
        assert definition.calculation_method.mapping_strategy is mapping
        assert definition.boundary_convention is BoundaryConvention.HALF_OPEN_LOW
        assert definition.calculation_method.boundary_convention is (
            BoundaryConvention.HALF_OPEN_LOW
        )


def test_method_identities_are_varga_specific() -> None:
    for varga_id in V1_EXPECTED:
        method = get_varga_definition(varga_id).calculation_method
        assert isinstance(method, VargaCalculationMethod)
        # No generic single identifier covering every varga.
        assert method.method_id != "parashara-v1"
        assert method.method_id.startswith(varga_id.lower())
        assert method.applicable_varga == varga_id
        assert method.source_references  # every method is source-cited
        assert canonical_method_id(varga_id) == method.method_id
        assert method.method_id in available_method_ids(varga_id)


def test_boundary_convention_frozen() -> None:
    for varga_id in V1_EXPECTED:
        assert (
            get_varga_definition(varga_id).boundary_convention
            is BoundaryConvention.HALF_OPEN_LOW
        )


def test_d9_relative_modality() -> None:
    params = get_varga_definition("D9").calculation_method.mapping_parameters
    assert isinstance(params, RelativeModalityParams)
    assert (params.movable_offset, params.fixed_offset, params.dual_offset) == (0, 8, 4)


def test_d16_d45_absolute_modality() -> None:
    for varga_id in ("D16", "D45"):
        params = get_varga_definition(varga_id).calculation_method.mapping_parameters
        assert isinstance(params, ModalityStartParams)
        assert params.movable_start.value == "MESHA"
        assert params.fixed_start.value == "SIMHA"
        assert params.dual_start.value == "DHANUSHA"


def test_d20_bphs_absolute_modality() -> None:
    params = get_varga_definition("D20").calculation_method.mapping_parameters
    assert isinstance(params, ModalityStartParams)
    # BPHS (Sanskrit): cara -> Aries, sthira -> Sagittarius, dvisvabhava -> Leo.
    assert params.movable_start.value == "MESHA"
    assert params.fixed_start.value == "DHANUSHA"
    assert params.dual_start.value == "SIMHA"


def test_d20_two_distinct_methods_never_merged() -> None:
    ids = available_method_ids("D20")
    assert "d20-bphs-v1" in ids
    assert "d20-saravali-variant-v1" in ids
    assert canonical_method_id("D20") == "d20-bphs-v1"
    canonical = get_varga_definition("D20", "d20-bphs-v1")
    variant = get_varga_definition("D20", "d20-saravali-variant-v1")
    assert canonical.calculation_method.method_id == "d20-bphs-v1"
    assert variant.calculation_method.method_id == "d20-saravali-variant-v1"
    # Distinct methods must produce distinct definition identities.
    assert canonical.to_dict() != variant.to_dict()


def test_d7_d10_relative_odd_even_offsets() -> None:
    for varga_id, odd, even in (("D7", 0, 6), ("D10", 0, 8)):
        params = get_varga_definition(varga_id).calculation_method.mapping_parameters
        assert isinstance(params, OddEvenStartParams)
        assert params.odd_offset == odd
        assert params.even_offset == even
        assert params.odd_start is None and params.even_start is None


def test_d24_d40_absolute_odd_even_starts() -> None:
    starts = {
        "D24": ("SIMHA", "KARKA"),
        "D40": ("MESHA", "TULA"),
    }
    for varga_id, (odd, even) in starts.items():
        params = get_varga_definition(varga_id).calculation_method.mapping_parameters
        assert isinstance(params, OddEvenStartParams)
        assert params.odd_start.value == odd
        assert params.even_start.value == even
        assert params.odd_offset is None and params.even_offset is None


def test_d2_hora_fixed_pair() -> None:
    params = get_varga_definition("D2").calculation_method.mapping_parameters
    assert isinstance(params, FixedStartParams)
    assert params.hora is True
    assert params.odd_start.value == "SIMHA"
    assert params.even_start.value == "KARKA"


def test_d12_self_sequence() -> None:
    params = get_varga_definition("D12").calculation_method.mapping_parameters
    assert isinstance(params, FixedStartParams)
    assert params.self_start is True


def test_d30_explicit_unequal_table() -> None:
    params = get_varga_definition("D30").calculation_method.mapping_parameters
    assert isinstance(params, ExplicitTableParams)
    odd_bounds = [(band.lower_deg, band.upper_deg) for band in params.odd_bands]
    even_bounds = [(band.lower_deg, band.upper_deg) for band in params.even_bands]
    # BPHS v.27-28 + Speculum of Trimsamsas: 5 / 5 / 8 / 7 / 5.
    assert odd_bounds == [
        (0.0, 5.0), (5.0, 10.0), (10.0, 18.0), (18.0, 25.0), (25.0, 30.0),
    ]
    assert even_bounds == [
        (0.0, 5.0), (5.0, 12.0), (12.0, 20.0), (20.0, 25.0), (25.0, 30.0),
    ]
    assert [band.destination.value for band in params.odd_bands] == [
        "MESHA", "KUMBHA", "DHANUSHA", "MITHUNA", "TULA",
    ]
    assert [band.destination.value for band in params.even_bands] == [
        "VRISHABHA", "KANYA", "MEENA", "MAKARA", "VRISHCHIKA",
    ]


def test_d60_specialized_remainder() -> None:
    params = get_varga_definition("D60").calculation_method.mapping_parameters
    assert isinstance(params, FixedStartParams)
    assert params.remainder is True


def test_unknown_varga_id_rejected() -> None:
    with pytest.raises(InvalidVargaRequestError):
        get_varga_definition("D27")
    with pytest.raises(InvalidVargaRequestError):
        get_varga_definition("D5")
    with pytest.raises(InvalidVargaRequestError):
        get_varga_definition("BOGUS")


def test_unknown_method_id_rejected() -> None:
    with pytest.raises(InvalidVargaRequestError):
        get_varga_definition("D9", "d9-bogus-v1")
    # D20 variants are not valid for other vargas.
    with pytest.raises(InvalidVargaRequestError):
        get_varga_definition("D9", "d20-bphs-v1")


def test_registry_immutable() -> None:
    import dataclasses

    from varga import VARGA_REGISTRY

    # Mapping is a read-only proxy: item assignment is rejected.
    with pytest.raises(TypeError):
        VARGA_REGISTRY["D2"] = get_varga_definition("D2")  # type: ignore[index]
    # Definitions and methods are frozen dataclasses.
    with pytest.raises(dataclasses.FrozenInstanceError):
        get_varga_definition("D2").calculation_method.method_id = "hijacked"  # type: ignore[misc]
