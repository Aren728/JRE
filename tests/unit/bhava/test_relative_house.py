"""Relative-house tests (TEST-PLAN §11/§5, SPEC §11, ADR-014)."""

from __future__ import annotations

from bhava import derive_house_analysis, relative_house
from jyotish import BodyId, TransitReferencePoint


def test_formula_pinned() -> None:
    assert relative_house(1, 1) == 1
    assert relative_house(2, 1) == 2
    assert relative_house(6, 1) == 6
    assert relative_house(1, 6) == 8  # ((1-6) mod 12) + 1 = (-5 mod 12) + 1 = 8
    assert relative_house(6, 6) == 1
    assert relative_house(12, 12) == 1


def test_relative_house_from_lagna_equals_absolute(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    table = analysis.relative_house_table
    absolute = {fact.body: fact.house_number for fact in analysis.planet_house_facts}
    for body, house in absolute.items():
        assert table["LAGNA"][body.value] == house


def test_asc_equals_lagna_rows(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    assert analysis.relative_house_table["ASC"] == analysis.relative_house_table["LAGNA"]


def test_reference_order_pinned(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    assert list(analysis.relative_house_table) == ["LAGNA", "MOON", "SUN", "ASC"]
    for row in analysis.relative_house_facts:
        assert isinstance(row.reference, TransitReferencePoint)


def test_reference_absolute_house(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_key = {(row.body, row.reference): row for row in analysis.relative_house_facts}
    assert by_key[(BodyId.SUN, TransitReferencePoint.LAGNA)].reference_absolute_house == 1
    assert by_key[(BodyId.SUN, TransitReferencePoint.ASC)].reference_absolute_house == 1
    # MOON is in house 2.
    assert by_key[(BodyId.SUN, TransitReferencePoint.MOON)].reference_absolute_house == 2


def test_relative_house_moon_anchor(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    table = analysis.relative_house_table["MOON"]
    # SUN house 1, MOON house 2 → relative_house(SUN, MOON) = ((1-2) mod 12)+1 = 12.
    assert table["SUN"] == 12
    assert table["MOON"] == 1
    # MARS house 3 → ((3-2) mod 12)+1 = 2.
    assert table["MARS"] == 2


def test_relative_house_facts_match_table(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    for row in analysis.relative_house_facts:
        assert (
            analysis.relative_house_table[row.reference.value][row.body.value]
            == row.relative_house_number
        )
        assert row.derivation.id == "RELATIVE_HOUSE"


def test_subset_references_requested(whole_sign_chart) -> None:
    from bhava.service import _effective_references

    refs = _effective_references(("SUN",))
    assert refs == (TransitReferencePoint.SUN,)
    analysis = derive_house_analysis(whole_sign_chart, references=refs)
    assert list(analysis.relative_house_table) == ["SUN"]
