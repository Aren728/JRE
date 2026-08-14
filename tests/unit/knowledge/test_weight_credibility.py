"""Weight/credibility tests (TEST-PLAN requirement 10, SPEC §10)."""

from __future__ import annotations

from knowledge import KnowledgeService, load_config, load_rule_catalogs, load_sources
from knowledge.models import (
    RuleDomain,
    RuleQuery,
    provenance_completeness_level,
)
from knowledge.precedence import (
    count_atoms,
    credibility,
    credibility_summary,
    effective_weight,
    source_priority_rank,
)


def _expected_weight(rule, profile, config):
    """Independent reimplementation of SPEC §10.1."""
    rank = source_priority_rank(profile, rule.provenance.source_id)
    specificity = count_atoms(rule.condition)
    n_sources = len(profile.source_priority)
    return round(
        config.weight_authority_coeff * rule.authority_tier
        + config.weight_specificity_coeff * specificity
        + config.weight_source_rank_coeff * (n_sources - rank),
        4,
    )


def _expected_credibility(rule, config):
    """Independent reimplementation of SPEC §10.2."""
    level = provenance_completeness_level(rule.provenance)
    completeness = config.provenance_completeness[level]
    specificity = count_atoms(rule.condition)
    return round(
        config.credibility_authority_weight * (rule.authority_tier / 5.0)
        + config.credibility_provenance_weight * completeness
        + config.credibility_specificity_weight * min(specificity / 5.0, 1.0),
        4,
    )


def test_formulas_match_independent_reimplementation():
    config = load_config()
    profile = KnowledgeService().get_profile("bphs-classical")
    rules = load_rule_catalogs(registry=load_sources()).all()
    for rule in rules:
        assert effective_weight(rule, profile, config) == _expected_weight(rule, profile, config)
        assert credibility(rule, config) == _expected_credibility(rule, config)
        assert 0.0 <= credibility(rule, config) <= 1.0


def test_known_hand_computed_values():
    config = load_config()
    profile = KnowledgeService().get_profile("bphs-classical")
    rule = load_rule_catalogs(registry=load_sources()).get("bphs.gajakesari.1")
    assert rule is not None
    # Y1 (corrected BPHS ch. 36 v. 3-4): tier 4, 12 atoms, bphs rank 0 in a
    # 4-source profile -> 1.0*4 + 0.5*12 + 0.05*4 = 10.2
    assert effective_weight(rule, profile, config) == 10.2
    # 0.55*0.8 + 0.30*1.0 + 0.15*1.0 (min(12/5,1)=1) = 0.89
    assert credibility(rule, config) == 0.89


def test_credibility_summary(service):
    from _kb_helpers import yoga_snapshot

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    summary = result.search_metadata.credibility_summary
    assert summary["n"] == len(result.matched_rules)
    values = [item.credibility for item in result.matched_rules]
    assert summary["min"] == round(min(values), 4)
    assert summary["max"] == round(max(values), 4)
    assert summary["mean"] == round(sum(values) / len(values), 4)


def test_credibility_summary_empty():
    assert credibility_summary([]) == {"mean": None, "min": None, "max": None, "n": 0}


def test_order_follows_precedence_key_not_weight(service):
    """effective_weight is display-only; order follows the §8 key."""
    from _kb_helpers import yoga_snapshot

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(
            bodies={
                "MOON": 35.0,
                "SUN": 65.0,
                "MERCURY": 70.0,
                "VENUS": 345.0,
                "JUPITER": 125.0,
                "SATURN": 275.0,
            }
        ),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    keys = [item.precedence_key for item in result.matched_rules]
    assert keys == sorted(keys)
