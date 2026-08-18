"""Cross-process determinism (normative specification §17, §26).

A child process computes the same Varga chart from identical inputs and
must produce byte-identical JSON — mirrors the JRE-002..007 harnesses.
No wall-clock, randomness, or environment dependence.
"""

from __future__ import annotations

import json
import subprocess
import sys

from tests.unit.varga.conftest import make_state

from jyotish import BodyId, RashiId
from varga import VargaService, result_to_json

STATES = (
    make_state(RashiId.MESHA, 5.0, body=BodyId.SUN),
    make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.MOON),
    make_state(RashiId.SIMHA, 25.0, body=BodyId.MARS),
    make_state(RashiId.VRISHABHA, 10.0, body=BodyId.VENUS),
    make_state(RashiId.MITHUNA, 17.0, body=BodyId.JUPITER),
)

CODE = """
import json
from jyotish import BodyId, RashiId
from tests.unit.varga.conftest import make_state
from varga import VargaService, result_to_json

STATES = (
    make_state(RashiId.MESHA, 5.0, body=BodyId.SUN),
    make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.MOON),
    make_state(RashiId.SIMHA, 25.0, body=BodyId.MARS),
    make_state(RashiId.VRISHABHA, 10.0, body=BodyId.VENUS),
    make_state(RashiId.MITHUNA, 17.0, body=BodyId.JUPITER),
)
svc = VargaService()
for varga_id in ("D2", "D9", "D30", "D60"):
    print(result_to_json(svc.compute_varga_chart(STATES, varga_id)))
"""


def test_cross_process_byte_identical() -> None:
    svc = VargaService()
    expected = [
        result_to_json(svc.compute_varga_chart(STATES, varga_id))
        for varga_id in ("D2", "D9", "D30", "D60")
    ]
    proc = subprocess.run(
        [sys.executable, "-c", CODE],
        capture_output=True,
        text=True,
        check=True,
        cwd="/home/abhyram/JRE",
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert lines == expected


def test_serialization_deterministic_and_lossless() -> None:
    from varga import result_to_dict

    svc = VargaService()
    chart = svc.compute_varga_chart(STATES, "D45")
    first = result_to_json(chart)
    second = result_to_json(chart)
    assert first == second
    # JSON round-trip is value-identical to the dict form.
    assert json.loads(first) == result_to_dict(chart)
    # No wall-clock / environment leakage in the serialized result.
    assert "wall" not in first
    assert "environ" not in first
    assert "getpid" not in first
