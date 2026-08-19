"""JRE-011 BalaService facade.

``BalaService.calculate_shadbala`` is the canonical entry point: it
validates the request and computes the six-fold Shadbala strength for
each classical planet + Rahu/Ketu.

The six balas are:
1. Sthana Bala (Positional Strength)
2. Dig Bala (Directional Strength)
3. Kala Bala (Temporal Strength)
4. Cheshta Bala (Motional/Effective Strength)
5. Naisargika Bala (Natural Strength)
6. Drik Bala (Aspectual Strength)

It performs NO prediction, interpretation, or judgment.
"""

from __future__ import annotations

import math

from jyotish import BodyId, LagnaState, PlanetState, RashiId, RetrogradeState

from .config import load_config
from .errors import InvalidBalaRequestError
from .models import (
    BALA_PLANETS,
    DEBILITATION_DEGREES,
    DIG_BALA_PEAK_HOUSE,
    DIGNITY_SCORES,
    KENDRA_HOUSES,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    PLANET_NUMBER,
    SIGN_LORDS_VIMSHOTTARI,
    VIRUPAS_PER_RUPA,
    BalaConfig,
    IshtaKashtaPhala,
    KalaBalaComponents,
    ShadbalaComponents,
    ShadbalaReport,
    ShadbalaResult,
    SthanaBalaComponents,
    get_dignity,
)

# RashiId to 1-indexed number mapping
_RASHI_ORDER: list[RashiId] = list(RashiId)


def _rashi_number(rashi: RashiId) -> int:
    """Convert RashiId to 1-indexed number (1=Aries, ...12=Pisces)."""
    return _RASHI_ORDER.index(rashi) + 1


