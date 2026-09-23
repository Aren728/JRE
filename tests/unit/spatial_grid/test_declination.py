"""Tests for the geospatial declination module.

All expectations are closed-form spherical-astronomy identities — no
ephemeris, no approximations beyond the obliquity constant itself.
"""

from __future__ import annotations

import math

import pytest

from geospatial.declination import (
    DEFAULT_OBLIQUITY_DEG,
    declination_from_ecliptic,
    ecliptic_longitude_crossing,
    horizon_declination,
    max_visible_declination,
    right_ascension_from_ecliptic,
    solar_declination,
)

# --------------------------------------------------------------------------- #
# declination_from_ecliptic
# --------------------------------------------------------------------------- #


class TestDeclinationFromEcliptic:
    def test_vernal_equinox_zero(self) -> None:
        # Sun at 0° ecliptic longitude sits on the equator.
        assert declination_from_ecliptic(0.0) == pytest.approx(0.0, abs=1e-12)

    def test_autumnal_equinox_zero(self) -> None:
        assert declination_from_ecliptic(180.0) == pytest.approx(0.0, abs=1e-12)

    def test_solstice_ascending_branch(self) -> None:
        # Summer solstice: lambda = 90° → delta = +obliquity.
        assert declination_from_ecliptic(90.0) == pytest.approx(
            DEFAULT_OBLIQUITY_DEG, abs=1e-9
        )

    def test_solstice_descending_branch(self) -> None:
        assert declination_from_ecliptic(270.0) == pytest.approx(
            -DEFAULT_OBLIQUITY_DEG, abs=1e-9
        )

    def test_longitude_wraps(self) -> None:
        # 450° == 90°.
        assert declination_from_ecliptic(450.0) == pytest.approx(
            declination_from_ecliptic(90.0), abs=1e-12
        )
        assert declination_from_ecliptic(-90.0) == pytest.approx(
            -DEFAULT_OBLIQUITY_DEG, abs=1e-9
        )

    def test_ecliptic_latitude_term(self) -> None:
        # sin(delta) = sin(beta)cos(eps) + cos(beta)sin(eps)sin(lambda)
        beta, lam = 5.0, 30.0
        expected = math.degrees(
            math.asin(
                math.sin(math.radians(beta)) * math.cos(math.radians(DEFAULT_OBLIQUITY_DEG))
                + math.cos(math.radians(beta))
                * math.sin(math.radians(DEFAULT_OBLIQUITY_DEG))
                * math.sin(math.radians(lam))
            )
        )
        assert declination_from_ecliptic(lam, beta) == pytest.approx(expected, abs=1e-12)

    def test_pole_of_ecliptic(self) -> None:
        # A body at the ecliptic pole (beta = 90°) has delta = 90° - eps.
        assert declination_from_ecliptic(0.0, 90.0) == pytest.approx(
            90.0 - DEFAULT_OBLIQUITY_DEG, abs=1e-9
        )

    def test_symmetry_lambda_vs_180_minus(self) -> None:
        # Declination is symmetric around the solstice: d(90+x) == d(90-x).
        assert declination_from_ecliptic(60.0) == pytest.approx(
            declination_from_ecliptic(120.0), abs=1e-12
        )


# --------------------------------------------------------------------------- #
# right_ascension_from_ecliptic
# --------------------------------------------------------------------------- #


class TestRightAscension:
    def test_equinoxes(self) -> None:
        # On the equinoxes RA == ecliptic longitude.
        assert right_ascension_from_ecliptic(0.0) == pytest.approx(0.0, abs=1e-12)
        assert right_ascension_from_ecliptic(180.0) == pytest.approx(180.0, abs=1e-12)

    def test_solstices(self) -> None:
        # RA(90°) = 90°, RA(270°) = 270°.
        assert right_ascension_from_ecliptic(90.0) == pytest.approx(90.0, abs=1e-12)
        assert right_ascension_from_ecliptic(270.0) == pytest.approx(270.0, abs=1e-12)

    def test_range_normalized(self) -> None:
        for lam in (10.0, 95.0, 200.0, 359.0):
            ra = right_ascension_from_ecliptic(lam)
            assert 0.0 <= ra < 360.0

    def test_identity_with_declination_pair(self) -> None:
        # The (RA, delta) pair must reproject to the original ecliptic point:
        # rotate the equatorial unit vector back by -obliquity about the
        # vernal-equinox axis.
        lam, beta = 137.5, -3.2
        eps = math.radians(DEFAULT_OBLIQUITY_DEG)
        ra = math.radians(right_ascension_from_ecliptic(lam, beta))
        dec = math.radians(declination_from_ecliptic(lam, beta))
        x_eq, y_eq, z_eq = (
            math.cos(dec) * math.cos(ra),
            math.cos(dec) * math.sin(ra),
            math.sin(dec),
        )
        y_ec = y_eq * math.cos(eps) + z_eq * math.sin(eps)
        z_ec = z_eq * math.cos(eps) - y_eq * math.sin(eps)
        lam_back = math.degrees(math.atan2(y_ec, x_eq)) % 360.0
        beta_back = math.degrees(math.asin(z_ec))
        assert ((lam_back - lam + 180) % 360) - 180 == pytest.approx(0.0, abs=1e-9)
        assert beta_back == pytest.approx(beta, abs=1e-9)


