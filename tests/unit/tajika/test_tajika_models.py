"""Unit tests for Tajika domain models."""

from __future__ import annotations

from jyotish import BodyId, RashiId

from tajika.models import (
    CLASSICAL_BENEFICS,
    RASHI_LORDS,
    SAHAM_FORMULAS,
    MunthaResult,
    SahamResult,
    SahamType,
    TajikaReport,
    VarsheshwarBasis,
    VarsheshwarResult,
    compute_muntha_lord,
    compute_muntha_rashi,
    compute_saham_longitude,
    compute_varsheshwar,
    longitude_to_degree_in_rashi,
    longitude_to_rashi,
)


class TestMunthaRashi:
    def test_year_0_is_natal_moon(self) -> None:
        assert compute_muntha_rashi(RashiId.MESHA, 0) == RashiId.MESHA

    def test_year_1_advances_one(self) -> None:
        assert compute_muntha_rashi(RashiId.MESHA, 1) == RashiId.VRISHABHA

    def test_year_12_wraps_around(self) -> None:
        assert compute_muntha_rashi(RashiId.MESHA, 12) == RashiId.MESHA

    def test_year_13_wraps_to_second(self) -> None:
        assert compute_muntha_rashi(RashiId.MESHA, 13) == RashiId.VRISHABHA

    def test_full_cycle_from_each_rashi(self) -> None:
        for rashi in RashiId:
            assert compute_muntha_rashi(rashi, 12) == rashi

    def test_negative_years_not_allowed(self) -> None:
        import pytest
        with pytest.raises((ValueError, OverflowError)):
            compute_muntha_rashi(RashiId.MESHA, -1)


class TestMunthaLord:
    def test_each_rashi_has_lord(self) -> None:
        for rashi in RashiId:
            lord = compute_muntha_lord(rashi)
            assert isinstance(lord, BodyId)

    def test_aries_lord_is_mars(self) -> None:
        assert compute_muntha_lord(RashiId.MESHA) == BodyId.MARS

    def test_taurus_lord_is_venus(self) -> None:
        assert compute_muntha_lord(RashiId.VRISHABHA) == BodyId.VENUS


class TestVarsheshwar:
    def test_benefic_muntha_lord_wins(self) -> None:
        result = compute_varsheshwar(
            muntha_lord=BodyId.JUPITER,
            year_lord=BodyId.SATURN,
            lagna_lord=BodyId.MARS,
        )
        assert result.planet == BodyId.JUPITER
        assert result.basis == VarsheshwarBasis.LORD_OF_MUNTHA

    def test_year_lord_wins_when_muntha_not_benefic(self) -> None:
        result = compute_varsheshwar(
            muntha_lord=BodyId.MARS,
            year_lord=BodyId.VENUS,
            lagna_lord=BodyId.SATURN,
        )
        assert result.planet == BodyId.VENUS
        assert result.basis == VarsheshwarBasis.LORD_OF_YEAR

    def test_lagna_lord_fallback(self) -> None:
        result = compute_varsheshwar(
            muntha_lord=BodyId.MARS,
            year_lord=BodyId.SATURN,
            lagna_lord=BodyId.JUPITER,
        )
        assert result.planet == BodyId.JUPITER
        assert result.basis == VarsheshwarBasis.LORD_OF_LAGNA


class TestSahamLongitude:
    def test_simple_calculation(self) -> None:
        # 100 + 150 - 60 = 190
        assert abs(compute_saham_longitude(100.0, 150.0, 60.0) - 190.0) < 1e-9

    def test_wraps_around_360(self) -> None:
        # 350 + 20 - 10 = 360 → 0
        assert abs(compute_saham_longitude(350.0, 20.0, 10.0) - 0.0) < 1e-9

    def test_negative_wraps(self) -> None:
        # 10 + 5 - 30 = -15 → 345
        assert abs(compute_saham_longitude(10.0, 5.0, 30.0) - 345.0) < 1e-9


class TestLongitudeConversion:
    def test_0_is_aries(self) -> None:
        assert longitude_to_rashi(0.0) == RashiId.MESHA

    def test_30_is_taurus(self) -> None:
        assert longitude_to_rashi(30.0) == RashiId.VRISHABHA

    def test_350_is_pisces(self) -> None:
        assert longitude_to_rashi(350.0) == RashiId.MEENA

    def test_degree_in_rashi(self) -> None:
        assert abs(longitude_to_degree_in_rashi(35.0) - 5.0) < 1e-9
        assert abs(longitude_to_degree_in_rashi(0.0) - 0.0) < 1e-9


class TestRashiLords:
    def test_all_12_rashis_have_lords(self) -> None:
        assert len(RASHI_LORDS) == 12
        for rashi in RashiId:
            assert rashi in RASHI_LORDS


class TestClassicalBenefics:
    def test_jupiter_is_benefic(self) -> None:
        assert BodyId.JUPITER in CLASSICAL_BENEFICS

    def test_venus_is_benefic(self) -> None:
        assert BodyId.VENUS in CLASSICAL_BENEFICS

    def test_saturn_not_benefic(self) -> None:
        assert BodyId.SATURN not in CLASSICAL_BENEFICS


class TestSahamFormulas:
    def test_all_saham_types_defined(self) -> None:
        assert len(SAHAM_FORMULAS) == len(SahamType)

    def test_punya_formula(self) -> None:
        assert SAHAM_FORMULAS[SahamType.PUNYA] == (BodyId.JUPITER, BodyId.SUN)


class TestMunthaResult:
    def test_to_dict(self) -> None:
        r = MunthaResult(rashi=RashiId.MESHA, house=1, lord=BodyId.MARS)
        d = r.to_dict()
        assert d["rashi"] == "MESHA"
        assert d["house"] == 1
        assert d["lord"] == "MARS"


class TestVarsheshwarResult:
    def test_to_dict(self) -> None:
        r = VarsheshwarResult(planet=BodyId.JUPITER, basis=VarsheshwarBasis.LORD_OF_MUNTHA)
        d = r.to_dict()
        assert d["planet"] == "JUPITER"
        assert d["basis"] == "LORD_OF_MUNTHA"


class TestSahamResult:
    def test_to_dict(self) -> None:
        r = SahamResult(saham_name=SahamType.PUNYA, rashi=RashiId.MESHA, degree=10.0)
        d = r.to_dict()
        assert d["saham_name"] == "PUNYA"
        assert d["rashi"] == "MESHA"
        assert d["degree"] == 10.0


class TestTajikaReport:
    def test_saham_for(self) -> None:
        report = TajikaReport(
            muntha=MunthaResult(rashi=RashiId.MESHA, house=1, lord=BodyId.MARS),
            varsheshwar=VarsheshwarResult(planet=BodyId.JUPITER, basis=VarsheshwarBasis.LORD_OF_MUNTHA),
            sahams=(
                SahamResult(saham_name=SahamType.PUNYA, rashi=RashiId.MESHA, degree=10.0),
            ),
        )
        assert report.saham_for(SahamType.PUNYA) is not None
        assert report.saham_for(SahamType.VIDYA) is None

    def test_to_dict(self) -> None:
        report = TajikaReport(
            muntha=MunthaResult(rashi=RashiId.MESHA, house=1, lord=BodyId.MARS),
            varsheshwar=VarsheshwarResult(planet=BodyId.JUPITER, basis=VarsheshwarBasis.LORD_OF_MUNTHA),
            sahams=(),
        )
        d = report.to_dict()
        assert "muntha" in d
        assert "varsheshwar" in d
        assert "sahams" in d
