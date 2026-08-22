"""Unit tests for BirthSignature models."""

from __future__ import annotations

import json

import pytest

from birth_signature.errors import (
    BirthSignatureError,
    InvalidSignatureRequestError,
    SignatureComputationError,
)
from birth_signature.models import (
    BIRTH_SIGNATURE_VERSION,
    AmPm,
    BirthSignature,
    DayNightPeriod,
    HoraPeriod,
    Karana,
    Tithi,
    Vara,
    Yoga,
    compute_am_pm,
    compute_day_night,
    compute_hora,
    compute_karana,
    compute_tithi,
    compute_tithi_number,
    compute_vara,
    compute_yoga,
    compute_yoga_number,
)
from jyotish import NakshatraId, Pada, RashiId

# --------------------------------------------------------------------------- #
# Tithi tests
# --------------------------------------------------------------------------- #


class TestTithi:
    """Tests for the Tithi enum and computation."""

    def test_all_thirties_have_string_values(self) -> None:
        for t in Tithi:
            assert isinstance(t.value, str)
            assert t.value == t.name

    def test_tithi_count(self) -> None:
        assert len(Tithi) == 30

    def test_conjunction_is_pratipada(self) -> None:
        """Sun and Moon at same longitude = Tithi 1 (SHUKLA_PRATIPADA)."""
        t = compute_tithi(10.0, 10.0)
        assert t == Tithi.SHUKLA_PRATIPADA

    def test_twelve_degrees_is_dvitiya(self) -> None:
        """Moon 12° ahead of Sun = Tithi 2 (SHUKLA_DVITIYA)."""
        t = compute_tithi(10.0, 22.0)
        assert t == Tithi.SHUKLA_DVITIYA

    def test_full_moon_is_purnima(self) -> None:
        """Moon 168° ahead of Sun = Tithi 15 (PURNIMA)."""
        t = compute_tithi(10.0, 178.0)
        assert t == Tithi.PURNIMA

    def test_waning_pratipada(self) -> None:
        """Moon 180° ahead of Sun = Tithi 16 (KRISHNA_PRATIPADA)."""
        t = compute_tithi(10.0, 190.0)
        assert t == Tithi.KRISHNA_PRATIPADA

    def test_amanta_is_thirty(self) -> None:
        """Moon 348° ahead of Sun = Tithi 30 (AMANTHA)."""
        t = compute_tithi(10.0, 358.0)
        assert t == Tithi.AMANTHA

    def test_wrapping_distance(self) -> None:
        """Sun at 250°, Moon at 50° = 160° diff = Tithi 14."""
        t = compute_tithi(250.0, 50.0)
        assert t == Tithi.SHUKLA_CHATURDASHI

    def test_tithi_number_range(self) -> None:
        """Tithi numbers should always be in [1, 30]."""
        for sun in range(0, 360, 30):
            for moon in range(0, 360, 15):
                num = compute_tithi_number(float(sun), float(moon))
                assert 1 <= num <= 30

    def test_tithi_number_consistency(self) -> None:
        """Tithi number maps to correct Tithi enum."""
        assert compute_tithi_number(0.0, 0.0) == 1
        assert compute_tithi_number(0.0, 12.0) == 2
        assert compute_tithi_number(0.0, 180.0) == 16


# --------------------------------------------------------------------------- #
# Karana tests
# --------------------------------------------------------------------------- #


class TestKarana:
    """Tests for the Karana enum and computation."""

    def test_all_karanas_have_string_values(self) -> None:
        for k in Karana:
            assert isinstance(k.value, str)
            assert k.value == k.name

    def test_karana_count(self) -> None:
        assert len(Karana) == 11

    def test_conjunction_first_half_is_kimstughna(self) -> None:
        """Sun and Moon at same longitude = first half = KIMSTUGHNA."""
        k = compute_karana(10.0, 10.0)
        assert k == Karana.KIMSTUGHNA

    def test_second_half_tithi_one(self) -> None:
        """Moon 6° ahead of Sun (midway in Tithi 1) = second half."""
        k = compute_karana(10.0, 16.0)
        assert k == Karana.BALAVA

    def test_tithi_two_first_half(self) -> None:
        """Moon 12° ahead of Sun = start of Tithi 2."""
        k = compute_karana(10.0, 22.0)
        assert k == Karana.BAVALA

    def test_full_moon_area(self) -> None:
        """Near full moon (Tithi 15)."""
        k = compute_karana(10.0, 190.0)
        # Tithi 15, should be near end of cycle
        assert isinstance(k, Karana)

    def test_amanta_second_half_is_shakuni(self) -> None:
        """Last half-tithi (position 59) = SHAKUNI."""
        # Moon 354° ahead of Sun (6° before full 360)
        k = compute_karana(0.0, 354.0)
        assert k == Karana.SHAKUNI


