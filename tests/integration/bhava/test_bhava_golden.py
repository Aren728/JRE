"""Golden fixture test (TEST-PLAN §6/§17).

The committed golden ``HouseAnalysisResult`` JSON uses hex-float
representation so the comparison survives repr changes; ``GOLDEN_VERSION``
pins the producing environment (same policy as JRE-002/003/004).
"""

from __future__ import annotations

import json
from pathlib import Path

from bhava import GOLDEN_VERSION, result_to_dict

GOLDEN_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "bhava" / "golden" / "analysis_golden.json"
)


def _hexify(obj):
    if isinstance(obj, float):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _hexify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_hexify(v) for v in obj]
    return obj


def test_golden_analysis_matches(bhava_service, birth) -> None:
    assert GOLDEN_PATH.is_file(), f"missing golden fixture {GOLDEN_PATH}"
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert golden["golden_version"] == GOLDEN_VERSION

    result = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN",))
    assert _hexify(result_to_dict(result)) == golden["analysis"]


def test_golden_hand_computed_markers(bhava_service, birth) -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["analysis"]
    analysis = golden["analyses"][0]
    assert analysis["house_system"] == "WHOLE_SIGN"
    assert analysis["empty_house_count"] == 5
    # LAGNA/ASC rows equal (JRE-004 pin).
    assert analysis["relative_house_table"]["ASC"] == analysis["relative_house_table"]["LAGNA"]
    # Every planet fact carries full provenance with catalog pins.
    fact = analysis["planet_house_facts"][0]
    assert fact["derivation"]["source_catalog_versions"]["rashi"]
    assert fact["derivation"]["source_catalog_versions"]["nakshatra"]