class BalaService:
    """Deterministic Shadbala computation facade."""

    def __init__(self, config: BalaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> BalaConfig:
        return self._config

    def calculate_shadbala(
        self,
        planet_states: tuple[PlanetState, ...],
        lagna_state: LagnaState | None = None,
        moon_phase_fraction: float = 0.5,
    ) -> ShadbalaReport:
        """Compute the Shadbala for each classical planet + Rahu/Ketu.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.  Must include at least
            one state for each planet to be computed.
        lagna_state : LagnaState | None
            The ascendant state from JRE-003.  Used for Dig Bala
            directional calculations.  If None, Dig Bala defaults to 0.
        moon_phase_fraction : float
            The lunar phase fraction [0.0, 1.0] where 0.0 = new moon,
            0.5 = full moon.  Used for Paksha Bala.  Defaults to 0.5
            (full moon).

        Returns
        -------
        ShadbalaReport
            Per-planet Shadbala results with all six components.
        """
        self._validate_request(planet_states)

        # Index planet states by body
        state_map: dict[BodyId, PlanetState] = {}
        for ps in planet_states:
            state_map[ps.body] = ps

        results: list[ShadbalaResult] = []

        for planet in BALA_PLANETS:
            state: PlanetState | None = state_map.get(planet)
            if state is None:
                # Planet not in chart — skip with zero strength
                continue

            # Determine which house the planet is in (1-indexed)
            house_number = self._planet_house_number(planet, state, lagna_state)

            # Determine the sign lord of the planet's current sign
            sign_lord = SIGN_LORDS_VIMSHOTTARI.get(
                _rashi_number(state.rashi), BodyId.SUN
            )

            # 1. Sthana Bala
            sthana = self._compute_sthana_bala(
                planet, state, house_number, sign_lord
            )

            # 2. Dig Bala
            dig = self._compute_dig_bala(planet, house_number, lagna_state)

            # 3. Kala Bala
            kala = self._compute_kala_bala(
                planet, state, moon_phase_fraction
            )

            # 4. Cheshta Bala
            cheshta = self._compute_cheshta_bala(planet, state)

            # 5. Naisargika Bala
            naisargika = self._compute_naisargika_bala(planet)

            # 6. Drik Bala
            drik = 0.0  # Requires aspect computation; simplified for V1

            components = ShadbalaComponents(
                sthana_bala=sthana,
                dig_bala=dig,
                kala_bala=kala,
                cheshta_bala=cheshta,
                naisargika_bala=naisargika,
                drik_bala=drik,
            )

            total_virupas = components.total_virupas
            total_rupas = total_virupas / VIRUPAS_PER_RUPA

            minimum = self._config.minimum_rupas.get(planet.value, 5.0)
            ratio = total_rupas / minimum if minimum > 0 else 0.0

            ishta_kashta = self._compute_ishta_kashta(
                sthana.total, dig, kala.total, cheshta, naisargika, drik
            )

            results.append(ShadbalaResult(
                planet=planet,
                components=components,
                total_virupas=total_virupas,
                total_rupas=total_rupas,
                minimum_required=minimum,
                ratio=ratio,
                ishta_kashta=ishta_kashta,
            ))

        return ShadbalaReport(results=tuple(results))

    # ------------------------------------------------------------------ #
    # 1. Sthana Bala (Positional Strength)
    # ------------------------------------------------------------------ #

    def _compute_sthana_bala(
        self,
        planet: BodyId,
        state: PlanetState,
        house_number: int,
        sign_lord: BodyId,
    ) -> SthanaBalaComponents:
        """Compute Sthana Bala and its sub-components."""
        uchcha = self._uchcha_bala(planet, state)
        saptavargaja = self._saptavargaja_bala(planet, sign_lord)
        ojhayugma = self._ojhayugma_bala(planet, state)
        kendradi = self._kendradi_bala(house_number)
        drekkana = self._drekkana_bala(planet, state)

        return SthanaBalaComponents(
            uchcha_bala=uchcha,
            saptavargaja_bala=saptavargaja,
            ojhayugma_bala=ojhayugma,
            kendradi_bala=kendradi,
            drekkana_bala=drekkana,
        )

    def _uchcha_bala(self, planet: BodyId, state: PlanetState) -> float:
        """Uchcha Bala: 60 * (distance from debilitation) / 180.

        Max = 60 virupas at exaltation, min = 0 at debilitation.
        """
        debil = DEBILITATION_DEGREES.get(planet, 0.0)
        lon = state.longitude_used % 360.0

        # Angular distance from debilitation to current longitude (along
        # the zodiac, wrapping at 360).
        diff = (lon - debil) % 360.0

        # The exaltation-debilitation arc is always 180 degrees
        bala = 60.0 * diff / 180.0
        return max(0.0, min(bala, 60.0))

    def _saptavargaja_bala(
        self, planet: BodyId, sign_lord: BodyId
    ) -> float:
        """Saptavargaja Bala: simplified dignity-based scoring.

        Without full Varga charts, we score based on the D-1 (Rashi)
        dignity.  The classical formula uses 7 vargas, but for V1 we
        use the rashi dignity as a proxy (score 0-5 x weight).

        Score: dignity score (0-5) x weight 2.0 = max 10.0 virupas.
        """
        dignity = get_dignity(planet, sign_lord)
        score = DIGNITY_SCORES.get(dignity, 2)
        return float(score) * 2.0

    def _ojhayugma_bala(self, planet: BodyId, state: PlanetState) -> float:
        """Ojhayugma Bala: 30 virupas for favorable odd/even match.

        Odd-numbered signs (Aries, Gemini, Leo, ...): odd-numbered
        planets get 30, even-numbered get 15.  Even-numbered signs:
        reverse.
        """
        sign_num = _rashi_number(state.rashi)  # 1-indexed
        is_odd_sign = sign_num % 2 == 1
        planet_num = PLANET_NUMBER.get(planet, 1)
        is_odd_planet = planet_num % 2 == 1

        if is_odd_sign == is_odd_planet:
            return 30.0  # Favorable
        return 15.0  # Less favorable

    def _kendradi_bala(self, house_number: int) -> float:
        """Kendradi Bala: angular distance-based strength.

        Kendra (1,4,7,10): 60 virupas
        Panaphara (2,5,8,11): 30 virupas
        Apoklima (3,6,9,12): 15 virupas
        """
        if house_number in KENDRA_HOUSES:
            return 60.0
        if house_number in {2, 5, 8, 11}:
            return 30.0
        if house_number in {3, 6, 9, 12}:
            return 15.0
        return 0.0

    def _drekkana_bala(self, planet: BodyId, state: PlanetState) -> float:
        """Drekkana Bala: strength based on decanate (1/3 of sign).

        For malefic planets: 1st Drekkana = 15, 2nd = 8, 3rd = 4.
        For benefic planets: 1st = 4, 2nd = 8, 3rd = 15.
        """
        degree_in_sign = state.degree_in_rashi
        pada_index = int(degree_in_sign / 10.0)  # 0, 1, or 2

        if planet in NATURAL_MALEFICS:
            values = (15.0, 8.0, 4.0)
        elif planet in NATURAL_BENEFICS:
            values = (4.0, 8.0, 15.0)
        else:
            values = (10.0, 10.0, 10.0)  # Mercury is neutral

        return values[min(pada_index, 2)]

    # ------------------------------------------------------------------ #
    # 2. Dig Bala (Directional Strength)
    # ------------------------------------------------------------------ #

    def _compute_dig_bala(
        self,
        planet: BodyId,
        house_number: int,
        lagna_state: LagnaState | None,
    ) -> float:
        """Dig Bala: directional strength based on house placement.

        Each planet has a preferred direction (peak house).  When at
        the peak house, Dig Bala = 60 virupas.  At 90 degrees (3 houses)
        away, it drops toward 0.

        Without a lagna, Dig Bala cannot be computed and defaults to 0.

        Formula: 60 * cos^2(angular_distance / 2)
        where angular_distance = |house_number - peak_house| * 30 degrees.
        """
        # Without lagna, directional strength cannot be determined
        if lagna_state is None:
            return 0.0

        peak_house = DIG_BALA_PEAK_HOUSE.get(planet)
        if peak_house is None:
            return 0.0

        # Angular distance in degrees
        house_diff = abs(house_number - peak_house)
        if house_diff > 6:
            house_diff = 12 - house_diff
        angular_distance = house_diff * 30.0

        # Dig Bala = 60 * cos^2(angular_distance / 2)
        bala = 60.0 * (math.cos(math.radians(angular_distance / 2.0))) ** 2
        return max(0.0, min(bala, 60.0))

    # ------------------------------------------------------------------ #
    # 3. Kala Bala (Temporal Strength)
    # ------------------------------------------------------------------ #

    def _compute_kala_bala(
        self,
        planet: BodyId,
        state: PlanetState,  # noqa: ARG002
        moon_phase_fraction: float,
    ) -> KalaBalaComponents:
        """Compute Kala Bala and its sub-components."""
        nathonnatha = self._nathonnatha_bala(planet)
        paksha = self._paksha_bala(planet, moon_phase_fraction)
        tribhaga = self._tribhaga_bala(planet)
        ayana = self._ayana_bala(planet, state)
        yudhdha = 0.0  # Yudhdha Bala requires war detection; V1 = 0

        return KalaBalaComponents(
            nathonnatha_bala=nathonnatha,
            paksha_bala=paksha,
            tribhaga_bala=tribhaga,
            ayana_bala=ayana,
            yudhdha_bala=yudhdha,
        )

    def _nathonnatha_bala(self, planet: BodyId) -> float:
        """Nathonnatha Bala: day/night strength.

        Day planets (Sun, Jupiter, Mars): 30 virupas during day,
        15 during night.
        Night planets (Moon, Venus, Saturn): 30 during night,
        15 during day.
        Mercury: 15 (neutral).
        Rahu/Ketu: 15 (neutral).
        """
        day_planets = {BodyId.SUN, BodyId.JUPITER, BodyId.MARS}
        night_planets = {BodyId.MOON, BodyId.VENUS, BodyId.SATURN}

        # For simplicity, assume daytime (caller can refine with birth time).
        if planet in day_planets:
            return 30.0
        if planet in night_planets:
            return 15.0
        return 15.0  # Mercury, Rahu, Ketu

    def _paksha_bala(
        self, planet: BodyId, moon_phase_fraction: float
    ) -> float:
        """Paksha Bala: lunar phase strength.

        Classical formula:
        - Benefics: 60 * (1 - |2*phase - 1|)
          Full moon (0.5) -> 60, New moon (0.0/1.0) -> 0
        - Malefics: 60 * |2*phase - 1|
          Full moon (0.5) -> 0, New moon (0.0/1.0) -> 60
        - Mercury: 30 (neutral)
        """
        phase_deviation = abs(2.0 * moon_phase_fraction - 1.0)

        if planet in NATURAL_BENEFICS:
            return 60.0 * (1.0 - phase_deviation)
        if planet in NATURAL_MALEFICS:
            return 60.0 * phase_deviation
        # Mercury is neutral
        return 30.0

    def _tribhaga_bala(self, planet: BodyId) -> float:
        """Tribhaga Bala: three-part day strength.

        The day is divided into three parts: Sunrise-Midday,
        Midday-Sunset, Sunset-Next Sunrise.  Each planet has a
        preferred part.

        For V1, we use a simplified formula based on planet identity.
        """
        if planet == BodyId.SUN:
            return 30.0  # Midday
        if planet == BodyId.MOON:
            return 30.0  # Night
        return 0.0  # Other planets

    def _ayana_bala(
        self, planet: BodyId, state: PlanetState
    ) -> float:
        """Ayana Bala: solstice strength based on declination.

        Planets north of the celestial equator (positive declination)
        are stronger during Uttarayana (northward sun), and vice versa.

        For V1, we use latitude as a proxy for declination.
        """
        declination = state.latitude

        if planet in {BodyId.SUN, BodyId.JUPITER, BodyId.MARS}:
            return 30.0 + 30.0 * min(max(declination / 23.5, -1.0), 1.0)
        if planet in {BodyId.MOON, BodyId.VENUS, BodyId.SATURN}:
            return 30.0 - 30.0 * min(max(declination / 23.5, -1.0), 1.0)
        # Mercury, Rahu, Ketu
        return 30.0

    # ------------------------------------------------------------------ #
    # 4. Cheshta Bala (Motional/Effective Strength)
    # ------------------------------------------------------------------ #

    def _compute_cheshta_bala(
        self, planet: BodyId, state: PlanetState
    ) -> float:
        """Cheshta Bala: motional strength based on retrograde/speed.

        Retrograde planets get maximum Cheshta Bala (60 virupas).
        Direct planets get a proportional value based on their speed.
        Stationary planets get 0.
        """
        if state.retrograde == RetrogradeState.RETROGRADE:
            return 60.0
        if state.retrograde == RetrogradeState.STATIONARY:
            return 0.0

        # Direct motion: proportional to speed
        speed = abs(state.speed_longitude)
        bala = min(speed / 15.0, 1.0) * 60.0
        return max(0.0, min(bala, 60.0))

    # ------------------------------------------------------------------ #
    # 5. Naisargika Bala (Natural Strength)
    # ------------------------------------------------------------------ #

    def _compute_naisargika_bala(self, planet: BodyId) -> float:
        """Naisargika Bala: fixed natural strength from config."""
        return self._config.naisargika_virupas.get(planet.value, 8.57)

    # ------------------------------------------------------------------ #
    # 6. Drik Bala (Aspectual Strength)
    # ------------------------------------------------------------------ #

    # Drik Bala requires full aspect computation across all planets.
    # For V1, it defaults to 0 (no benefic/malefic aspect scoring).

    # ------------------------------------------------------------------ #
    # Ishta / Kashta Phala
    # ------------------------------------------------------------------ #

    def _compute_ishta_kashta(
        self,
        sthana: float,
        dig: float,
        kala: float,
        cheshta: float,
        naisargika: float,
        drik: float,
    ) -> IshtaKashtaPhala:
        """Compute Ishta and Kashta Phala from the six balas.

        Ishta Phala = (Cheshta + Drik + Naisargika) / 3
        Kashta Phala = (Sthana + Dig + Kala) / 3
        """
        ishta = (cheshta + drik + naisargika) / 3.0
        kashta = (sthana + dig + kala) / 3.0
        return IshtaKashtaPhala(ishta_phala=ishta, kashta_phala=kashta)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _planet_house_number(
        self,
        planet: BodyId,  # noqa: ARG002
        state: PlanetState,
        lagna_state: LagnaState | None,
    ) -> int:
        """Determine the 1-indexed house number for a planet.

        Uses the Rashi position relative to the Ascendant sign.
        """
        if lagna_state is None:
            return 1

        lagna_num = _rashi_number(lagna_state.rashi)
        planet_num = _rashi_number(state.rashi)

        house = (planet_num - lagna_num) % 12 + 1
        return house

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Bala computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidBalaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidBalaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )
