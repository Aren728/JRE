"""Pure derivation tests (normative specification §8-§11, §21-§22).

Every known value below is traced to the BPHS ch. 6 verses / Speculum
tables (R. Santhanam translation) or the other primary sources recorded in
the source-pinning research. Boundary membership uses the frozen
HALF_OPEN_LOW convention: ``[lower, upper)`` — an exact boundary belongs
to the NEXT division; 30°00' is invalid (JRE-003 normalizes to [0, 30)).
"""

from __future__ import annotations

import pytest
from tests.unit.varga.conftest import make_state

from jyotish import BodyId, RashiId
from varga import (
    BoundaryConvention,
    compute_varga_position,
    get_varga_definition,
)
from varga.errors import InvalidVargaRequestError


def _position(varga_id: str, rashi: str, degree: float) -> tuple[RashiId, int]:
    definition = get_varga_definition(varga_id)
    position = compute_varga_position(make_state(RashiId[rashi], degree), definition)
    return position.varga_sign, position.division_index


# --------------------------------------------------------------------------- #
# D2 Hora (BPHS v.5-6 + Speculum of Horas)
# --------------------------------------------------------------------------- #


def test_d2_hora_odd_even_halves() -> None:
    # Odd signs: first half Leo (Sun), second half Cancer (Moon).
    assert _position("D2", "MESHA", 10.0) == (RashiId.SIMHA, 1)
    assert _position("D2", "MESHA", 20.0) == (RashiId.KARKA, 2)
    # Even signs: reversed.
    assert _position("D2", "VRISHABHA", 10.0) == (RashiId.KARKA, 1)
    assert _position("D2", "VRISHABHA", 20.0) == (RashiId.SIMHA, 2)
    # Speculum of Horas row for Leo (odd): Sun then Moon.
    assert _position("D2", "SIMHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D2", "SIMHA", 29.9) == (RashiId.KARKA, 2)
    # Speculum row for Scorpio (even): Moon then Sun.
    assert _position("D2", "VRISHCHIKA", 0.0) == (RashiId.KARKA, 1)
    assert _position("D2", "VRISHCHIKA", 29.9) == (RashiId.SIMHA, 2)


def test_d2_hora_exact_15_degree_boundary() -> None:
    # [0, 15) -> first hora; [15, 30) -> second hora (HALF_OPEN_LOW).
    assert _position("D2", "MESHA", 15.0) == (RashiId.KARKA, 2)
    assert _position("D2", "MESHA", 14.9999999) == (RashiId.SIMHA, 1)
    assert _position("D2", "VRISHABHA", 15.0) == (RashiId.SIMHA, 2)
    assert _position("D2", "VRISHABHA", 14.9999999) == (RashiId.KARKA, 1)


# --------------------------------------------------------------------------- #
# D3 Drekkana (BPHS v.7-8 + Speculum): 1st/5th/9th from the source sign
# --------------------------------------------------------------------------- #


def test_d3_trinal_mapping() -> None:
    # Aries: 1st->Aries(1), 2nd->Leo(5), 3rd->Sagittarius(9).
    assert _position("D3", "MESHA", 4.0) == (RashiId.MESHA, 1)
    assert _position("D3", "MESHA", 14.0) == (RashiId.SIMHA, 2)
    assert _position("D3", "MESHA", 25.0) == (RashiId.DHANUSHA, 3)
    # Taurus: speculum 2/6/10.
    assert _position("D3", "VRISHABHA", 4.0) == (RashiId.VRISHABHA, 1)
    assert _position("D3", "VRISHABHA", 14.0) == (RashiId.KANYA, 2)
    assert _position("D3", "VRISHABHA", 25.0) == (RashiId.MAKARA, 3)
    # Leo: speculum 5/9/1 (wraps).
    assert _position("D3", "SIMHA", 4.0) == (RashiId.SIMHA, 1)
    assert _position("D3", "SIMHA", 14.0) == (RashiId.DHANUSHA, 2)
    assert _position("D3", "SIMHA", 25.0) == (RashiId.MESHA, 3)


def test_d3_boundaries() -> None:
    assert _position("D3", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D3", "MESHA", 10.0) == (RashiId.SIMHA, 2)
    assert _position("D3", "MESHA", 9.9999999) == (RashiId.MESHA, 1)
    assert _position("D3", "MESHA", 20.0) == (RashiId.DHANUSHA, 3)
    assert _position("D3", "MESHA", 19.9999999) == (RashiId.SIMHA, 2)
    assert _position("D3", "MESHA", 29.9999999) == (RashiId.DHANUSHA, 3)


# --------------------------------------------------------------------------- #
# D4 Chaturthamsa (BPHS v.9 + Speculum): 1st/4th/7th/10th from the source
# --------------------------------------------------------------------------- #


def test_d4_kendra_mapping() -> None:
    assert _position("D4", "MESHA", 4.0) == (RashiId.MESHA, 1)
    assert _position("D4", "MESHA", 10.0) == (RashiId.KARKA, 2)
    assert _position("D4", "MESHA", 18.0) == (RashiId.TULA, 3)
    assert _position("D4", "MESHA", 25.0) == (RashiId.MAKARA, 4)
    # Taurus 2nd -> 5th (speculum).
    assert _position("D4", "VRISHABHA", 10.0) == (RashiId.SIMHA, 2)


def test_d4_boundaries() -> None:
    # Each chaturthamsa is 7.5°: [0,7.5) [7.5,15) [15,22.5) [22.5,30).
    assert _position("D4", "MESHA", 7.5) == (RashiId.KARKA, 2)
    assert _position("D4", "MESHA", 7.4999999) == (RashiId.MESHA, 1)
    assert _position("D4", "MESHA", 22.5) == (RashiId.MAKARA, 4)
    assert _position("D4", "MESHA", 22.4999999) == (RashiId.TULA, 3)


# --------------------------------------------------------------------------- #
# D7 Saptamsa (BPHS v.10-11 + Speculum): odd same sign, even 7th sign
# --------------------------------------------------------------------------- #


def test_d7_odd_even_mapping() -> None:
    # Odd sign: count from the sign itself.
    assert _position("D7", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D7", "MESHA", 20.0) == (RashiId.SIMHA, 5)
    # Even sign: count from the 7th sign (speculum: Taurus 1st -> Scorpio 8).
    assert _position("D7", "VRISHABHA", 0.0) == (RashiId.VRISHCHIKA, 1)
    assert _position("D7", "VRISHABHA", 5.0) == (RashiId.DHANUSHA, 2)


def test_d7_boundaries() -> None:
    # Each saptamsa is 30/7 degrees; [0, 30/7) is the first.
    assert _position("D7", "MESHA", 30.0 / 7.0) == (RashiId.VRISHABHA, 2)
    # 7th saptamsa of Aries = 7th sign from Aries = Libra.
    assert _position("D7", "MESHA", 29.9999999) == (RashiId.TULA, 7)


# --------------------------------------------------------------------------- #
# D9 Navamsa (BPHS v.12 + Speculum): relative modality — movable +0,
# fixed +8 (9th), dual +4 (5th)
# --------------------------------------------------------------------------- #


def test_d9_relative_modality_mapping() -> None:
    # Speculum 1st row: 1 10 7 4 1 10 7 4 1 10 7 4.
    assert _position("D9", "MESHA", 0.0) == (RashiId.MESHA, 1)  # movable
    assert _position("D9", "VRISHABHA", 0.0) == (RashiId.MAKARA, 1)  # fixed 9th
    assert _position("D9", "MITHUNA", 0.0) == (RashiId.TULA, 1)  # dual 5th
    assert _position("D9", "KARKA", 0.0) == (RashiId.KARKA, 1)  # movable
    assert _position("D9", "SIMHA", 0.0) == (RashiId.MESHA, 1)  # fixed 9th
    assert _position("D9", "KANYA", 0.0) == (RashiId.MAKARA, 1)  # dual 5th
    assert _position("D9", "TULA", 0.0) == (RashiId.TULA, 1)  # movable
    assert _position("D9", "VRISHCHIKA", 0.0) == (RashiId.KARKA, 1)  # fixed 9th
    assert _position("D9", "DHANUSHA", 0.0) == (RashiId.MESHA, 1)  # dual 5th
    assert _position("D9", "MAKARA", 0.0) == (RashiId.MAKARA, 1)  # movable
    assert _position("D9", "KUMBHA", 0.0) == (RashiId.TULA, 1)  # fixed 9th
    assert _position("D9", "MEENA", 0.0) == (RashiId.KARKA, 1)  # dual 5th
    # 2nd navamsa of movable Aries -> Taurus (3°20' = 3.33333...;
    # 3.3333333334 is just above the boundary).
    assert _position("D9", "MESHA", 3.3333333334) == (RashiId.VRISHABHA, 2)
    # 2nd navamsa of fixed Leo: 9th from Leo = Aries, +1 = Taurus.
    assert _position("D9", "SIMHA", 3.3333333334) == (RashiId.VRISHABHA, 2)


def test_d9_boundaries() -> None:
    # Navamsa boundaries at k * 3°20' (= 3.33333...).
    assert _position("D9", "MESHA", 3.3333333334) == (RashiId.VRISHABHA, 2)
    assert _position("D9", "MESHA", 3.3333333332) == (RashiId.MESHA, 1)
    assert _position("D9", "MESHA", 26.6666666667) == (RashiId.DHANUSHA, 9)
    assert _position("D9", "MESHA", 29.9999999) == (RashiId.DHANUSHA, 9)


# --------------------------------------------------------------------------- #
# D10 Dasamsa (BPHS v.13-14): odd same sign, even 9th sign
# --------------------------------------------------------------------------- #


def test_d10_odd_even_mapping() -> None:
    assert _position("D10", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D10", "MESHA", 25.0) == (RashiId.DHANUSHA, 9)
    assert _position("D10", "VRISHABHA", 0.0) == (RashiId.MAKARA, 1)  # 9th from Taurus
    assert _position("D10", "VRISHABHA", 3.0) == (RashiId.KUMBHA, 2)


def test_d10_boundaries() -> None:
    # Dasamsa boundaries at k * 3°.
    assert _position("D10", "MESHA", 3.0) == (RashiId.VRISHABHA, 2)
    assert _position("D10", "MESHA", 2.9999999) == (RashiId.MESHA, 1)
    assert _position("D10", "MESHA", 27.0) == (RashiId.MAKARA, 10)


# --------------------------------------------------------------------------- #
# D12 Dwadashamsa (BPHS v.15 + Speculum): successive from the sign itself
# for ALL signs (Santhanam BPHS)
# --------------------------------------------------------------------------- #


def test_d12_self_sequence() -> None:
    # Santhanam BPHS example: the Dvadashamsa in Aries are Aries, Taurus,
    # ... Pisces in order.
    assert _position("D12", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D12", "MESHA", 25.0) == (RashiId.KUMBHA, 11)
    assert _position("D12", "MESHA", 29.9999999) == (RashiId.MEENA, 12)
    # Taurus counts from Taurus too (speculum: 1st row is the sign itself).
    assert _position("D12", "VRISHABHA", 0.0) == (RashiId.VRISHABHA, 1)
    assert _position("D12", "VRISHABHA", 25.0) == (RashiId.MEENA, 11)


def test_d12_boundaries() -> None:
    # Dwadashamsa boundaries at k * 2.5°.
    assert _position("D12", "MESHA", 2.5) == (RashiId.VRISHABHA, 2)
    assert _position("D12", "MESHA", 2.4999999) == (RashiId.MESHA, 1)


# --------------------------------------------------------------------------- #
# D16 Shodasamsa (BPHS v.16 + Speculum): absolute modality —
# movable Aries, fixed Leo, dual Sagittarius
# --------------------------------------------------------------------------- #


def test_d16_absolute_modality_mapping() -> None:
    # Speculum: movable 1st -> Aries; fixed 1st -> Leo; dual 1st -> Sagittarius.
    assert _position("D16", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D16", "KARKA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D16", "TULA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D16", "MAKARA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D16", "SIMHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D16", "VRISHABHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D16", "MITHUNA", 0.0) == (RashiId.DHANUSHA, 1)
    assert _position("D16", "MEENA", 0.0) == (RashiId.DHANUSHA, 1)
    # 2nd shodasamsa: movable -> Taurus, fixed -> Virgo, dual -> Capricorn.
    assert _position("D16", "MESHA", 3.0) == (RashiId.VRISHABHA, 2)
    assert _position("D16", "SIMHA", 3.0) == (RashiId.KANYA, 2)
    assert _position("D16", "MITHUNA", 3.0) == (RashiId.MAKARA, 2)


def test_d16_boundaries() -> None:
    # Shodasamsa = 1°52'30" = 1.875°.
    assert _position("D16", "MESHA", 1.875) == (RashiId.VRISHABHA, 2)
    assert _position("D16", "MESHA", 1.8749999) == (RashiId.MESHA, 1)


# --------------------------------------------------------------------------- #
# D20 Vimsamsa (BPHS v.17-21): absolute modality — movable Aries,
# fixed Sagittarius, dual Leo (canonical); Saravali note variant separate
# --------------------------------------------------------------------------- #


def test_d20_bphs_mapping() -> None:
    # BPHS (Sanskrit): cara -> Aries, sthira -> Sagittarius, dvisvabhava -> Leo.
    assert _position("D20", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D20", "SIMHA", 0.0) == (RashiId.DHANUSHA, 1)
    assert _position("D20", "MITHUNA", 0.0) == (RashiId.SIMHA, 1)
    # 17th vimsamsa (25°): movable -> Leo, fixed -> Aries, dual -> Virgo
    # (dual start is Leo, so 17th from Leo = Leo + 16 = Sagittarius).
    assert _position("D20", "MESHA", 25.0) == (RashiId.SIMHA, 17)
    assert _position("D20", "SIMHA", 25.0) == (RashiId.MESHA, 17)
    assert _position("D20", "MITHUNA", 25.0) == (RashiId.DHANUSHA, 17)


def test_d20_saravali_variant_distinct() -> None:
    """Same input, different method -> different result and identity."""
    from varga import varga_definition_identity

    state = make_state(RashiId.SIMHA, 25.0)
    bphs = get_varga_definition("D20", "d20-bphs-v1")
    variant = get_varga_definition("D20", "d20-saravali-variant-v1")
    p_bphs = compute_varga_position(state, bphs, method=bphs.calculation_method)
    p_var = compute_varga_position(state, variant, method=variant.calculation_method)
    # Saravali note: movable -> Aries, dual -> Sagittarius, common/fixed -> Leo.
    assert p_var.varga_sign == RashiId.DHANUSHA  # fixed Leo, 17th from Leo = Sagittarius
    assert p_bphs.varga_sign == RashiId.MESHA
    assert p_bphs.position_id != p_var.position_id
    assert varga_definition_identity(bphs) != varga_definition_identity(variant)


def test_d20_boundaries() -> None:
    # Vimsamsa = 1°30' = 1.5°.
    assert _position("D20", "MESHA", 1.5) == (RashiId.VRISHABHA, 2)
    assert _position("D20", "MESHA", 1.4999999) == (RashiId.MESHA, 1)


# --------------------------------------------------------------------------- #
# D24 Siddhamsa (BPHS v.22-23): absolute — any odd sign from Leo,
# any even sign from Cancer
# --------------------------------------------------------------------------- #


def test_d24_absolute_odd_even_mapping() -> None:
    # Odd signs start from Leo; even signs from Cancer.
    assert _position("D24", "MESHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D24", "SIMHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D24", "VRISHABHA", 0.0) == (RashiId.KARKA, 1)
    assert _position("D24", "VRISHCHIKA", 0.0) == (RashiId.KARKA, 1)
    # 5th siddhamsa (5°): odd -> Leo+4 = Sagittarius; even -> Cancer+4 = Scorpio.
    assert _position("D24", "MESHA", 5.0) == (RashiId.DHANUSHA, 5)
    assert _position("D24", "SIMHA", 5.0) == (RashiId.DHANUSHA, 5)
    assert _position("D24", "VRISHABHA", 5.0) == (RashiId.VRISHCHIKA, 5)


def test_d24_boundaries() -> None:
    # Siddhamsa = 1°15' = 1.25°.
    assert _position("D24", "MESHA", 1.25) == (RashiId.KANYA, 2)
    assert _position("D24", "MESHA", 1.2499999) == (RashiId.SIMHA, 1)


# --------------------------------------------------------------------------- #
# D30 Trimsamsa (BPHS v.27-28 + Speculum): explicit unequal five-band table
# --------------------------------------------------------------------------- #


def test_d30_odd_bands() -> None:
    # Odd: 0-5 Aries, 5-10 Aquarius, 10-18 Sagittarius, 18-25 Gemini, 25-30 Libra.
    cases = [
        (0.0, "MESHA"),
        (4.9999999, "MESHA"),
        (5.0, "KUMBHA"),
        (9.9999999, "KUMBHA"),
        (10.0, "DHANUSHA"),
        (17.9999999, "DHANUSHA"),
        (18.0, "MITHUNA"),
        (24.9999999, "MITHUNA"),
        (25.0, "TULA"),
        (29.9999999, "TULA"),
    ]
    for degree, expected in cases:
        sign, index = _position("D30", "MESHA", degree)
        assert sign.value == expected, f"odd {degree} -> {sign}"


def test_d30_even_bands() -> None:
    # Even: 0-5 Taurus, 5-12 Virgo, 12-20 Pisces, 20-25 Capricorn, 25-30 Scorpio.
    cases = [
        (0.0, "VRISHABHA"),
        (4.9999999, "VRISHABHA"),
        (5.0, "KANYA"),
        (11.9999999, "KANYA"),
        (12.0, "MEENA"),
        (19.9999999, "MEENA"),
        (20.0, "MAKARA"),
        (24.9999999, "MAKARA"),
        (25.0, "VRISHCHIKA"),
        (29.9999999, "VRISHCHIKA"),
    ]
    for degree, expected in cases:
        sign, index = _position("D30", "VRISHABHA", degree)
        assert sign.value == expected, f"even {degree} -> {sign}"


def test_d30_never_populates_leo_cancer() -> None:
    """The unequal classical table never maps a trimsamsa to Leo or Cancer."""
    from varga import compute_varga_position

    for rashi in RashiId:
        for tenth in range(300):
            degree = tenth / 10.0
            position = compute_varga_position(
                make_state(rashi, degree), get_varga_definition("D30")
            )
            assert position.varga_sign not in (RashiId.SIMHA, RashiId.KARKA)


# --------------------------------------------------------------------------- #
# D40 Chaturvarimsamsa (BPHS v.29-30): absolute — odd signs from Aries,
# even signs from Libra
# --------------------------------------------------------------------------- #


def test_d40_absolute_odd_even_mapping() -> None:
    # Speculum 1st/13th/25th/37th row: 1 7 1 7 1 7 ...
    assert _position("D40", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D40", "MITHUNA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D40", "VRISHABHA", 0.0) == (RashiId.TULA, 1)
    assert _position("D40", "MEENA", 0.0) == (RashiId.TULA, 1)
    # 7th chaturvarimsamsa (5°): odd -> Aries+6 = Libra; even -> Libra+6 = Aries.
    assert _position("D40", "MESHA", 5.0) == (RashiId.TULA, 7)
    assert _position("D40", "VRISHABHA", 5.0) == (RashiId.MESHA, 7)


def test_d40_boundaries() -> None:
    # Chaturvarimsamsa = 45' = 0.75°.
    assert _position("D40", "MESHA", 0.75) == (RashiId.VRISHABHA, 2)
    assert _position("D40", "MESHA", 0.7499999) == (RashiId.MESHA, 1)


# --------------------------------------------------------------------------- #
# D45 Akshavedamsa (BPHS v.31-32): absolute modality — movable Aries,
# fixed Leo, dual Sagittarius
# --------------------------------------------------------------------------- #


def test_d45_absolute_modality_mapping() -> None:
    assert _position("D45", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D45", "SIMHA", 0.0) == (RashiId.SIMHA, 1)
    assert _position("D45", "MITHUNA", 0.0) == (RashiId.DHANUSHA, 1)
    # 31st akshavedamsa (20°): movable -> Aries+30 = Libra; fixed -> Leo+30 = Aquarius.
    assert _position("D45", "MESHA", 20.0) == (RashiId.TULA, 31)
    assert _position("D45", "SIMHA", 20.0) == (RashiId.KUMBHA, 31)


def test_d45_boundaries() -> None:
    # Akshavedamsa = 40' = 2/3°.
    assert _position("D45", "MESHA", 0.6666666667) == (RashiId.VRISHABHA, 2)
    assert _position("D45", "MESHA", 0.6666666666) == (RashiId.MESHA, 1)


# --------------------------------------------------------------------------- #
# D60 Shashtiamsa (BPHS v.33-41): remainder algorithm — count forward from
# the source sign for BOTH odd and even signs
# --------------------------------------------------------------------------- #


def test_d60_bphs_worked_example() -> None:
    """BPHS worked example: Venus at Capricorn 13°25' (even sign)
    -> 13°25' x 2 = 26°50' -> 26 / 12 remainder 2 -> +1 = 3
    -> count 3 signs from Capricorn -> Pisces (lord Jupiter)."""
    sign, index = _position("D60", "MAKARA", 13.4166666667)
    assert sign == RashiId.MEENA
    assert index == 27


def test_d60_odd_even_same_sign_counting() -> None:
    # Odd sign: count from the same sign.
    assert _position("D60", "MESHA", 0.0) == (RashiId.MESHA, 1)
    assert _position("D60", "MESHA", 5.5) == (RashiId.MEENA, 12)  # 12th from Aries
    # Even sign: count from the same sign too (the odd/even reversal in
    # BPHS applies only to the shashtiamsa NAMES, not sign positions).
    # 6.5° -> 14th shashtiamsa -> 2nd from the source sign.
    assert _position("D60", "VRISHABHA", 0.0) == (RashiId.VRISHABHA, 1)
    assert _position("D60", "VRISHABHA", 0.5) == (RashiId.MITHUNA, 2)
    assert _position("D60", "VRISHABHA", 6.5) == (RashiId.MITHUNA, 14)
    # Capricorn (even) worked-example family: count from Capricorn — the
    # "from the 9th" reading would put these elsewhere.
    assert _position("D60", "MAKARA", 0.0) == (RashiId.MAKARA, 1)
    assert _position("D60", "MAKARA", 6.0) == (RashiId.MAKARA, 13)  # 13th == 1st in cycle


def test_d60_boundaries_and_remainder_transitions() -> None:
    from tests.unit.varga.conftest import make_raw_state

    # Shashtiamsa = 0.5°; boundaries at k * 0.5.
    assert _position("D60", "MESHA", 0.5) == (RashiId.VRISHABHA, 2)
    assert _position("D60", "MESHA", 0.4999999) == (RashiId.MESHA, 1)
    assert _position("D60", "MESHA", 29.5) == (RashiId.MEENA, 60)
    assert _position("D60", "MESHA", 29.4999999) == (RashiId.KUMBHA, 59)
    # 30°00' is invalid as a JRE-008 input (JRE-003 normalizes to [0, 30)).
    with pytest.raises(InvalidVargaRequestError):
        compute_varga_position(
            make_raw_state(30.0), get_varga_definition("D60")
        )


# --------------------------------------------------------------------------- #
# Boundary policy / precision / input contract
# --------------------------------------------------------------------------- #


def test_boundary_convention_half_open_low() -> None:
    for varga_id in ("D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
                     "D20", "D24", "D30", "D40", "D45", "D60"):
        definition = get_varga_definition(varga_id)
        assert definition.boundary_convention is BoundaryConvention.HALF_OPEN_LOW


def test_zero_degree_first_division() -> None:
    for varga_id in ("D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
                     "D20", "D24", "D30", "D40", "D45", "D60"):
        position = compute_varga_position(
            make_state(RashiId.MESHA, 0.0), get_varga_definition(varga_id)
        )
        assert position.division_index == 1


def test_30_degrees_rejected() -> None:
    from tests.unit.varga.conftest import make_raw_state

    for varga_id in ("D2", "D9", "D30", "D60"):
        with pytest.raises(InvalidVargaRequestError):
            compute_varga_position(
                make_raw_state(30.0), get_varga_definition(varga_id)
            )


def test_negative_degree_rejected() -> None:
    from tests.unit.varga.conftest import make_raw_state

    with pytest.raises(InvalidVargaRequestError):
        compute_varga_position(
            make_raw_state(-0.0001), get_varga_definition("D9")
        )


def test_no_approximate_boundary_snapping() -> None:
    """A just-below-boundary value must stay in the lower division — no
    nearest-rational snapping onto the boundary (spec §10)."""
    # 3°20' = 3.33333...; 3.3333333332 is below it and must be division 1.
    assert _position("D9", "MESHA", 3.3333333332) == (RashiId.MESHA, 1)
    # 40' = 0.6666...; 0.6666666666 is below it and must be division 1.
    assert _position("D45", "MESHA", 0.6666666666) == (RashiId.MESHA, 1)
    # 30/7 = 4.2857142857...; 4.2857142856 is below it and must be division 1.
    assert _position("D7", "MESHA", 4.2857142856) == (RashiId.MESHA, 1)
    # 0.5° shashtiamsa boundary: 0.4999999 stays in division 1.
    assert _position("D60", "MESHA", 0.4999999) == (RashiId.MESHA, 1)


def test_echoes_jre003_facts() -> None:
    state = make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.MOON)
    position = compute_varga_position(state, get_varga_definition("D60"))
    assert position.source_state_id == position.provenance.source_state_id
    assert position.provenance.provider_id == state.provider_id
    assert position.provenance.ephemeris_version == state.ephemeris_version
    assert position.longitude_used == state.longitude_used
    assert position.source_rashi == state.rashi
    assert position.source_degree_in_rashi == state.degree_in_rashi
    assert position.body is BodyId.MOON


def test_deterministic_repeat() -> None:
    state = make_state(RashiId.MITHUNA, 17.0)
    definition = get_varga_definition("D9")
    a = compute_varga_position(state, definition)
    b = compute_varga_position(state, definition)
    assert a.to_dict() == b.to_dict()
    assert a.position_id == b.position_id


def test_identity_sensitive_to_inputs() -> None:
    from varga import varga_definition_identity

    state = make_state(RashiId.MESHA, 5.0)
    definition = get_varga_definition("D9")
    base = compute_varga_position(state, definition)
    # Degree change -> different position identity.
    other = compute_varga_position(make_state(RashiId.MESHA, 5.5), definition)
    assert base.position_id != other.position_id
    # Method change -> different definition identity.
    assert varga_definition_identity(definition) != varga_definition_identity(
        get_varga_definition("D20")
    )


def test_mismatched_method_rejected() -> None:
    definition = get_varga_definition("D9")
    foreign = get_varga_definition("D10").calculation_method
    with pytest.raises(InvalidVargaRequestError):
        compute_varga_position(make_state(), definition, method=foreign)


def test_source_citations_present() -> None:
    for varga_id in ("D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
                     "D20", "D24", "D30", "D40", "D45", "D60"):
        position = compute_varga_position(
            make_state(RashiId.MESHA, 5.0), get_varga_definition(varga_id)
        )
        assert position.provenance.source_citations
