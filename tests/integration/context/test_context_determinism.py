"""Cross-process determinism (TEST-PLAN row 22, SPEC §19).

A child process computes the same instant + natal + interval snapshots
and must produce byte-identical JSON (mirrors the JRE-002/003/004/005/006
harness).
"""

from __future__ import annotations

import json
import subprocess
import sys

from context import (
    ContextInstantRequest,
    ContextNatalRequest,
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
from bhava import BhavaService
from context import (
    ContextService, ContextInstantRequest, ContextNatalRequest, result_to_json,
)
from jyotish import BodyId

birth = BirthData(date="1990-06-15", time="10:00:00",
                  timezone="Asia/Kolkata", latitude=28.6139, longitude=77.2090)
svc = ContextService(JyotishService(), BhavaService())
instant = svc.snapshot_instant(ContextInstantRequest(
    instant_utc_iso="2026-06-15T12:00:00.000000Z",
    bodies=(BodyId.SUN, BodyId.MOON)))
natal = svc.snapshot_natal(ContextNatalRequest(birth=birth))
print(json.dumps({
    "instant": json.loads(result_to_json(instant)),
    "natal": json.loads(result_to_json(natal)),
}, sort_keys=True))
"""


def test_cross_process_byte_identity(context_service, birth) -> None:
    instant = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    natal = context_service.snapshot_natal(ContextNatalRequest(birth=birth))
    parent = json.dumps(
        {
            "instant": json.loads(result_to_json(instant)),
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


def test_repeated_in_process_identical(context_service, birth) -> None:
    a = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    b = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    assert result_to_json(a) == result_to_json(b)
