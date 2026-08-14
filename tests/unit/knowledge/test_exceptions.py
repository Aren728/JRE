"""Exception (`exception_for`) tests (TEST-PLAN requirement 9, SPEC §9.2)."""

from __future__ import annotations

import pytest
from _kb_helpers import write_catalog

from knowledge.errors import ConflictResolutionError, RuleSchemaError
from knowledge.models import RuleDomain, RuleQuery
from knowledge.rules import load_rule_catalogs
from knowledge.sources import load_sources

#: Moon in the 6th from Jupiter (Sakata) with the Moon in a kendra from the
#: ascendant (cancellation): both the Sakata rule and its Phaladīpikā
#: cancellation exception match.
SAKATA_CANCELLED_BODIES = {
    "MOON": 200.0,  # TULA (6th from Jupiter@VRISHABHA; 4th from the KARKA lagna)
    "SUN": 65.0,
    "MERCURY": 70.0,
    "VENUS": 345.0,
    "JUPITER": 40.0,  # VRISHABHA
    "SATURN": 275.0,
}

#: Same Moon-from-Jupiter geometry with a MITHUNA lagna -> the Moon is 5th
#: from the ascendant (not a kendra), so the cancellation does NOT match.
SAKATA_NOT_CANCELLED_LAGNA = 65.0  # MITHUNA


def test_exception_overrides_base_rule(service):
    from _kb_helpers import yoga_snapshot

    # Moon 6th from Jupiter AND in a kendra from the ascendant: the verified
    # Phaladīpikā Sakata cancellation (exception) suppresses the Sakata rule
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(bodies=SAKATA_CANCELLED_BODIES),
        profile_id="bphs-classical",
        include_suppressed=True,
    )
    result = service.synthesize(query)
    matched = [item.rule.rule_id for item in result.matched_rules]
    suppressed = [item.rule.rule_id for item in result.suppressed_rules]
    assert "phaladeepika.sakata-cancellation.8" in matched
    # the Sakata base rule is overridden by the cancellation exception
    assert "phaladeepika.sakata.3" not in matched
    assert "phaladeepika.sakata.3" in suppressed
    notes = {item.rule.rule_id: item.status_note for item in result.suppressed_rules}
    assert notes["phaladeepika.sakata.3"] == (
        "overridden by exception phaladeepika.sakata-cancellation.8"
    )
    records = [record for record in result.conflicts if record.resolution == "exception"]
    assert any(
        record.rule_a_id == "phaladeepika.sakata-cancellation.8"
        and record.rule_b_id == "phaladeepika.sakata.3"
        for record in records
    )


def test_exception_does_not_fire_when_not_matching(service):
    from _kb_helpers import yoga_snapshot

    # Moon 6th from Jupiter but 5th from the (MITHUNA) lagna: Sakata stands
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(
            bodies=SAKATA_CANCELLED_BODIES, lagna_longitude=SAKATA_NOT_CANCELLED_LAGNA
        ),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    assert "phaladeepika.sakata.3" in [item.rule.rule_id for item in result.matched_rules]
    assert "phaladeepika.sakata-cancellation.8" not in [
        item.rule.rule_id for item in result.matched_rules
    ]
    assert result.suppressed_rules == ()
    assert not [record for record in result.conflicts if record.resolution == "exception"]


def test_exception_cycle_rejected(tmp_path):
    rules_path = write_catalog(
        tmp_path,
        "rules:test",
        [
            {
                "rule_id": "e1.1",
                "domain": "GENERAL",
                "summary": "e1",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "e1", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "1",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": ["e2.2"],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            },
            {
                "rule_id": "e2.2",
                "domain": "GENERAL",
                "summary": "e2",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "e2", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "2",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": ["e1.1"],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            },
        ],
    )
    with pytest.raises(ConflictResolutionError):
        load_rule_catalogs(paths=[rules_path], registry=load_sources())


def test_exception_unknown_target_rejected(tmp_path):
    rules_path = write_catalog(
        tmp_path,
        "rules:test",
        [
            {
                "rule_id": "e1.1",
                "domain": "GENERAL",
                "summary": "e1",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "e1", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "1",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": ["missing.rule"],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            }
        ],
    )
    with pytest.raises(RuleSchemaError):
        load_rule_catalogs(paths=[rules_path], registry=load_sources())
