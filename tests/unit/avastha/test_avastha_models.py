"""Unit tests for Avastha domain models."""

from __future__ import annotations

from jyotish import BodyId

from avastha.models import (
    JagradadiState,
    DeeptadiState,
    BaladiState,
    AvasthaResult,
    AvasthaReport,
    JagradadiState as _,
)


class TestJagradadiState:
    def test_enum_members(self) -> None:
        assert JagradadiState.JAGRAT.value == "JAGRAT"
        assert JagradadiState.SWAPNA.value == "SWAPNA"
        assert JagradadiState.SUSHUPTI.value == "SUSHUPTI"

    def test_all_three_states(self) -> None:
        assert len(JagradadiState) == 3


class TestDeeptadiState:
    def test_enum_members(self) -> None:
        assert DeeptadiState.DEEPTA.value == "DEEPTA"
        assert DeeptadiState.SWASTHA.value == "SWASTHA"
        assert DeeptadiState.PRASANTA.value == "PRASANTA"
        assert DeeptadiState.DEENA.value == "DEENA"
        assert DeeptadiState.KSHUDHITA.value == "KSHUDHITA"
        assert DeeptadiState.KSHOBHITA.value == "KSHOBHITA"

    def test_all_six_states(self) -> None:
        assert len(DeeptadiState) == 6


class TestBaladiState:
    def test_enum_members(self) -> None:
        assert BaladiState.BALA.value == "BALA"
        assert BaladiState.KUMARA.value == "KUMARA"
        assert BaladiState.YUVA.value == "YUVA"
        assert BaladiState.VRIDDHA.value == "VRIDDHA"
        assert BaladiState.MRITA.value == "MRITA"

    def test_all_five_states(self) -> None:
        assert len(BaladiState) == 5


class TestAvasthaResult:
    def test_fields(self) -> None:
        r = AvasthaResult(
            planet=BodyId.SUN,
            jagradadi=JagradadiState.JAGRAT,
            deeptadi=DeeptadiState.DEEPTA,
            baladi=BaladiState.YUVA,
            multiplier=1.0,
        )
        assert r.planet == BodyId.SUN
        assert r.jagradadi == JagradadiState.JAGRAT
        assert r.multiplier == 1.0

    def test_to_dict(self) -> None:
        r = AvasthaResult(
            planet=BodyId.SUN,
            jagradadi=JagradadiState.JAGRAT,
            deeptadi=DeeptadiState.DEEPTA,
            baladi=None,
            multiplier=0.75,
        )
        d = r.to_dict()
        assert d["planet"] == "SUN"
        assert d["jagradadi"] == "JAGRAT"
        assert d["multiplier"] == 0.75


class TestAvasthaReport:
    def test_is_tuple(self) -> None:
        r = AvasthaReport(
            results=(
                AvasthaResult(
                    planet=BodyId.SUN,
                    jagradadi=JagradadiState.JAGRAT,
                    deeptadi=DeeptadiState.DEEPTA,
                    baladi=BaladiState.YUVA,
                    multiplier=1.0,
                ),
            )
        )
        assert isinstance(r.results, tuple)
        assert len(r.results) == 1

    def test_result_for(self) -> None:
        r = AvasthaReport(
            results=(
                AvasthaResult(
                    planet=BodyId.SUN,
                    jagradadi=JagradadiState.JAGRAT,
                    deeptadi=DeeptadiState.DEEPTA,
                    baladi=None,
                    multiplier=1.0,
                ),
            )
        )
        assert r.result_for(BodyId.SUN) is not None
        assert r.result_for(BodyId.MOON) is None
