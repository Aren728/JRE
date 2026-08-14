"""Envelope schema conformance (TEST-PLAN §5, DATA-CONTRACT §10, ADR-011).

The serialized payloads for ``Rule``, ``Source``, ``TraditionProfile`` and
``SynthesisResult`` conform to the contract: required keys present, no
unknown keys (``additionalProperties: false``), enum values from the pinned
sets, and the documented types. Mirrors the shape-check convention of
JRE-002/JRE-003 (no JSON-Schema validator dependency).
"""

from __future__ import annotations

from _kb_helpers import yoga_snapshot

from knowledge import KnowledgeService
from knowledge.models import RuleDomain, RuleQuery
from knowledge.serialize import result_to_dict

REQUIRED_RULE = [
    "rule_id",
    "domain",
    "summary",
    "condition",
    "conclusion",
    "provenance",
    "supporting_refs",
    "conflicts_with",
    "exception_for",
    "authority_tier",
    "status",
    "tradition_tags",
    "rule_version",
]
ALLOWED_RULE = set(REQUIRED_RULE)

RULE_DOMAINS = {
    "KARAKA",
    "BHAVA_MEANING",
    "DRISHTI",
    "YOGA_DEFINITION",
    "NAKSHATRA_CHARACTER",
    "DASHA_APPLICATION",
    "GOCHAR_SIGNIFICATION",
    "ECLIPSE_SIGNIFICATION",
    "GENERAL",
}
RULE_STATUSES = {"ACTIVE", "INACTIVE", "DEPRECATED", "SUPERSEDED"}

REQUIRED_SOURCE = [
    "source_id",
    "canonical_name",
    "common_name",
    "author",
    "period",
    "language",
    "lineage",
    "status",
    "editions",
    "catalog_version",
]
ALLOWED_SOURCE = set(REQUIRED_SOURCE)

REQUIRED_EDITION = [
    "edition_id",
    "title",
    "translator",
    "publisher",
    "year",
    "language",
    "notes",
]

REQUIRED_PROFILE = [
    "profile_id",
    "name",
    "version",
    "description",
    "included_sources",
    "source_priority",
    "conflict_policy",
    "domains",
    "passthrough_config",
]
ALLOWED_PROFILE = set(REQUIRED_PROFILE)

REQUIRED_SYNTHESIS = [
    "query",
    "profile",
    "matched_rules",
    "suppressed_rules",
    "conflicts",
    "provenance_index",
    "config",
    "search_metadata",
]
ALLOWED_SYNTHESIS = set(REQUIRED_SYNTHESIS)

REQUIRED_RESOLVED = [
    "rule",
    "precedence_key",
    "effective_weight",
    "credibility",
    "applicability",
    "status_note",
]


def _check_required_and_closed(payload: dict, required: list[str], allowed: set[str], label: str):
    for key in required:
        assert key in payload, f"{label} missing required key {key!r}"
    unknown = set(payload) - allowed
    assert not unknown, f"{label} has unknown keys (additionalProperties:false): {unknown}"


def _get_rule_dict(service: KnowledgeService) -> dict:
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    assert result.matched_rules, "expected at least one matched rule"
    resolved = result_to_dict(result)["matched_rules"][0]
    return resolved["rule"]


def test_rule_envelope_conformance(service):
    rule = _get_rule_dict(service)
    _check_required_and_closed(rule, REQUIRED_RULE, ALLOWED_RULE, "Rule")
    assert rule["domain"] in RULE_DOMAINS
    assert rule["status"] in RULE_STATUSES
    assert isinstance(rule["authority_tier"], int) and 1 <= rule["authority_tier"] <= 5
    assert isinstance(rule["rule_version"], str)
    assert isinstance(rule["conflicts_with"], list)
    assert isinstance(rule["exception_for"], list)
    assert isinstance(rule["supporting_refs"], list)
    # provenance ref closed shape
    prov = rule["provenance"]
    assert set(prov) <= {
        "source_id",
        "chapter",
        "verse_start",
        "verse_end",
        "edition_id",
        "commentary",
    }
    assert isinstance(prov["source_id"], str)
    # condition tree shape
    cond = rule["condition"]
    assert set(cond) <= {"combiner", "op", "path", "value", "children"}


def test_source_envelope_conformance():
    service = KnowledgeService()
    for source in service.sources():
        payload = result_to_dict(source)
        _check_required_and_closed(payload, REQUIRED_SOURCE, ALLOWED_SOURCE, "Source")
        assert payload["status"] in {"CANONICAL", "SUPPLEMENTAL", "REGIONAL", "HISTORICAL"}
        assert isinstance(payload["editions"], list)
        assert payload["editions"], f"source {payload['source_id']} has no edition records"
        for edition in payload["editions"]:
            assert set(edition) == set(REQUIRED_EDITION)
            assert isinstance(edition["edition_id"], str)
            assert isinstance(edition["title"], str)


def test_profile_envelope_conformance():
    service = KnowledgeService()
    for profile in service.profiles():
        payload = result_to_dict(profile)
        _check_required_and_closed(payload, REQUIRED_PROFILE, ALLOWED_PROFILE, "TraditionProfile")
        assert payload["conflict_policy"] in {"FIRST_WINS", "REPORT_ALL"}
        assert isinstance(payload["source_priority"], list)
        assert payload["source_priority"][0] == payload["included_sources"][0]


def test_synthesis_envelope_conformance(service):
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    payload = result_to_dict(result)
    _check_required_and_closed(payload, REQUIRED_SYNTHESIS, ALLOWED_SYNTHESIS, "SynthesisResult")
    # ResolvedRule closed shape
    for item in payload["matched_rules"]:
        _check_required_and_closed(item, REQUIRED_RESOLVED, set(REQUIRED_RESOLVED), "ResolvedRule")
        assert isinstance(item["precedence_key"], list)
        assert isinstance(item["effective_weight"], (int, float))
        assert 0.0 <= item["credibility"] <= 1.0
        assert item["applicability"] is True
    # search_metadata echo keys
    meta = payload["search_metadata"]
    assert set(meta) <= {
        "algorithm",
        "catalogs",
        "rules_evaluated",
        "rules_matched",
        "credibility_summary",
    }
    assert meta["algorithm"] == "profile-precedence-order"
    assert "fact_vocabulary" in meta["catalogs"]
    assert meta["catalogs"]["fact_vocabulary"] == "1.1.0"
    assert meta["catalogs"]["facts"] == "1.0.0"
