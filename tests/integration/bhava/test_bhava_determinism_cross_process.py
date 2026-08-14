"""Cross-process determinism (TEST-PLAN §4/§7/§21).

A child process computes the same analysis and must produce
byte-identical JSON (mirrors the JRE-002/JRE-003/JRE-004 harness).
"""

from __future__ import annotations

import json
import subprocess
import sys

from bhava import result_to_json

ANALYSIS_CODE = """
import json
from jyotish import BirthData, JyotishService
from bhava import BhavaService, result_to_json

birth = BirthData(date="1990-06-15", time="10:00:00",
                  timezone="Asia/Kolkata", latitude=28.6139, longitude=77.2090)
svc = BhavaService(JyotishService())
result = svc.analyze(birth, house_systems=("WHOLE_SIGN", "PLACIDUS"))
print(result_to_json(result))
"""


def test_cross_process_byte_identity(bhava_service, birth) -> None:
    parent = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN", "PLACIDUS"))
    child = subprocess.run(
        [sys.executable, "-c", ANALYSIS_CODE],
        capture_output=True,
        text=True,
        check=True,
    )
    parent_json = result_to_json(parent)
    assert child.stdout.strip() == parent_json
    assert json.loads(child.stdout) == json.loads(parent_json)


def test_config_interleave_no_state_leakage(bhava_service, birth) -> None:
    """WHOLE_SIGN then PLACIDUS then WHOLE_SIGN — no cross-run state."""
    a = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN",))
    b = bhava_service.analyze(birth, house_systems=("PLACIDUS",))
    c = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN",))
    assert result_to_json(a) == result_to_json(c)
    assert result_to_json(a) != result_to_json(b)
