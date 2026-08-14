"""Config echo tests (TEST-PLAN §3, SPEC §11/§16).

The ``KnowledgeConfig`` snapshot embedded in ``SynthesisResult.config`` must
equal the input config; a custom config (bound at service construction per
SPEC §11) is honored end to end.
"""

from __future__ import annotations

from knowledge import (
    KnowledgeService,
    RuleDomain,
    RuleQuery,
    normalize_snapshot,
    result_to_dict,
)
from knowledge.config import load_config


def test_config_snapshot_equals_input_config(knowledge_service, jyotish_service, birth):
    config = load_config()
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    result = knowledge_service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=snapshot,
            profile_id="bphs-classical",
        )
    )
    assert result.config == config
    payload = result_to_dict(result)
    assert payload["config"] == result_to_dict(config)


def test_config_round_trips_through_json(knowledge_service, jyotish_service, birth):
    from knowledge.serialize import config_from_dict

    config = load_config()
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    result = knowledge_service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=snapshot,
            profile_id="bphs-classical",
        )
    )
    # config payload -> config object round-trips to equality
    rebuilt = config_from_dict(result_to_dict(result)["config"])
    assert rebuilt == config


def test_custom_config_is_honored(jyotish_service, birth):
    from dataclasses import replace

    config = replace(load_config(), max_rules_per_synthesis=5)
    service = KnowledgeService(config=config)
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=snapshot,
            profile_id="bphs-classical",
        )
    )
    assert result.config.max_rules_per_synthesis == 5
    assert len(result.matched_rules) <= 5
    assert result_to_dict(result)["config"]["max_rules_per_synthesis"] == 5
