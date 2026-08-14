"""Serialization tests (TEST-PLAN §5, DATA-CONTRACT §9)."""

from __future__ import annotations

import json

from _kb_helpers import yoga_snapshot

from knowledge.models import RuleDomain, RuleQuery
from knowledge.serialize import (
    config_from_dict,
    provenance_from_dict,
    result_to_dict,
    result_to_json,
    rule_query_from_dict,
)


def test_enum_to_string_tuple_to_array_none_to_null(service):
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    payload = result_to_dict(result)
    assert payload["query"]["domain"] == "YOGA_DEFINITION"
    assert payload["profile"]["conflict_policy"] == "FIRST_WINS"
    assert payload["matched_rules"][0]["status_note"] is None
    assert isinstance(payload["matched_rules"][0]["precedence_key"], list)
    assert isinstance(payload["search_metadata"]["catalogs"], dict)


def test_float_round_trip_and_negative_zero():
    data = {"value": -0.0, "pi": 3.141592653589793}
    text = json.dumps(data)
    assert json.loads(text)["value"] == 0.0
    from knowledge.models import model_to_dict

    assert model_to_dict({"neg_zero": -0.0}) == {"neg_zero": 0.0}


def test_fact_snapshot_byte_round_trip(service):
    snapshot = yoga_snapshot()
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
    )
    result = service.synthesize(query)
    payload = json.loads(result_to_json(result))
    assert payload["query"]["fact_snapshot"] == snapshot


def test_rule_query_from_dict_round_trip():
    query = RuleQuery(
        domain=RuleDomain.DRISHTI,
        fact_snapshot={"pairs": []},
        profile_id="bphs-classical",
        include_suppressed=True,
    )
    rebuilt = rule_query_from_dict(
        {
            "domain": "DRISHTI",
            "fact_snapshot": {"pairs": []},
            "profile_id": "bphs-classical",
            "include_suppressed": True,
        }
    )
    assert rebuilt == query


def test_provenance_from_dict():
    ref = provenance_from_dict(
        {
            "source_id": "bphs",
            "chapter": "25",
            "verse_start": "12",
            "verse_end": None,
            "edition_id": "santhanam-2001",
            "commentary": None,
        }
    )
    assert ref.source_id == "bphs"
    assert ref.chapter == "25"
    assert ref.edition_id == "santhanam-2001"
    assert ref.verse_end is None


def test_config_from_dict_round_trip():
    from knowledge import load_config

    config = load_config()
    rebuilt = config_from_dict(
        {
            "default_profile_id": config.default_profile_id,
            "default_conflict_policy": config.default_conflict_policy.value,
            "rule_catalog_versions": config.rule_catalog_versions,
            "enforce_provenance": config.enforce_provenance,
            "verify_checksums": config.verify_checksums,
            "max_rules_per_synthesis": config.max_rules_per_synthesis,
            "provenance_completeness": config.provenance_completeness,
        }
    )
    assert rebuilt == config


def test_provenance_strings_stable(service):
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    payload = result_to_dict(result)
    first = payload["provenance_index"]
    second = json.loads(result_to_json(result))["provenance_index"]
    assert first == second
