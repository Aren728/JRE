"""Cross-process determinism (TEST-PLAN §4, SPEC §16).

A child process runs the same synthesis and must produce byte-identical JSON
(mirrors the JRE-002/JRE-003 harness pattern). Runs fully offline against the
committed catalogs.
"""

from __future__ import annotations

import json
import subprocess
import sys

from knowledge import (
    KnowledgeService,
    RuleDomain,
    RuleQuery,
    result_to_json,
)

QUERY_CODE = """
import json
from knowledge import (
    KnowledgeService, RuleDomain, RuleQuery, result_to_json,
)
snapshot = {
    "planets": [
        {"body": "MOON", "rashi": "KARKA", "nakshatra": "PUSHYA", "pada": 1,
         "degree_in_rashi": 5.0, "retrograde": "DIRECT"},
        {"body": "JUPITER", "rashi": "DHANUSHA", "nakshatra": "MULA", "pada": 1,
         "degree_in_rashi": 2.0, "retrograde": "DIRECT"},
    ],
    "lagna": {"rashi": "KARKA", "nakshatra": "PUSHYA", "pada": 1},
    "relative_houses": {
        "LAGNA": {"MOON": 1, "JUPITER": 9},
        "MOON": {"MOON": 1, "JUPITER": 9},
    },
    "pairs": [
        {"first": "MOON", "second": "JUPITER", "conjunction": False,
         "separation_deg": 70.0, "aspects": []},
    ],
}
query = RuleQuery(domain=RuleDomain.YOGA_DEFINITION,
                  fact_snapshot=snapshot, profile_id="bphs-classical")
service = KnowledgeService()
print(result_to_json(service.synthesize(query)))
"""


def test_cross_process_byte_identity():
    parent = KnowledgeService()
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot={
            "planets": [
                {
                    "body": "MOON",
                    "rashi": "KARKA",
                    "nakshatra": "PUSHYA",
                    "pada": 1,
                    "degree_in_rashi": 5.0,
                    "retrograde": "DIRECT",
                },
                {
                    "body": "JUPITER",
                    "rashi": "DHANUSHA",
                    "nakshatra": "MULA",
                    "pada": 1,
                    "degree_in_rashi": 2.0,
                    "retrograde": "DIRECT",
                },
            ],
            "lagna": {"rashi": "KARKA", "nakshatra": "PUSHYA", "pada": 1},
            "relative_houses": {
                "LAGNA": {"MOON": 1, "JUPITER": 9},
                "MOON": {"MOON": 1, "JUPITER": 9},
            },
            "pairs": [
                {
                    "first": "MOON",
                    "second": "JUPITER",
                    "conjunction": False,
                    "separation_deg": 70.0,
                    "aspects": [],
                },
            ],
        },
        profile_id="bphs-classical",
    )
    parent_payload = result_to_json(parent.synthesize(query))

    completed = subprocess.run(
        [sys.executable, "-c", QUERY_CODE],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=".",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    child_payload = completed.stdout.strip()
    assert json.loads(child_payload) == json.loads(parent_payload)
    assert child_payload == parent_payload
