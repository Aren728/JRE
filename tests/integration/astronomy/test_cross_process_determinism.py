"""Cross-process determinism (Test plan §3, §7).

The same request computed in two separate interpreter processes must produce
byte-identical JSON output. Uses a short inline child program (no committed
script artifact required).
"""

from __future__ import annotations

import os
import subprocess
import sys

from tests.integration.astronomy.conftest import make_request

from astronomy.serialize import result_to_json

CHILD = (
    "import datetime as dt;"
    "from astronomy.service import AstronomicalService;"
    "from astronomy.models import EphemerisRequest;"
    "req = EphemerisRequest(date=dt.date(1990,6,15), time=dt.time(10,0,0),"
    " timezone='Asia/Kolkata', latitude=28.6139, longitude=77.2090);"
    "import json;"
    "print(json.dumps(AstronomicalService().compute(req).to_dict(), sort_keys=True))"
)


def _child_output() -> str:
    return subprocess.run(
        [sys.executable, "-c", CHILD],
        capture_output=True,
        text=True,
        check=True,
        cwd=os.getcwd(),
    ).stdout.strip()


def test_cross_process_determinism(service):
    parent = result_to_json(service.compute(make_request()))
    child_a = _child_output()
    child_b = _child_output()
    assert child_a == child_b  # child vs child
    # Parent and child must agree on all numeric content.
    import json

    parent_data = json.loads(parent)
    child_data = json.loads(child_a)
    assert parent_data["julian_day_ut"] == child_data["julian_day_ut"]
    assert parent_data["positions"] == child_data["positions"]
    assert parent_data["provider_run"] == child_data["provider_run"]
