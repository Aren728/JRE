"""Deterministic builders for the JRE-004 unit suite (no Swiss Ephemeris).

Kept in a uniquely-named module (not ``conftest``) so ``from _kb_helpers
import ...`` resolves unambiguously when the full test tree runs (pytest
inserts each test directory into ``sys.path``; several layers ship a
``conftest``/``test_config`` module).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from astronomy.models import BodyId, ProviderMetadata, RetrogradeState
from jyotish import (
    Bhava,
    DmsValue,
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    HouseSystem,
    JyotishConfig,
    LagnaState,
    NatalChart,
    PairGeometry,
    PlanetState,
    RashiId,
    SearchMetadata,
    TransitEvent,
    TransitEventKind,
)
from jyotish.models import ApplyingSeparating, AspectRelationship, BirthData
from jyotish.nakshatra import degree_in_nakshatra, lord_of, nakshatra_of, pada_of
from jyotish.rashi import degree_in_rashi, rashi_of

RASHI_LORDS: dict[str, str] = {
    "MESHA": "MARS",
    "VRISHABHA": "VENUS",
    "MITHUNA": "MERCURY",
    "KARKA": "MOON",
    "SIMHA": "SUN",
    "KANYA": "MERCURY",
    "TULA": "VENUS",
    "VRISHCHIKA": "MARS",
    "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN",
    "KUMBHA": "SATURN",
    "MEENA": "JUPITER",
}

FAKE_AYANAMSA = 24.0


def make_planet_state(
    body: str = "MOON",
    longitude: float = 105.0,
    speed: float = 1.0,
    retrograde: str | None = None,
) -> PlanetState:
    """A full ``PlanetState`` at a sidereal longitude (pure jyotish catalogs)."""
    lon = longitude % 360.0
    nakshatra = nakshatra_of(lon)
    rashi = rashi_of(lon)
    state = retrograde if retrograde is not None else ("RETROGRADE" if speed < 0.0 else "DIRECT")
    return PlanetState(
        body=BodyId(body),
        longitude_tropical=lon,
        longitude_sidereal=(lon - FAKE_AYANAMSA) % 360.0,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi,
        degree_in_rashi=degree_in_rashi(lon),
        nakshatra=nakshatra,
        nakshatra_lord=lord_of(nakshatra),
        pada=pada_of(lon),
        degree_in_nakshatra=degree_in_nakshatra(lon),
        latitude=0.0,
        speed_longitude=speed,
        retrograde=RetrogradeState(state),
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="test.astronomy",
        ephemeris_version="18",
    )


def make_pair_geometry(
    first: str,
    second: str,
    separation_deg: float,
    aspects: tuple[tuple[str, bool], ...] = (),
) -> PairGeometry:
    """A ``PairGeometry`` with the given shortest separation and aspect kinds."""
    from jyotish import AspectKind

    relationships = tuple(
        AspectRelationship(
            kind=AspectKind(kind),
            exact_angle_deg=0.0,
            separation_deg=separation_deg,
            distance_from_exact_deg=0.0,
            within_orb=within,
            orb_deg=8.0,
            applying_separating=ApplyingSeparating.NONE,
        )
        for kind, within in aspects
    )
    return PairGeometry(
        first=BodyId(first),
        second=BodyId(second),
        separation_deg=separation_deg,
        normalized_separation_deg=min(separation_deg, 360.0 - separation_deg),
        same_rashi=False,
        same_bhava=None,
        conjunction=any(kind == "CONJUNCTION" and within for kind, within in aspects),
        conjunction_distance_deg=0.0,
        aspects=relationships,
        orb_config={"conjunction": 8.0},
        config_snapshot=JyotishConfig(),
    )


def make_natal_chart(
    lagna_longitude: float = 105.0,
    bodies: dict[str, float] | None = None,
) -> NatalChart:
    """A whole-sign ``NatalChart``; ``bodies`` maps body -> sidereal longitude."""
    if bodies is None:
        bodies = {"MOON": 105.0, "SUN": 80.0}
    lagna_lon = lagna_longitude % 360.0
    lagna_rashi = rashi_of(lagna_lon)
    states = tuple(make_planet_state(body, lon) for body, lon in bodies.items())

    lagna = LagnaState(
        ascendant_longitude_deg=lagna_lon,
        dms=DmsValue(degrees=int(lagna_lon), minutes=0, seconds=0.0, sign=1),
        rashi=lagna_rashi,
        degree_in_rashi=degree_in_rashi(lagna_lon),
        nakshatra=nakshatra_of(lagna_lon),
        nakshatra_lord=lord_of(nakshatra_of(lagna_lon)),
        pada=pada_of(lagna_lon),
        degree_in_nakshatra=degree_in_nakshatra(lagna_lon),
        bhava_relationship=None,
        house_system=HouseSystem.WHOLE_SIGN,
    )

    lagna_rashi_index = list(RashiId).index(lagna_rashi)
    bhavas: list[Bhava] = []
    for house_number in range(1, 13):
        rashi_index = (lagna_rashi_index + house_number - 1) % 12
        rashi = list(RashiId)[rashi_index]
        start_deg = rashi_index * 30.0
        occupants = tuple(state.body for state in states if state.rashi == rashi)
        bhavas.append(
            Bhava(
                house_number=house_number,
                start_deg=start_deg,
                end_deg=start_deg + 30.0,
                rashi=rashi,
                house_lord=BodyId(RASHI_LORDS[rashi.value]),
                occupants=occupants,
                occupant_states=tuple(state for state in states if state.rashi == rashi),
                aspects=(),
                nakshatra=None,
            )
        )

    return NatalChart(
        birth_snapshot=BirthData(
            date="1990-06-15",
            time="10:00:00",
            timezone="Asia/Kolkata",
            latitude=28.6139,
            longitude=77.2090,
        ),
        lagna=lagna,
        bhavas=tuple(bhavas),
        planet_states=states,
        config=JyotishConfig(),
        provider_metadata=(
            ProviderMetadata(
                provider_id="test.astronomy",
                library_name="test",
                library_version="0.0.1",
                ephemeris_version="18",
            ),
        ),
    )


def make_transit_event(body: str = "JUPITER", kind: str = "RASHI_INGRESS") -> TransitEvent:
    return TransitEvent(
        body=BodyId(body),
        kind=TransitEventKind(kind),
        event_julian_day_ut=2451545.0,
        event_utc_iso="2000-01-01T12:00:00Z",
        boundary_deg=0.0,
        reached=None,
        direction=RetrogradeState.DIRECT,
        search_metadata=SearchMetadata(
            algorithm="test",
            sample_step_hours=6.0,
            tolerance_jd=1e-4,
            iterations=10,
            position_calls=20,
        ),
    )


def make_eclipse_event(kind: str = "SOLAR", classification: str = "TOTAL") -> EclipseEvent:
    return EclipseEvent(
        kind=EclipseKind(kind),
        classification=EclipseClassification(classification),
        maximum_jd_ut=2451545.0,
        maximum_utc_iso="2000-01-01T12:00:00Z",
        contacts=(EclipseContact("MAX", 2451545.0, "2000-01-01T12:00:00Z"),),
        magnitude=1.0,
        node_positions=(),
        solar_lunar_positions=(),
        geographic_visibility=None,
        pre_event_interval_days=0.5,
        post_event_interval_days=0.5,
        provider_id="test.eclipse",
        ephemeris_version="18",
    )


def write_catalog(
    tmp_path: Path,
    catalog_id: str,
    entries: list[dict[str, object]],
    version: str = "1.0.0",
) -> Path:
    """Write a checksummed temp catalog (mirrors the authoring canonicalization)."""
    document: dict[str, object] = {
        "catalog_id": catalog_id,
        "catalog_version": version,
        "schema_version": "0.3.0",
        "source_citation": "test fixture",
        "checksum_sha256": "",
        "entries": entries,
    }
    path = tmp_path / f"{catalog_id}.json"
    body = {k: v for k, v in document.items() if k != "checksum_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    document["checksum_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Snapshot helpers (canonical fact_snapshot dicts, FACT_VOCABULARY v1.1.0)
# --------------------------------------------------------------------------- #

#: Default chart geometry: a bphs-classical chart where the corrected BPHS
#: Gaja-Kesari rule (Jupiter in a kendra from the lagna, aspected by the
#: benefic Venus, not combust, exalted) is the ONLY yoga that matches.
DEFAULT_LAGNA_LONGITUDE = 95.0  # KARKA
DEFAULT_BODIES: dict[str, float] = {
    "MOON": 125.0,  # SIMHA
    "SUN": 65.0,  # MITHUNA
    "MERCURY": 175.0,  # KANYA
    "VENUS": 345.0,  # MEENA (9th from Jupiter: half glance on Jupiter)
    "JUPITER": 95.0,  # KARKA (1st from the KARKA lagna; exalted)
    "SATURN": 275.0,  # MAKARA
}


def _all_pairs(bodies: dict[str, float]) -> list[PairGeometry]:
    """Every unordered pair with its shortest-arc separation (unit tests)."""
    pairs: list[PairGeometry] = []
    items = sorted(bodies.items())
    for index, (first, lon_a) in enumerate(items):
        for second, lon_b in items[index + 1 :]:
            separation = min(abs(lon_a - lon_b), 360.0 - abs(lon_a - lon_b))
            pairs.append(make_pair_geometry(first, second, separation))
    return pairs


def base_snapshot(facts: object = None) -> dict[str, object]:
    """A rich canonical snapshot (enriched via the real facts registry)."""
    return yoga_snapshot(facts=facts)


def yoga_snapshot(
    bodies: dict[str, float] | None = None,
    lagna_longitude: float = DEFAULT_LAGNA_LONGITUDE,
    *,
    facts: object = None,
) -> dict[str, object]:
    """A YOGA_DEFINITION-friendly, facts-enriched canonical snapshot.

    ``bodies`` maps body -> sidereal longitude; the default geometry makes the
    corrected ``bphs.gajakesari.1`` the sole matching ACTIVE yoga rule. The
    snapshot is built from a real ``NatalChart`` through ``normalize_snapshot``
    with the committed facts registry, so the v1.1.0 derived fields
    (``nature``/``dignity``/``combusted``) are exercised by the unit suite.
    """
    from knowledge import load_facts, normalize_snapshot

    resolved = dict(DEFAULT_BODIES) if bodies is None else dict(bodies)
    registry = load_facts() if facts is None else facts
    chart = make_natal_chart(lagna_longitude=lagna_longitude, bodies=resolved)
    return normalize_snapshot(
        chart,
        pairs=_all_pairs(resolved),
        facts=registry,  # type: ignore[arg-type]
    )