# --------------------------------------------------------------------------- #
# solar_declination
# --------------------------------------------------------------------------- #


class TestSolarDeclination:
    def test_matches_general_formula_at_zero_latitude(self) -> None:
        for lam in (0.0, 45.0, 90.0, 180.0, 271.0, 359.5):
            assert solar_declination(lam) == pytest.approx(
                declination_from_ecliptic(lam, 0.0), abs=1e-12
            )

    def test_tropical_bounds(self) -> None:
        for lam in range(0, 360, 5):
            assert abs(solar_declination(float(lam))) <= DEFAULT_OBLIQUITY_DEG + 1e-9

    def test_year_symmetry(self) -> None:
        # Equinox-symmetric longitudes have mirrored declinations.
        assert solar_declination(60.0) == pytest.approx(-solar_declination(300.0), abs=1e-12)


# --------------------------------------------------------------------------- #
# ecliptic_longitude_crossing
# --------------------------------------------------------------------------- #


class TestEclipticLongitudeCrossing:
    def test_round_trip_ascending(self) -> None:
        lon = ecliptic_longitude_crossing(10.0)
        assert declination_from_ecliptic(lon) == pytest.approx(10.0, abs=1e-9)
        assert 0.0 <= lon < 90.0  # ascending branch before the solstice

    def test_zero_crossing_is_equinox(self) -> None:
        assert ecliptic_longitude_crossing(0.0) == pytest.approx(0.0, abs=1e-12)

    def test_tropical_limit_reachable(self) -> None:
        lon = ecliptic_longitude_crossing(DEFAULT_OBLIQUITY_DEG)
        assert declination_from_ecliptic(lon) == pytest.approx(
            DEFAULT_OBLIQUITY_DEG, abs=1e-9
        )

    def test_beyond_tropical_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="tropical limit"):
            ecliptic_longitude_crossing(DEFAULT_OBLIQUITY_DEG + 0.5)
        with pytest.raises(ValueError):
            ecliptic_longitude_crossing(-DEFAULT_OBLIQUITY_DEG - 1.0)

    def test_negative_target_on_descending_reachable_via_wrap(self) -> None:
        # asin returns [-90, 90]; a negative target maps into (270, 360).
        lon = ecliptic_longitude_crossing(-10.0)
        assert 270.0 < lon < 360.0
        assert declination_from_ecliptic(lon) == pytest.approx(-10.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# horizon_declination / max_visible_declination
# --------------------------------------------------------------------------- #


class TestHorizonDeclination:
    def test_equator_threshold_is_90(self) -> None:
        # At the equator nothing is circumpolar: threshold is 90°.
        assert horizon_declination(0.0) == 90.0

    def test_poles_threshold_is_zero(self) -> None:
        assert horizon_declination(90.0) == 0.0
        assert horizon_declination(-90.0) == 0.0

    def test_midlatitude_value(self) -> None:
        # T = 90 - |lat|: Delhi (28.6°N) → 61.4°.
        assert horizon_declination(28.6) == pytest.approx(61.4, abs=1e-12)
        # Southern hemisphere is symmetric in magnitude.
        assert horizon_declination(-28.6) == pytest.approx(61.4, abs=1e-12)

    def test_refraction_reduces_threshold(self) -> None:
        assert horizon_declination(45.0, refraction_deg=0.5) == pytest.approx(
            44.5, abs=1e-12
        )

    def test_threshold_clamped_at_zero(self) -> None:
        # Refraction larger than the threshold clamps at 0 near the pole.
        assert horizon_declination(89.9, refraction_deg=1.0) == 0.0

    def test_invalid_latitude_raises(self) -> None:
        with pytest.raises(ValueError, match="out of range"):
            horizon_declination(90.5)

    def test_max_visible_is_alias(self) -> None:
        for lat in (-90.0, -33.0, 0.0, 17.25, 90.0):
            assert max_visible_declination(lat) == horizon_declination(lat)

    def test_circumpolar_regime_consistency(self) -> None:
        # A declination beyond the threshold never sets at that latitude —
        # cross-check against the classic h_max = delta + lat - 90 > 0 test.
        lat, dec = 60.0, 40.0
        assert abs(dec) > horizon_declination(lat)
        assert dec + lat - 90.0 > 0.0
