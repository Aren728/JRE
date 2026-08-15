"""Error taxonomy + input invariants (TEST-PLAN §2 rows 4-5, SPEC §7/§8,
DC §3).

Four error types with the documented hierarchy; malformed instants,
start > end, empty bodies, unknown references/house systems, and
``natal_house_series`` without an anchor all raise the exact typed errors
— never raw ``ValueError``/``KeyError``/``AttributeError``.
"""

from __future__ import annotations

import pytest

from gochar import (
    GocharComputationError,
    GocharConfig,
    GocharError,
    GocharInstantRequest,
    GocharIntervalRequest,
    GocharNatalRequest,
    GocharService,
    InvalidGocharConfigError,
    InvalidGocharRequestError,
)
from gochar.derive import civil_split
from jyotish import BirthData, BodyId

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)


def test_error_hierarchy() -> None:
    assert issubclass(InvalidGocharConfigError, GocharError)
    assert issubclass(InvalidGocharRequestError, GocharError)
    assert issubclass(GocharComputationError, GocharError)
    assert issubclass(GocharError, Exception)


def test_invalid_instant_forms() -> None:
    for bad in (
        "not-a-date",
        "2026-06-15",  # date-only rejected (SPEC §8)
        "2026-06-15T",  # no time
        "2026-13-45T12:00:00Z",  # out of range
        "",
    ):
        with pytest.raises(InvalidGocharRequestError):
            civil_split(bad)
    # Offset-bearing strings are rejected too (must be UTC).
    with pytest.raises(InvalidGocharRequestError):
        civil_split("2026-06-15T12:00:00+05:30")


def test_interval_start_after_end() -> None:
    svc = GocharService()
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-16T00:00:00.000000Z",
        end_utc_iso="2026-06-15T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
    )
    with pytest.raises(InvalidGocharRequestError, match="start.*end|end.*start"):
        svc.analyze_interval(req)


def test_empty_bodies_rejected() -> None:
    svc = GocharService()
    with pytest.raises(InvalidGocharRequestError, match="bodies"):
        svc.analyze_instant(
            GocharInstantRequest(instant_utc_iso="2026-06-15T00:00:00.000000Z", bodies=())
        )
    with pytest.raises(InvalidGocharRequestError, match="bodies"):
        svc.analyze_interval(
            GocharIntervalRequest(
                start_utc_iso="2026-06-15T00:00:00.000000Z",
                end_utc_iso="2026-06-16T00:00:00.000000Z",
                bodies=(),
            )
        )


def test_unknown_body_rejected() -> None:
    from gochar.serialize import instant_request_from_dict

    with pytest.raises(InvalidGocharRequestError, match="body"):
        instant_request_from_dict(
            {"instant_utc_iso": "2026-06-15T00:00:00.000000Z", "bodies": ["PLUTO"]}
        )


def test_unknown_reference_point_request() -> None:
    svc = GocharService()
    req = GocharNatalRequest(
        birth=BIRTH,
        instant_utc_iso="2026-06-15T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
        reference_point="BOGUS",
    )
    with pytest.raises(InvalidGocharRequestError, match="reference_point"):
        svc.analyze_natal(req)


def test_unknown_house_system_config() -> None:
    with pytest.raises(InvalidGocharConfigError, match="house_system"):
        GocharConfig(house_system="BOGUS")


def test_natal_house_series_requires_anchor() -> None:
    svc = GocharService()
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-15T00:00:00.000000Z",
        end_utc_iso="2026-06-16T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(natal_house_series=True),
    )
    with pytest.raises(InvalidGocharRequestError, match="natal_anchor"):
        svc.analyze_interval(req)


def test_no_raw_exceptions_escape() -> None:
    """SPEC §7 — malformed input never raises raw builtins."""
    svc = GocharService()
    with pytest.raises(GocharError):
        svc.analyze_instant(
            GocharInstantRequest(instant_utc_iso="garbage", bodies=(BodyId.SUN,))
        )
    from gochar.serialize import interval_request_from_dict

    with pytest.raises(GocharError):
        interval_request_from_dict(
            {"start_utc_iso": "garbage", "end_utc_iso": "garbage", "bodies": ["SUN"]}
        )


def test_delegated_failure_wrapped(fake_service) -> None:
    """SPEC §7 — a failing delegated computation is wrapped as
    ``GocharComputationError`` with the wrapped class name in the message."""

    class ExplodingService(fake_service.__class__):
        def planetary_state(self, *args, **kwargs):
            from jyotish import TransitSearchError

            raise TransitSearchError("boom")

    svc = GocharService(ExplodingService())
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T00:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    with pytest.raises(GocharComputationError, match="TransitSearchError"):
        svc.analyze_instant(req)
