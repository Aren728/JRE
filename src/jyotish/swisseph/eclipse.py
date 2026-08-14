"""``SwissEphemerisEclipseProvider`` — the initial eclipse adapter.

Behavior contract (Specialist §4.2, ADR-006):

- Uses the binding's named ``ECL_*`` constants via the separate ``ecltype``
  parameter (empirically verified with pysweph 2.10.03; supersedes ADR-006's
  raw-hex premise).
- ``tret`` layout (verified against NASA canon for the 1991-07-11 total solar
  and 1990-02-09 total lunar eclipses): see the mapping tables below.
- Deterministic: same interval + config => identical events and times.
- Data-only: no causation/significance fields (static gate enforced).
- ``node_positions`` / ``solar_lunar_positions`` are filled by the service
  (which owns the astronomy position path) after ``find_eclipses`` returns.
"""

from __future__ import annotations

import threading

import swisseph as swe

from ..eclipse import EclipseProvider
from ..errors import EclipseError
from ..models import (
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    GeographicVisibility,
    JyotishConfig,
)
from .constants import (
    ECL_ALLTYPES_LUNAR,
    ECL_ALLTYPES_SOLAR,
    ECL_ANNULAR,
    ECL_ANNULAR_TOTAL,
    ECL_PARTIAL,
    ECL_PENUMBRAL,
    ECL_TOTAL,
    EPHEMERIS_VERSION,
    FLAG_SWIEPH,
)

#: Sun/Moon and node bodies whose positions are reported at eclipse maximum.
_POSITION_BODIES = ("SUN", "MOON", "RAHU", "KETU")

#: Reference geographic position for global searches (equator, sea level).
_GEOPOS = (0.0, 0.0, 0.0)


class SwissEphemerisEclipseProvider(EclipseProvider):
    """Deterministic Swiss Ephemeris eclipse adapter."""

    provider_id = "swisseph.pysweph.eclipse"

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def find_eclipses(
        self,
        jd_start: float,
        jd_end: float,
        kind: EclipseKind | None,
        config: JyotishConfig,
    ) -> tuple[EclipseEvent, ...]:
        if jd_start > jd_end:
            raise EclipseError(f"jd_start {jd_start} must be <= jd_end {jd_end}")
        kinds: tuple[EclipseKind, ...] = (
            (EclipseKind.SOLAR, EclipseKind.LUNAR)
            if kind is None
            else (kind,)
        )
        events: list[EclipseEvent] = []
        with self._lock:
            for ecl_kind in kinds:
                events.extend(self._search(ecl_kind, jd_start, jd_end))
        events.sort(key=lambda e: e.maximum_jd_ut)
        return tuple(events)

    # ------------------------------------------------------------------ #

    def _search(self, kind: EclipseKind, jd_start: float, jd_end: float) -> list[EclipseEvent]:
        result: list[EclipseEvent] = []
        jd = jd_start
        if kind is EclipseKind.SOLAR:
            ecltype = ECL_ALLTYPES_SOLAR
            while jd <= jd_end:
                res, tret = swe.sol_eclipse_when_glob(jd, FLAG_SWIEPH, ecltype, False)
                if res == 0:
                    break
                maximum = tret[0]
                if maximum > jd_end:
                    break
                result.append(self._solar_event(tret, res))
                jd = maximum + 0.5  # move past this event
        else:
            ecltype = ECL_ALLTYPES_LUNAR
            while jd <= jd_end:
                res, tret = swe.lun_eclipse_when(jd, FLAG_SWIEPH, ecltype, False)
                if res == 0:
                    break
                maximum = tret[0]
                if maximum > jd_end:
                    break
                result.append(self._lunar_event(tret, res))
                jd = maximum + 0.5
        return result

    # ------------------------------------------------------------------ #
    # Event builders
    # ------------------------------------------------------------------ #

    def _solar_event(self, tret: tuple[float, ...], res: int) -> EclipseEvent:
        maximum = tret[0]
        classification = _solar_classification(res)
        contacts = _solar_contacts(tret)
        pre, post = _intervals(tret[2], maximum, tret[3])
        magnitude, visibility = self._solar_geometry(maximum)
        return EclipseEvent(
            kind=EclipseKind.SOLAR,
            classification=classification,
            maximum_jd_ut=maximum,
            maximum_utc_iso=_iso(maximum),
            contacts=contacts,
            magnitude=magnitude,
            node_positions=(),
            solar_lunar_positions=(),
            geographic_visibility=visibility,
            pre_event_interval_days=pre,
            post_event_interval_days=post,
            provider_id=self.provider_id,
            ephemeris_version=EPHEMERIS_VERSION,
        )

    def _lunar_event(self, tret: tuple[float, ...], res: int) -> EclipseEvent:
        maximum = tret[0]
        classification = _lunar_classification(res)
        contacts = _lunar_contacts(tret)
        # pre/post use the penumbral phase extents where available.
        p_begin = tret[6] if tret[6] else tret[2]
        p_end = tret[7] if tret[7] else tret[3]
        pre, post = _intervals(p_begin, maximum, p_end)
        magnitude = self._lunar_magnitude(maximum)
        return EclipseEvent(
            kind=EclipseKind.LUNAR,
            classification=classification,
            maximum_jd_ut=maximum,
            maximum_utc_iso=_iso(maximum),
            contacts=contacts,
            magnitude=magnitude,
            node_positions=(),
            solar_lunar_positions=(),
            geographic_visibility=None,
            pre_event_interval_days=pre,
            post_event_interval_days=post,
            provider_id=self.provider_id,
            ephemeris_version=EPHEMERIS_VERSION,
        )

    def _solar_geometry(self, maximum: float) -> tuple[float, GeographicVisibility | None]:
        """Solar magnitude + central-path visibility where available."""
        try:
            retflags, geopos, attr = swe.sol_eclipse_where(maximum, FLAG_SWIEPH)
            magnitude = float(attr[0])
        except (TypeError, ValueError):
            return 0.0, None
        if retflags == 0 or not geopos:
            return magnitude, None
        lon, lat = float(geopos[0]), float(geopos[1])
        if lon == 0.0 and lat == 0.0:
            return magnitude, None
        return magnitude, GeographicVisibility(
            latitude_deg=lat, longitude_deg=lon, description="central path"
        )

    def _lunar_magnitude(self, maximum: float) -> float:
        try:
            retflag, attr = swe.lun_eclipse_how(maximum, _GEOPOS, FLAG_SWIEPH)
        except (TypeError, ValueError):
            return 0.0
        if retflag == 0:
            return 0.0
        return float(attr[0])