# --------------------------------------------------------------------------- #
# Yoga tests
# --------------------------------------------------------------------------- #


class TestYoga:
    """Tests for the Yoga enum and computation."""

    def test_all_yogas_have_string_values(self) -> None:
        for y in Yoga:
            assert isinstance(y.value, str)
            assert y.value == y.name

    def test_yoga_count(self) -> None:
        assert len(Yoga) == 27

    def test_conjunction_is_vishkambha(self) -> None:
        """Sun and Moon at same longitude = Yoga 1 (VISHKAMBHA)."""
        y = compute_yoga(0.0, 0.0)
        assert y == Yoga.VISHKAMBHA

    def test_sum_at_14_is_priti(self) -> None:
        """Sum of Sun+Moon = 14° = Yoga 2 (PRITI)."""
        y = compute_yoga(7.0, 7.0)
        assert y == Yoga.PRITI

    def test_full_circle(self) -> None:
        """Sum wraps: Sun=200, Moon=200 = 400 mod 360 = 40°."""
        y = compute_yoga(200.0, 200.0)
        # 40 * 27 / 360 = 3.0, so yoga = 4 = SOUBHAGYA
        assert y == Yoga.SOUBHAGYA

    def test_yoga_number_range(self) -> None:
        """Yoga numbers should always be in [1, 27]."""
        for sun in range(0, 360, 30):
            for moon in range(0, 360, 15):
                num = compute_yoga_number(float(sun), float(moon))
                assert 1 <= num <= 27


# --------------------------------------------------------------------------- #
# Vara tests
# --------------------------------------------------------------------------- #


class TestVara:
    """Tests for the Vara (weekday) computation."""

    def test_all_vars_have_string_values(self) -> None:
        for v in Vara:
            assert isinstance(v.value, str)
            assert v.value == v.name

    def test_vara_count(self) -> None:
        assert len(Vara) == 7

    def test_known_weekday(self) -> None:
        """JD 2451545.0 (2000-01-01 12:00 UT) is a Saturday."""
        v = compute_vara(2451545.0)
        assert v == Vara.SATURDAY

    def test_sunday(self) -> None:
        """2000-01-02 is a Sunday. JD for 2000-01-02 12:00 UT = 2451546.0."""
        v = compute_vara(2451546.0)
        assert v == Vara.SUNDAY


# --------------------------------------------------------------------------- #
# Hora tests
# --------------------------------------------------------------------------- #


class TestHora:
    """Tests for the Hora computation."""

    def test_all_hora_periods_have_string_values(self) -> None:
        for h in HoraPeriod:
            assert isinstance(h.value, str)
            assert h.value == h.name

    def test_hora_count(self) -> None:
        assert len(HoraPeriod) == 7

    def test_sunday_first_hour_is_sun(self) -> None:
        """On Sunday (JD 2451546.0), first hora should be SUN."""
        h = compute_hora(2451546.0, 0.0)
        assert h == HoraPeriod.SUN

    def test_sunday_second_hour_is_moon(self) -> None:
        """On Sunday, second hora (hour 1) should be MOON."""
        h = compute_hora(2451546.0, 1.0)
        assert h == HoraPeriod.MOON

    def test_monday_first_hour_is_moon(self) -> None:
        """On Monday (JD 2451547.0), first hora should be MOON."""
        h = compute_hora(2451547.0, 0.0)
        assert h == HoraPeriod.MOON


# --------------------------------------------------------------------------- #
# AmPm tests
# --------------------------------------------------------------------------- #


class TestAmPm:
    """Tests for the AM/PM computation."""

    def test_midnight_is_am(self) -> None:
        assert compute_am_pm(0.0) == AmPm.AM

    def test_noon_is_pm(self) -> None:
        assert compute_am_pm(12.0) == AmPm.PM

    def test_11_59_is_am(self) -> None:
        assert compute_am_pm(11.99) == AmPm.AM

    def test_12_00_is_pm(self) -> None:
        assert compute_am_pm(12.0) == AmPm.PM


# --------------------------------------------------------------------------- #
# DayNightPeriod tests
# --------------------------------------------------------------------------- #


class TestDayNightPeriod:
    """Tests for the Day/Night computation."""

    def test_morning_is_day(self) -> None:
        assert compute_day_night(10.0, 10.0) == DayNightPeriod.DAY

    def test_evening_is_night(self) -> None:
        assert compute_day_night(250.0, 20.0) == DayNightPeriod.NIGHT

    def test_six_am_is_day(self) -> None:
        assert compute_day_night(100.0, 6.0) == DayNightPeriod.DAY

    def test_six_pm_is_night(self) -> None:
        assert compute_day_night(100.0, 18.0) == DayNightPeriod.NIGHT


# --------------------------------------------------------------------------- #
# BirthSignature dataclass tests
# --------------------------------------------------------------------------- #


class TestBirthSignature:
    """Tests for the BirthSignature dataclass."""

    def test_creation(self) -> None:
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        assert sig.lagna == RashiId.MESHA
        assert sig.tithi == Tithi.SHUKLA_PRATIPADA

    def test_frozen(self) -> None:
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        with pytest.raises(AttributeError):
            sig.lagna = RashiId.VRISHABHA  # type: ignore[misc]

    def test_deterministic_id_computed(self) -> None:
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        assert sig.deterministic_id != ""
        assert len(sig.deterministic_id) == 64  # SHA-256 hex

    def test_deterministic_id_same_for_equal_inputs(self) -> None:
        sig1 = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        sig2 = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        assert sig1.deterministic_id == sig2.deterministic_id

    def test_deterministic_id_different_for_different_inputs(self) -> None:
        sig1 = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        sig2 = BirthSignature(
            lagna=RashiId.KARKA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        assert sig1.deterministic_id != sig2.deterministic_id

    def test_to_dict(self) -> None:
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        d = sig.to_dict()
        assert d["lagna"] == "MESHA"
        assert d["tithi"] == "SHUKLA_PRATIPADA"
        assert d["yoga"] == "SUBHA"
        assert d["weekday"] == "THURSDAY"
        assert d["deterministic_id"] != ""

    def test_to_dict_deterministic(self) -> None:
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        d1 = sig.to_dict()
        d2 = sig.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(
            d2, sort_keys=True
        )

    def test_cross_contamination_prevention(self) -> None:
        """Ensure BirthSignature fields are distinct from other domains."""
        sig = BirthSignature(
            lagna=RashiId.MESHA,
            sun_rashi=RashiId.MESHA,
            moon_rashi=RashiId.VRISHABHA,
            nakshatra=NakshatraId.ASHWINI,
            pada=Pada.PADA_1,
            weekday=Vara.THURSDAY,
            hora=HoraPeriod.JUPITER,
            tithi=Tithi.SHUKLA_PRATIPADA,
            karana=Karana.BALAVA,
            yoga=Yoga.SUBHA,
            day_night_period=DayNightPeriod.DAY,
            am_pm=AmPm.AM,
        )
        d = sig.to_dict()
        # No cancer/health/career/marriage keywords
        all_values = " ".join(str(v) for v in d.values()).lower()
        assert "disease" not in all_values
        assert "death" not in all_values
        assert "cancer" not in all_values
        assert "marriage" not in all_values


# --------------------------------------------------------------------------- #
# Version test
# --------------------------------------------------------------------------- #


class TestVersion:
    """Tests for the package version constant."""

    def test_version_string(self) -> None:
        assert isinstance(BIRTH_SIGNATURE_VERSION, str)
        assert BIRTH_SIGNATURE_VERSION != ""


# --------------------------------------------------------------------------- #
# Error hierarchy tests
# --------------------------------------------------------------------------- #


class TestErrors:
    """Tests for the error hierarchy."""

    def test_base_error_is_exception(self) -> None:
        assert issubclass(BirthSignatureError, Exception)

    def test_request_error_inherits(self) -> None:
        assert issubclass(InvalidSignatureRequestError, BirthSignatureError)

    def test_computation_error_inherits(self) -> None:
        assert issubclass(SignatureComputationError, BirthSignatureError)
