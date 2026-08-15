"""Cross-process determinism (TEST-PLAN row 22, SPEC §19).

A child process computes the same instant + interval results and must
produce byte-identical JSON (mirrors the JRE-002/003/004/005 harness).
"""

from __future__ import annotations

import json
import subprocess
import sys

from gochar import (
    GocharInstantRequest,
    GocharIntervalRequest,
    GocharNatalRequest,
    result_to_json,
)
from jyotish import BirthData, BodyId

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)

CODE = """
import json
from jyotish import BirthData, JyotishService
from gochar import (
    GocharService, GocharInstantRequest, GocharIntervalRequest,
    GocharNatalRequest, result_to_json,
)
from jyotish import BodyId

birth = BirthData(date="1990-06-15", time="10:00:00",
                  timezone="Asia/Kolkata", latitude=28.6139, longitude=77.2090)
svc = GocharService(JyotishService())
instant = svc.analyze_instant(GocharInstantRequest(
    instant_utc_iso="2026-06-15T12:00:00.000000Z",
    bodies=(BodyId.SUN, BodyId.MOON)))
interval = svc.analyze_interval(GocharIntervalRequest(
    start_utc_iso="2026-06-01T00:00:00.000000Z",
    end_utc_iso="2026-08-01T00:00:00.000000Z",
    bodies=(BodyId.MOON, BodyId.SUN)))
natal = svc.analyze_natal(GocharNatalRequest(
    birth=birth, instant_utc_iso="2026-06-15T12:00:00.000000Z",
    bodies=(BodyId.SUN, BodyId.MOON)))
print(json.dumps({
    "instant": json.loads(result_to_json(instant)),
    "interval": json.loads(result_to_json(interval)),
    "natal": json.loads(result_to_json(natal)),
}, sort_keys=True))
"""


def test_cross_process_byte_identity(gochar_service, birth) -> None:
    instant = gochar_service.analyze_instant(
        GocharInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    interval = gochar_service.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-08-01T00:00:00.000000Z",
            bodies=(BodyId.MOON, BodyId.SUN),
        )
    )
    natal = gochar_service.analyze_natal(
        GocharNatalRequest(
            birth=birth,
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    parent = json.dumps(
        {
            "instant": json.loads(result_to_json(instant)),
            "interval": json.loads(result_to_json(interval)),
            "natal": json.loads(result_to_json(natal)),
        },
        sort_keys=True,
    )
    child = subprocess.run(
        [sys.executable, "-c", CODE],
        capture_output=True,
        text=True,
        check=True,
    )
    assert child.stdout.strip() == parent


def test_repeated_in_process_identical(gochar_service, birth) -> None:
    a = gochar_service.analyze_instant(
        GocharInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    b = gochar_service.analyze_instant(
        GocharInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    assert result_to_json(a) == result_to_json(b)
