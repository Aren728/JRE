"""Shared builders for JRE-005 unit tests.

Synthetic charts are constructed via the ``jyotish`` PUBLIC API only
(mirroring the JRE-005 boundary), so derivation logic is testable without
an ephemeris. No birth data is embedded (privacy rule); charts are pure
fixtures in code.
"""

from __future__ import annotations

import pytest

from jyotish import (
    ApplyingSeparating,
    AspectKind,
    AspectRelationship,
    Bhava,
    BirthData,
    BodyId,
    DmsValue,
    HouseSystem,
    JyotishConfig,
    LagnaState,
    NatalChart,
    PlanetState,
    RetrogradeState,
    TransitThroughHouses,
    degree_in_nakshatra,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
    sign_lord_of,
)

FAKE_AYANAMSA = 23.0


def make_planet_state(
    body: BodyId = BodyId.SUN,
    longitude_used: float = 5.0,
    speed: float = 1.0,
    latitude: float = 0.0,
    retrograde: RetrogradeState | None = None,
) -> PlanetState:
    """Build a full ``PlanetState`` with consistent fields (public API)."""
    lon = longitude_used % 360.0
    rashi = rashi_of(lon)
    nakshatra = nakshatra_of(lon)
    return PlanetState(
        body=body,
        longitude_tropical=(lon + FAKE_AYANAMSA) % 360.0,
        longitude_sidereal=lon,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi,
        degree_in_rashi=degree_in_rashi(lon),
        nakshatra=nakshatra,
        nakshatra_lord=lord_of(nakshatra),
        pada=pada_of(lon),
        degree_in_nakshatra=degree_in_nakshatra(lon),
        latitude=latitude,
        speed_longitude=speed,
        retrograde=(
            retrograde
            if retrograde is not None
            else (RetrogradeState.RETROGRADE if speed < 0.0 else RetrogradeState.DIRECT)
        ),
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


def make_aspect(
    kind: AspectKind = AspectKind.TRINE,
    exact_angle_deg: float = 120.0,
    within_orb: bool = True,
) -> AspectRelationship:
    return AspectRelationship(
        kind=kind,
        exact_angle_deg=exact_angle_deg,
        separation_deg=exact_angle_deg,
        distance_from_exact_deg=0.0,
        within_orb=within_orb,
        orb_deg=7.0,
        applying_separating=ApplyingSeparating.SEPARATING,
    )


def make_bhava(
    house_number: int,
    start_deg: float,
    end_deg: float,
    occupants: tuple[PlanetState, ...] = (),
    aspects: tuple[AspectRelationship, ...] = (),
) -> Bhava:
    """Build one ``Bhava`` (public-API derived fields)."""
    start = start_deg % 360.0
    return Bhava(
        house_number=house_number,
        start_deg=start,
        end_deg=end_deg % 360.0,
        rashi=rashi_of(start),
        house_lord=sign_lord_of(rashi_of(start)),
        occupants=tuple(state.body for state in occupants),
        occupant_states=occupants,
        aspects=aspects,
        nakshatra=nakshatra_of(start),
    )


def make_whole_sign_chart(
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> NatalChart:
    """Canonical synthetic chart: lagna MESHA, one body per house 1..9
    (SUN..KETU at 5°, 35°, ..., 245°), houses 10–12 empty."""
    bodies = [
        (BodyId.SUN, 5.0),
        (BodyId.MOON, 35.0),
        (BodyId.MARS, 65.0),
        (BodyId.MERCURY, 95.0),
        (BodyId.JUPITER, 125.0),
        (BodyId.VENUS, 155.0),
        (BodyId.SATURN, 185.0),
        (BodyId.RAHU, 215.0),
        (BodyId.KETU, 245.0),
    ]
    states = tuple(make_planet_state(body, lon) for body, lon in bodies)
    bhavas = tuple(
        make_bhava(
            h, (h - 1) * 30.0, h * 30.0, (states[h - 1],) if h <= len(states) else ()
        )
        for h in range(1, 13)
    )
    return make_chart(states, bhavas, house_system)


def make_chart(
    planet_states: tuple[PlanetState, ...],
    bhavas: tuple[Bhava, ...],
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> NatalChart:
    """Build a ``NatalChart`` from states and bhavas (lagna = house 1)."""
    lagna_rashi = bhavas[0].rashi
    lagna = LagnaState(
        ascendant_longitude_deg=bhavas[0].start_deg,
        dms=DmsValue(degrees=int(bhavas[0].start_deg), minutes=0, seconds=0.0, sign=1),
        rashi=lagna_rashi,
        degree_in_rashi=degree_in_rashi(bhavas[0].start_deg),
        nakshatra=nakshatra_of(bhavas[0].start_deg),
        nakshatra_lord=lord_of(nakshatra_of(bhavas[0].start_deg)),
        pada=pada_of(bhavas[0].start_deg),
        degree_in_nakshatra=degree_in_nakshatra(bhavas[0].start_deg),
        bhava_relationship=bhavas[0],
        house_system=house_system,
    )
    return NatalChart(
        birth_snapshot=make_birth(),
        lagna=lagna,
        bhavas=bhavas,
        planet_states=planet_states,
        config=JyotishConfig(house_system=house_system),
        provider_metadata=(),
    )


def make_birth() -> BirthData:
    return BirthData(
        date="1990-06-15",
        time="10:00:00",
        timezone="Asia/Kolkata",
        latitude=28.6139,
        longitude=77.2090,
    )


def make_transit(
    natal_chart: NatalChart,
    transiting: tuple[tuple[BodyId, float], ...],
) -> TransitThroughHouses:
    """Build a TransitThroughHouses whose entries echo the natal house the
    transiting longitude falls in (JRE-003 semantics)."""
    import jyotish
    from jyotish import HouseTransitEntry, JyotishConfig, TransitReferencePoint

    entries = []
    states = []
    for body, longitude in transiting:
        state = make_planet_state(body, longitude)
        states.append(state)
        containing = jyotish.bhava_containing_longitude(natal_chart.bhavas, longitude)
        entry_house = containing.house_number if containing is not None else 1
        entries.append(
            HouseTransitEntry(
                body=body,
                natal_house_number=entry_house,
                natal_house_lord=natal_chart.bhavas[entry_house - 1].house_lord,
                natal_occupants=natal_chart.bhavas[entry_house - 1].occupants,
                aspects_to_natal=(),
                natal_house_rashi=natal_chart.bhavas[entry_house - 1].rashi,
            )
        )
    return TransitThroughHouses(
        reference=TransitReferencePoint.LAGNA,
        transit_instant_utc_iso="2024-06-01T00:00:00Z",
        planet_states=tuple(states),
        entries=tuple(entries),
        birth_snapshot=natal_chart.birth_snapshot,
        config=JyotishConfig(),
    )


def make_gapped_natal_chart() -> NatalChart:
    """Whole-sign chart whose house 12 spans [330, 350) — leaving the arc
    [350, 360) uncovered so a transiting body there is genuinely unplaced."""
    from dataclasses import replace

    chart = make_whole_sign_chart()
    bhavas = list(chart.bhavas)
    bhavas[11] = replace(bhavas[11], end_deg=350.0)
    return replace(chart, bhavas=tuple(bhavas))


@pytest.fixture
def whole_sign_chart() -> NatalChart:
    return make_whole_sign_chart()
