"""Golden-value integration tests (normative specification §26).

Independent known values taken directly from the BPHS ch. 6 Speculum
tables (R. Santhanam translation, Ranjan Publications 1984) — NOT
re-derived from the engine. Every row below was transcribed from the text
during source-pinning research. Positions are placed at division
mid-points to avoid boundary-float ambiguity; boundary membership itself
is covered in the unit suite.
"""

from __future__ import annotations

from tests.unit.varga.conftest import make_state

from jyotish import BodyId, RashiId
from varga import compute_varga_position, get_varga_definition

SIGNS = list(RashiId)


def _position_at_midpoint(varga_id: str, sign: RashiId, division: int) -> RashiId:
    definition = get_varga_definition(varga_id)
    n = definition.division_number
    if varga_id == "D30":
        # D30 uses the unequal table; place at the midpoint of each band
        # by testing both parities separately below.
        raise AssertionError("D30 has no uniform division; use band tests")
    lower = (division - 1) * 30.0 / n
    upper = division * 30.0 / n
    degree = (lower + upper) / 2.0
    return compute_varga_position(
        make_state(sign, degree, body=BodyId.SUN), definition
    ).varga_sign


# --------------------------------------------------------------------------- #
# D3 Drekkana — Speculum of Drekkana (BPHS ch. 6, page 44)
# --------------------------------------------------------------------------- #

D3_SPECULUM = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    2: [5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4],
    3: [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8],
}


def test_d3_matches_speculum() -> None:
    for division, row in D3_SPECULUM.items():
        for sign_index, sign in enumerate(SIGNS):
            expected = RashiId(SIGNS[row[sign_index] - 1].value)
            assert _position_at_midpoint("D3", sign, division) == expected, (
                f"D3 {sign} div {division} -> {expected}"
            )


# --------------------------------------------------------------------------- #
# D4 Chaturthamsa — Speculum of Chathurthamsa (BPHS ch. 6, page 44)
# --------------------------------------------------------------------------- #

D4_SPECULUM = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    2: [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3],
    3: [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6],
    4: [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],
}


def test_d4_matches_speculum() -> None:
    for division, row in D4_SPECULUM.items():
        for sign_index, sign in enumerate(SIGNS):
            expected = RashiId(SIGNS[row[sign_index] - 1].value)
            assert _position_at_midpoint("D4", sign, division) == expected, (
                f"D4 {sign} div {division} -> {expected}"
            )


# --------------------------------------------------------------------------- #
# D7 Saptamsa — Speculum of Sapthamamsha (BPHS ch. 6, page 45)
# --------------------------------------------------------------------------- #

D7_SPECULUM_FIRST = [1, 8, 3, 10, 5, 12, 7, 2, 9, 4, 11, 6]


def test_d7_first_division_matches_speculum() -> None:
    for sign_index, sign in enumerate(SIGNS):
        expected = RashiId(SIGNS[D7_SPECULUM_FIRST[sign_index] - 1].value)
        assert _position_at_midpoint("D7", sign, 1) == expected, (
            f"D7 {sign} 1st saptamsa -> {expected}"
        )


# --------------------------------------------------------------------------- #
# D9 Navamsa — Speculum of Navamsha (BPHS ch. 6, page 46)
# --------------------------------------------------------------------------- #

#: Rows transcribed from the printed table (signs 1..12 per row).
D9_SPECULUM = {
    1: [1, 10, 7, 4, 1, 10, 7, 4, 1, 10, 7, 4],
    2: [2, 11, 8, 5, 2, 11, 8, 5, 2, 11, 8, 5],
    3: [3, 12, 9, 6, 3, 12, 9, 6, 3, 12, 9, 6],
    4: [4, 1, 10, 7, 4, 1, 10, 7, 4, 1, 10, 7],
    5: [5, 2, 11, 8, 5, 2, 11, 8, 5, 2, 11, 8],
    6: [6, 3, 12, 9, 6, 3, 12, 9, 6, 3, 12, 9],
    7: [7, 4, 1, 10, 7, 4, 1, 10, 7, 4, 1, 10],
    8: [8, 5, 2, 11, 8, 5, 2, 11, 8, 5, 2, 11],
    9: [9, 6, 3, 12, 9, 6, 3, 12, 9, 6, 3, 12],
}


def test_d9_matches_speculum() -> None:
    for division, row in D9_SPECULUM.items():
        for sign_index, sign in enumerate(SIGNS):
            expected = RashiId(SIGNS[row[sign_index] - 1].value)
            assert _position_at_midpoint("D9", sign, division) == expected, (
                f"D9 {sign} div {division} -> {expected}"
            )


# --------------------------------------------------------------------------- #
# D16 Shodasamsa — Speculum of Shodashamsa (BPHS ch. 6, page 48)
# --------------------------------------------------------------------------- #


def test_d16_absolute_starts_match_speculum() -> None:
    # 1st/13th: movable -> Aries; fixed -> Leo; dual -> Sagittarius.
    expected = {
        RashiId.MESHA: RashiId.MESHA,
        RashiId.KARKA: RashiId.MESHA,
        RashiId.TULA: RashiId.MESHA,
        RashiId.MAKARA: RashiId.MESHA,
        RashiId.VRISHABHA: RashiId.SIMHA,
        RashiId.SIMHA: RashiId.SIMHA,
        RashiId.VRISHCHIKA: RashiId.SIMHA,
        RashiId.KUMBHA: RashiId.SIMHA,
        RashiId.MITHUNA: RashiId.DHANUSHA,
        RashiId.KANYA: RashiId.DHANUSHA,
        RashiId.DHANUSHA: RashiId.DHANUSHA,
        RashiId.MEENA: RashiId.DHANUSHA,
    }
    for sign, want in expected.items():
        assert _position_at_midpoint("D16", sign, 1) == want
        assert _position_at_midpoint("D16", sign, 13) == want


# --------------------------------------------------------------------------- #
# D20 Vimsamsa — BPHS v.17-21 (cara->Aries, sthira->Sagittarius,
# dvisvabhava->Leo)
# --------------------------------------------------------------------------- #


def test_d20_bphs_absolute_starts() -> None:
    starts = {
        RashiId.MESHA: RashiId.MESHA,  # movable
        RashiId.KARKA: RashiId.MESHA,
        RashiId.TULA: RashiId.MESHA,
        RashiId.MAKARA: RashiId.MESHA,
        RashiId.VRISHABHA: RashiId.DHANUSHA,  # fixed
        RashiId.SIMHA: RashiId.DHANUSHA,
        RashiId.VRISHCHIKA: RashiId.DHANUSHA,
        RashiId.KUMBHA: RashiId.DHANUSHA,
        RashiId.MITHUNA: RashiId.SIMHA,  # dual
        RashiId.KANYA: RashiId.SIMHA,
        RashiId.DHANUSHA: RashiId.SIMHA,
        RashiId.MEENA: RashiId.SIMHA,
    }
    for sign, want in starts.items():
        assert _position_at_midpoint("D20", sign, 1) == want


# --------------------------------------------------------------------------- #
# D40 Chaturvarimsamsa — Speculum of Chatvarimsamsa (BPHS ch. 6, page 52)
# --------------------------------------------------------------------------- #


def test_d40_first_division_matches_speculum() -> None:
    # 1st/13th/25th/37th row: odd signs -> 1 (Aries), even signs -> 7 (Libra).
    for sign_index, sign in enumerate(SIGNS):
        want = RashiId.MESHA if sign_index % 2 == 0 else RashiId.TULA
        assert _position_at_midpoint("D40", sign, 1) == want
        assert _position_at_midpoint("D40", sign, 13) == want
        assert _position_at_midpoint("D40", sign, 25) == want
        assert _position_at_midpoint("D40", sign, 37) == want


# --------------------------------------------------------------------------- #
# D60 Shashtiamsa — BPHS v.33-41 worked example + cycle structure
# --------------------------------------------------------------------------- #


def test_d60_bphs_worked_example_golden() -> None:
    """Venus at Capricorn 13°25' -> 26°50' -> 26/12 rem 2 -> +1 = 3
    -> count 3 from Capricorn -> Pisces (BPHS ch. 6, translator's note)."""
    definition = get_varga_definition("D60")
    position = compute_varga_position(
        make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.VENUS), definition
    )
    assert position.varga_sign == RashiId.MEENA
    assert position.division_index == 27
    assert position.body is BodyId.VENUS


def test_d60_full_cycle_odd_and_even_signs() -> None:
    # Shashtiamsa k (1..60) of any sign -> (source + (k-1) mod 12).
    for sign in (RashiId.MESHA, RashiId.MAKARA):
        for k in range(1, 61):
            # Place the planet at the midpoint of shashtiamsa k.
            got = _position_at_midpoint("D60", sign, k)
            want = RashiId(SIGNS[(SIGNS.index(sign) + (k - 1) % 12) % 12].value)
            assert got == want, f"D60 {sign} shashtiamsa {k} -> {got}"


# --------------------------------------------------------------------------- #
# D30 Trimsamsa — explicit unequal five-band table (BPHS v.27-28)
# --------------------------------------------------------------------------- #


def test_d30_odd_sign_all_bands() -> None:
    # Odd bands: 0-5 Aries, 5-10 Aquarius, 10-18 Sagittarius, 18-25 Gemini,
    # 25-30 Libra (lords Mars, Saturn, Jupiter, Mercury, Venus).
    cases = [
        (2.5, RashiId.MESHA),
        (7.5, RashiId.KUMBHA),
        (14.0, RashiId.DHANUSHA),
        (21.5, RashiId.MITHUNA),
        (27.5, RashiId.TULA),
    ]
    for degree, want in cases:
        position = compute_varga_position(
            make_state(RashiId.MESHA, degree), get_varga_definition("D30")
        )
        assert position.varga_sign == want, f"odd {degree} -> {want}"


def test_d30_even_sign_all_bands() -> None:
    # Even bands: 0-5 Taurus, 5-12 Virgo, 12-20 Pisces, 20-25 Capricorn,
    # 25-30 Scorpio (lords Venus, Mercury, Jupiter, Saturn, Mars).
    cases = [
        (2.5, RashiId.VRISHABHA),
        (8.5, RashiId.KANYA),
        (16.0, RashiId.MEENA),
        (22.5, RashiId.MAKARA),
        (27.5, RashiId.VRISHCHIKA),
    ]
    for degree, want in cases:
        position = compute_varga_position(
            make_state(RashiId.VRISHABHA, degree), get_varga_definition("D30")
        )
        assert position.varga_sign == want, f"even {degree} -> {want}"
