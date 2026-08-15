"""Golden fixture test (TEST-PLAN row 21, DC §7).

The committed golden ``GocharNatalResult`` JSON uses hex-float
representation so the comparison survives repr changes; ``GOLDEN_VERSION``
pins the producing environment (same policy as JRE-002/003/004/005).
"""

from __future__ import annotations

import json
from pathlib import Path

from gochar import GOLDEN_VERSION, GocharConfig, GocharNatalRequest, result_to_dict
from jyotish import BodyId

GOLDEN_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "gochar"
    / "golden"
    / "natal_golden.json"
)


def _hexify(obj):
    if isinstance(obj, float):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _hexify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_hexify(v) for v in obj]
    return obj


def test_golden_natal_matches(gochar_service, birth) -> None:
    assert GOLDEN_PATH.is_file(), f"missing golden fixture {GOLDEN_PATH}"
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert golden["golden_version"] == GOLDEN_VERSION

    result = gochar_service.analyze_natal(
        GocharNatalRequest(
            birth=birth,
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS),
            config=GocharConfig(aspect_echo=True),
        )
    )
    assert _hexify(result_to_dict(result)) == golden["result"]


def test_golden_hand_computed_markers(gochar_service, birth) -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["result"]
    assert golden["reference_point"] == "LAGNA"
    prov = golden["provenance"]
    assert prov["derivation_id"] == "gochar.natal.v1"
    assert prov["source_layers"] == ["JRE-002", "JRE-003", "JRE-005"]
    assert "JRE-002" in prov["source_layers"]
    assert golden["transit_to_natal_aspects"] is not None