# --------------------------------------------------------------------------- #
# Mapping helpers (Specialist §4.2 — empirically pinned layout)
# --------------------------------------------------------------------------- #


def _solar_classification(res: int) -> EclipseClassification:
    if res & ECL_ANNULAR_TOTAL:
        return EclipseClassification.HYBRID
    if res & ECL_TOTAL:
        return EclipseClassification.TOTAL
    if res & ECL_ANNULAR:
        return EclipseClassification.ANNULAR
    if res & ECL_PARTIAL:
        return EclipseClassification.PARTIAL
    raise EclipseError(f"unclassifiable solar eclipse res flags: {res:#x}")


def _lunar_classification(res: int) -> EclipseClassification:
    if res & ECL_TOTAL:
        return EclipseClassification.TOTAL
    if res & ECL_PARTIAL:
        return EclipseClassification.PARTIAL
    if res & ECL_PENUMBRAL:
        return EclipseClassification.PENUMBRAL
    raise EclipseError(f"unclassifiable lunar eclipse res flags: {res:#x}")


def _contact_if_nonzero(phase: str, jd: float) -> EclipseContact | None:
    """Build a contact only when the binding returned a real instant (JD > 0).

    The binding returns 0.0 for phase slots that do not occur for this
    eclipse (e.g. no P1/P4 slots for a penumbral-only lunar eclipse).
    """
    if not jd or jd <= 0.0:
        return None
    return EclipseContact(phase, jd, _iso(jd))


def _solar_contacts(tret: tuple[float, ...]) -> tuple[EclipseContact, ...]:
    """Solar tret layout: [2]=P1, [4]=P2 (central only), [0]=MAX, [5]=P3, [3]=P4."""
    contacts: list[EclipseContact] = []
    p1 = _contact_if_nonzero("P1", tret[2])
    if p1:
        contacts.append(p1)
    p2 = _contact_if_nonzero("P2", tret[4])
    if p2:
        contacts.append(p2)
    contacts.append(EclipseContact("MAX", tret[0], _iso(tret[0])))
    p3 = _contact_if_nonzero("P3", tret[5])
    if p3:
        contacts.append(p3)
    p4 = _contact_if_nonzero("P4", tret[3])
    if p4:
        contacts.append(p4)
    return tuple(contacts)


def _lunar_contacts(tret: tuple[float, ...]) -> tuple[EclipseContact, ...]:
    """Lunar tret layout: [2]=P1, [4]=U2 (total only), [0]=MAX, [5]=U3, [3]=P4."""
    contacts: list[EclipseContact] = []
    p1 = _contact_if_nonzero("P1", tret[2])
    if p1:
        contacts.append(p1)
    u2 = _contact_if_nonzero("U2", tret[4])
    if u2:
        contacts.append(u2)
    contacts.append(EclipseContact("MAX", tret[0], _iso(tret[0])))
    u3 = _contact_if_nonzero("U3", tret[5])
    if u3:
        contacts.append(u3)
    p4 = _contact_if_nonzero("P4", tret[3])
    if p4:
        contacts.append(p4)
    pen_b = _contact_if_nonzero("PENUMBRAL_BEGIN", tret[6])
    if pen_b:
        contacts.append(pen_b)
    pen_e = _contact_if_nonzero("PENUMBRAL_END", tret[7])
    if pen_e:
        contacts.append(pen_e)
    return tuple(contacts)


def _intervals(begin: float, maximum: float, end: float) -> tuple[float, float]:
    """(pre, post) temporal extents in days — data, not interpretation."""
    return (maximum - begin) if begin else 0.0, (end - maximum) if end else 0.0


def _iso(jd_ut: float) -> str:
    from ..transit import jd_to_iso_utc

    return jd_to_iso_utc(jd_ut)
