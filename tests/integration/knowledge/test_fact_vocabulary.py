"""Fact-vocabulary resolution against real JRE-003 payloads (TEST-PLAN §2).

Every pinned vocabulary path — including the v1.1.0 ``relative_house``
(all-body references) and the derived-fact paths ``nature``/``dignity``/
``combusted``/``aspect_strength`` (ADR-012) — resolves against a genuine
``JyotishService`` output, and ``FACT_VOCABULARY_VERSION`` is echoed in
synthesis metadata (SPEC §16).
"""

from __future__ import annotations

from knowledge import (
    RuleDomain,
    RuleQuery,
    normalize_snapshot,
    result_to_dict,
)
from knowledge.schema import (
    FACT_VOCABULARY,
    FACT_VOCABULARY_VERSION,
    evaluate,
    parse_path,
)


def test_fact_vocabulary_version_echoed(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart, facts=knowledge_service.facts)
    result = knowledge_service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=snapshot,
            profile_id="bphs-classical",
        )
    )
    catalogs = result.search_metadata.catalogs
    assert catalogs.get("fact_vocabulary") == FACT_VOCABULARY_VERSION
    assert catalogs.get("facts") == knowledge_service.facts.catalog_version
    # and it round-trips through JSON serialization
    payload = result_to_dict(result)
    assert payload["search_metadata"]["catalogs"]["fact_vocabulary"] == FACT_VOCABULARY_VERSION


def test_every_vocabulary_path_resolves_against_real_payload(
    knowledge_service, jyotish_service, birth
):

    from astronomy.models import BodyId
    from jyotish.models import TransitEventKind

    chart = jyotish_service.chart(birth)
    pairs = jyotish_service.pair_geometry(chart.planet_states)
    # real transit + eclipse events make the transit()/eclipse sections present
    transits = jyotish_service.events_between(
        "2011-05-01T00:00:00Z",
        "2011-05-15T00:00:00Z",
        (BodyId.JUPITER,),
        (TransitEventKind.RASHI_INGRESS,),
    )
    eclipses = jyotish_service.eclipses(
        "1991-06-01T00:00:00Z", "1991-08-01T00:00:00Z"
    )  # 1991-07-11 solar
    assert eclipses, "expected the 1991-07-11 solar eclipse in range"
    snapshot = normalize_snapshot(
        (chart, *transits, *eclipses), pairs=pairs, facts=knowledge_service.facts
    )
    assert "transits" in snapshot
    assert "eclipses" in snapshot

    concretes = {
        "planet(<BODY>).rashi": "planet(MOON).rashi",
        "planet(<BODY>).nakshatra": "planet(SUN).nakshatra",
        "planet(<BODY>).pada": "planet(JUPITER).pada",
        "planet(<BODY>).degree_in_rashi": "planet(MOON).degree_in_rashi",
        "planet(<BODY>).retrograde": "planet(MARS).retrograde",
        "lagna.rashi": "lagna.rashi",
        "lagna.nakshatra": "lagna.nakshatra",
        "lagna.pada": "lagna.pada",
        "bhava(<N>).house_lord": "bhava(9).house_lord",
        "bhava(<N>).occupants": "bhava(7).occupants",
        "relative_house(<BODY>, <REF>)": "relative_house(MOON, JUPITER)",
        "pair(<A>,<B>).conjunction": "pair(MOON, JUPITER).conjunction",
        "pair(<A>,<B>).separation_deg": "pair(MOON, SUN).separation_deg",
        "pair(<A>,<B>).aspects": "pair(MARS, SATURN).aspects",
        "pair(<A>,<B>).aspect_strength": "pair(SATURN, MOON).aspect_strength",
        "planet(<BODY>).nature": "planet(JUPITER).nature",
        "planet(<BODY>).dignity": "planet(JUPITER).dignity",
        "planet(<BODY>).combusted": "planet(MOON).combusted",
        "transit(<BODY>).kind": "transit(JUPITER).kind",
        "eclipse.kind": "eclipse.kind",
        "eclipse.classification": "eclipse.classification",
    }

    # every template parses against the pinned table
    for template in FACT_VOCABULARY:
        assert template in concretes, f"vocabulary path {template} missing a concrete"

    # every concrete resolves (evaluates without raising, returns a value)
    from knowledge.models import ConditionOp, RuleCondition

    for template, concrete in concretes.items():
        value_type, _multi = FACT_VOCABULARY[template]
        # EXISTS-style probe: existence never raises and is a bool
        cond = RuleCondition(
            combiner=None,
            op=ConditionOp.EXISTS,
            path=concrete,
            value=None,
            children=(),
        )
        result = evaluate(cond, snapshot)
        assert isinstance(result, bool), concrete
        spec = parse_path(concrete)
        assert spec.value_type == value_type


def test_relative_house_resolves_from_real_chart(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart, facts=knowledge_service.facts)
    assert "relative_houses" in snapshot
    # default reference is LAGNA
    lagna_ref = snapshot["relative_houses"].get("LAGNA")
    assert lagna_ref is not None
    for house in lagna_ref.values():
        assert isinstance(house, int)
        assert 1 <= house <= 12
    # v1.1.0: a reference map exists for every body present in the chart
    for body in {entry["body"] for entry in snapshot["planets"]}:
        ref_map = snapshot["relative_houses"].get(body)
        assert ref_map is not None, body
        for house in ref_map.values():
            assert isinstance(house, int)
            assert 1 <= house <= 12


def test_derived_facts_present_with_real_payload(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    pairs = jyotish_service.pair_geometry(chart.planet_states)
    snapshot = normalize_snapshot(chart, pairs=pairs, facts=knowledge_service.facts)
    for entry in snapshot["planets"]:
        assert "nature" in entry, entry["body"]
        assert "combusted" in entry, entry["body"]
        if entry["body"] not in ("RAHU", "KETU"):
            assert "dignity" in entry, entry["body"]
