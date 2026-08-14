"""Golden fixture test (TEST-PLAN §8).

The committed golden ``SynthesisResult`` JSON uses hex-float representation
so the comparison survives repr changes; ``GOLDEN_VERSION`` pins the
producing environment (same policy as JRE-002/JRE-003). A mismatch means
either the engine output changed (needs a versioned golden bump) or the
environment changed.
"""

from __future__ import annotations

import json
from pathlib import Path

from _kb_helpers import yoga_snapshot

from knowledge import KnowledgeService, RuleDomain, RuleQuery
from knowledge.serialize import result_to_dict

GOLDEN_VERSION = "2.0.0"
GOLDEN_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "knowledge" / "synthesis_golden.json"
)


def _hexify(obj):
    if isinstance(obj, float):
        return obj.hex()
    if isinstance(obj, dict):
        return {k: _hexify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_hexify(v) for v in obj]
    return obj


def test_golden_synthesis_result_matches():
    assert GOLDEN_PATH.is_file(), f"missing golden fixture {GOLDEN_PATH}"
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert golden["golden_version"] == GOLDEN_VERSION

    service = KnowledgeService()
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    payload = result_to_dict(result)
    # drop the opaque snapshot echo (inputs are not part of the output golden)
    payload["query"] = {
        "domain": "YOGA_DEFINITION",
        "profile_id": "bphs-classical",
        "include_suppressed": False,
    }
    assert _hexify(payload) == golden["synthesis"]


def test_golden_hand_computed_markers():
    """Sanity anchors for the golden: hand-computed Y1 order + weight/credibility.

    The corrected BPHS Gaja-Kesari (ch. 36 v. 3-4) carries 12 condition atoms,
    tier 4 and full provenance: weight = 1.0*4 + 0.5*12 + 0.05*4 = 10.2;
    credibility = 0.55*0.8 + 0.30*1.0 + 0.15*1.0 = 0.89.
    """
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["synthesis"]
    matched = golden["matched_rules"]
    assert [item["rule"]["rule_id"] for item in matched] == ["bphs.gajakesari.1"]
    assert golden["search_metadata"]["rules_evaluated"] == 5
    assert golden["search_metadata"]["rules_matched"] == 1
    assert matched[0]["credibility"] == (0.89).hex()
    assert matched[0]["effective_weight"] == (10.2).hex()
