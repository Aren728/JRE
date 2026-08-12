"""``SwissEphemerisProvider`` — the initial provider over the pysweph binding.

Behavior contract (Specialist spec §4, §8, §21–§22):

- Apparent geocentric ecliptic-of-date positions by default; ``TRUE`` adds
  ``FLG_TRUEPOS``.
- Speeds always computed (``FLG_SPEED``); retrograde/stationary from the
  longitude speed.
- Sidereal longitude is taken directly from the library's ``FLG_SIDEREAL``
  output (authoritative); ``ayanamsa_value`` is the library's reported value
  via ``get_ayanamsa_ut``. The two reconcile only to ~0.01° because the
  library applies the sidereal correction without nutation in longitude
  (documented deviation from Specialist spec §12's stricter claim).
- Rahu/Ketu derive from the lunar node chosen explicitly by
  ``config.node_type``; never mixed silently.
- Every ``swe.set_*`` call is executed per compute from the immutable config;
  a lock serializes calls (the C library keeps process-global state).
  Fallback to MOSEPH is never silent — the actual mode and files are recorded
  in ``ProviderRun``.
"""

from __future__ import annotations

import threading
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

import swisseph as swe

from ..coordinates import normalize_longitude
from ..errors import EphemerisDataError, EphemerisError
from ..models import (
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    ProviderMetadata,
    ProviderRun,
    classify_retrograde,
)
from ..provider import EphemerisProvider
from .constants import (
    AYANAMSA_TO_SIDM,
    BODY_TO_SWE,
    EPHEMERIS_VERSION,
    LIBRARY_NAME,
    NODE_TO_SWE,
    calculation_flags,
    mode_flag,
)
from .ephemeris import required_ephemeris_files, resolve_ephemeris_path, verify_ephemeris_dir

#: Longitude offset applied to the lunar node for Ketu (Rahu + 180°).
_NODE_OFFSET_KETU = 180.0


def _library_version() -> str:
    try:
        return _pkg_version("pysweph")
    except PackageNotFoundError:
        return str(getattr(swe, "version", "unknown"))


class SwissEphemerisProvider(EphemerisProvider):
    """Deterministic Swiss Ephemeris adapter (SWIEPH standard, MOSEPH fallback)."""

    provider_id = "swisseph.pysweph"

    def __init__(self, verify_checksums: bool = True) -> None:
        self._lock = threading.Lock()
        self._verify_checksums = verify_checksums
        self._verified_path: str | None = None
        self._metadata = ProviderMetadata(
            provider_id=self.provider_id,
            library_name=LIBRARY_NAME,
            library_version=_library_version(),
            ephemeris_version=EPHEMERIS_VERSION,
        )

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def compute(
        self, jd_ut: float, bodies: tuple[BodyId, ...], config: CalculationConfig
    ) -> ProviderRun:
        if not bodies:
            raise EphemerisError("bodies must not be empty")
        with self._lock:
            mode = self._resolve_mode(jd_ut, config)
            ayanamsa_value = self._ayanamsa(jd_ut, config)
            positions = tuple(
                self._compute_body(jd_ut, body, config, mode, ayanamsa_value)
                for body in bodies
            )
            files = required_ephemeris_files() if mode is EphemerisMode.SWIEPH else ()
            return ProviderRun(positions=positions, ephemeris_mode=mode, ephemeris_files=files)

    # ------------------------------------------------------------------ #
    # Mode resolution and fallback (never silent)
    # ------------------------------------------------------------------ #

    def _resolve_mode(
        self, jd_ut: float, config: CalculationConfig
    ) -> EphemerisMode:
        if config.ephemeris_mode is EphemerisMode.MOSEPH:
            return EphemerisMode.MOSEPH
        path = resolve_ephemeris_path(config.ephemeris_path)
        if path is None:
            return self._fallback_or_raise(
                config, f"SWIEPH data files not found (path={config.ephemeris_path!r} and defaults)"
            )
        try:
            if self._verified_path != str(path):
                verify_ephemeris_dir(path, verify_checksums=self._verify_checksums)
                self._verified_path = str(path)
            swe.set_ephe_path(str(path))
            self._probe_swieph(jd_ut, config)
            return EphemerisMode.SWIEPH
        except EphemerisDataError as exc:
            return self._fallback_or_raise(config, str(exc))

    def _fallback_or_raise(self, config: CalculationConfig, message: str) -> EphemerisMode:
        if config.allow_fallback:
            return EphemerisMode.MOSEPH
        raise EphemerisDataError(message)

    def _probe_swieph(self, jd_ut: float, config: CalculationConfig) -> None:
        flags = calculation_flags(EphemerisMode.SWIEPH, config.position_type)
        _xx, retflag, errmsg = swe.calc_ut(jd_ut, swe.SUN, flags)
        if not (retflag & swe.FLG_SWIEPH):
            raise EphemerisDataError(f"SWIEPH mode did not engage: retflag={retflag} {errmsg!r}")

    # ------------------------------------------------------------------ #
    # Ayanamsa
    # ------------------------------------------------------------------ #

    def _ayanamsa(self, jd_ut: float, config: CalculationConfig) -> float | None:
        if config.ayanamsa is None:
            return None
        override = config.ayanamsa_override
        t0, ayanamsa_t0 = override if override is not None else (0.0, 0.0)
        swe.set_sid_mode(AYANAMSA_TO_SIDM[config.ayanamsa], t0, ayanamsa_t0)
        return float(swe.get_ayanamsa_ut(jd_ut))

    # ------------------------------------------------------------------ #
    # Body computation
    # ------------------------------------------------------------------ #

    def _compute_body(
        self,
        jd_ut: float,
        body: BodyId,
        config: CalculationConfig,
        mode: EphemerisMode,
        ayanamsa_value: float | None,
    ) -> BodyPosition:
        flags = calculation_flags(mode, config.position_type)
        if body is BodyId.RAHU or body is BodyId.KETU:
            ipl = NODE_TO_SWE[config.node_type]
            offset = _NODE_OFFSET_KETU if body is BodyId.KETU else 0.0
        else:
            ipl = BODY_TO_SWE[body]
            offset = 0.0

        xx, retflag, errmsg = swe.calc_ut(jd_ut, ipl, flags)
        self._check_mode_flag(mode, retflag, errmsg, body)
        tropical = normalize_longitude(xx[0] + offset)

        sidereal: float | None = None
        if ayanamsa_value is not None:
            sid_xx, sid_ret, sid_err = swe.calc_ut(jd_ut, ipl, flags | swe.FLG_SIDEREAL)
            self._check_mode_flag(mode, sid_ret, sid_err, body)
            sidereal = normalize_longitude(sid_xx[0] + offset)

        return BodyPosition(
            body=body,
            longitude_tropical=tropical,
            longitude_sidereal=sidereal,
            latitude=xx[1],
            distance_au=xx[2],
            speed_longitude=xx[3],
            speed_latitude=xx[4],
            speed_distance=xx[5],
            retrograde=classify_retrograde(xx[3]),
            position_type=config.position_type,
            ayanamsa_value=ayanamsa_value,
        )

    def _check_mode_flag(
        self, mode: EphemerisMode, retflag: int, errmsg: str, body: BodyId
    ) -> None:
        if not (retflag & mode_flag(mode)):
            raise EphemerisDataError(
                f"{mode.value} mode not effective for {body.value}: retflag={retflag} {errmsg!r}"
            )
