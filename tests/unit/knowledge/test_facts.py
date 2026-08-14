"""Facts-layer tests (FACT_VOCABULARY v1.1.0, ADR-012).

Covers the derived classical facts (nature, dignity, combustion, aspect
strength, rashi lords, natural friendship), the all-body ``relative_house``
reference set, and the corrected catalog semantics (Gaja-Kesari variants,
Sakata + cancellation, the preserved Y1-Y5 conflict, INACTIVE rules) through
the public contract (``load_facts``, ``derive_*``, ``enrich_snapshot``,
``normalize_snapshot``, ``evaluate``, ``KnowledgeService.synthesize``).
"""

from __future__ import annotations

from _kb_helpers import yoga_snapshot

from knowledge import (
    FACTS_CATALOG_VERSION,
    KnowledgeService,
    derive_aspect_strength,
    derive_combusted,
    derive_dignity,
    derive_nature,
    load_facts,
    normalize_snapshot,
)
from knowledge.models import RuleDomain, RuleQuery
from knowledge.schema import (
    FACT_VOCABULARY,
    FACT_VOCABULARY_VERSION,
    evaluate,
    parse_path,
)

FACTS = load_facts()


# --------------------------------------------------------------------------- #
# Catalog integrity
# --------------------------------------------------------------------------- #


def test_facts_catalog_version_pinned():
    assert FACTS_CATALOG_VERSION == "1.0.0"
    assert FACTS.catalog_version == "1.0.0"


def test_every_fact_id_has_full_provenance():
    for _fact_id, ref in FACTS.provenance.items():
        assert ref.source_id == "bphs"
        assert ref.edition_id == "santhanam-2001"
        assert ref.chapter is not None
        assert ref.verse_start is not None


# --------------------------------------------------------------------------- #
# Nature (BPHS ch. 3 v. 11)
# --------------------------------------------------------------------------- #


def test_natural_benefic_malefic_classification():
    assert derive_nature(FACTS, "SUN") == "MALEFIC"
    assert derive_nature(FACTS, "SATURN") == "MALEFIC"
    assert derive_nature(FACTS, "MARS") == "MALEFIC"
    assert derive_nature(FACTS, "RAHU") == "MALEFIC"
    assert derive_nature(FACTS, "KETU") == "MALEFIC"
    assert derive_nature(FACTS, "MOON") == "BENEFIC"
    assert derive_nature(FACTS, "JUPITER") == "BENEFIC"
    assert derive_nature(FACTS, "VENUS") == "BENEFIC"
    # Mercury is conditionally a benefic -> NEUTRAL (ch. 3 v. 11)
    assert derive_nature(FACTS, "MERCURY") == "NEUTRAL"


# --------------------------------------------------------------------------- #
# Dignity (BPHS ch. 3 v. 49-55, ch. 4)
# --------------------------------------------------------------------------- #


def test_dignity_scale():
    assert derive_dignity(FACTS, "JUPITER", "KARKA") == "EXALTED"  # ch. 3 v. 49
    assert derive_dignity(FACTS, "SATURN", "MESHA") == "DEBILITATED"  # 7th from TULA
    assert derive_dignity(FACTS, "SUN", "SIMHA") == "MULATRIKONA"  # checked before OWN
    assert derive_dignity(FACTS, "VENUS", "VRISHABHA") == "OWN"  # ch. 4 ruler
    assert derive_dignity(FACTS, "MARS", "VRISHCHIKA") == "OWN"
    assert derive_dignity(FACTS, "SUN", "KARKA") == "FRIEND"  # KARKA lord MOON is SUN's friend
    assert derive_dignity(FACTS, "SUN", "VRISHABHA") == "ENEMY"  # VENUS is SUN's enemy
    assert derive_dignity(FACTS, "SUN", "KANYA") == "NEUTRAL"  # MERCURY neutral to SUN
    # the nodes are outside the classical grade table (seven grahas only)
    assert derive_dignity(FACTS, "RAHU", "MESHA") is None
    assert derive_dignity(FACTS, "KETU", "MESHA") is None


def test_dignity_in_rule_condition():
    # the corrected Gaja-Kesari requires Jupiter NOT debilitated/enemy
    snapshot = yoga_snapshot(bodies={"MOON": 125.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 275.0})
    # Jupiter in MAKARA is DEBILITATED -> Y1 must not match
    from knowledge.models import ConditionOp, RuleCondition

    cond = RuleCondition(
        combiner=None,
        op=ConditionOp.EQ,
        path="planet(JUPITER).dignity",
        value="DEBILITATED",
        children=(),
    )
    assert evaluate(cond, snapshot)
    result = KnowledgeService().synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
        )
    )
    assert "bphs.gajakesari.1" not in [item.rule.rule_id for item in result.matched_rules]


# --------------------------------------------------------------------------- #
# Combustion (BPHS ch. 7 v. 28-29)
# --------------------------------------------------------------------------- #


def test_combustion_thresholds_direct_and_retrograde():
    # Moon: 12 deg direct; Mars 17/8; Mercury 14/12; Jupiter 11; Venus 10/8; Saturn 16
    assert derive_combusted(FACTS, "MOON", "DIRECT", 12.0) is True
    assert derive_combusted(FACTS, "MOON", "DIRECT", 12.1) is False
    assert derive_combusted(FACTS, "MARS", "DIRECT", 17.0) is True
    assert derive_combusted(FACTS, "MARS", "RETROGRADE", 8.0) is True
    assert derive_combusted(FACTS, "MARS", "RETROGRADE", 9.0) is False
    assert derive_combusted(FACTS, "JUPITER", "DIRECT", 11.0) is True
    # absent retrograde column -> same threshold as direct (never *more* combust)
    assert derive_combusted(FACTS, "JUPITER", "RETROGRADE", 11.0) is True
    assert derive_combusted(FACTS, "JUPITER", "RETROGRADE", 12.0) is False
    assert derive_combusted(FACTS, "VENUS", "DIRECT", 10.0) is True
    assert derive_combusted(FACTS, "VENUS", "RETROGRADE", 9.0) is False


def test_nodes_and_sun_never_combust():
    # outside the table: Sun itself and the nodes never combust
    assert derive_combusted(FACTS, "SUN", "DIRECT", 0.5) is False
    assert derive_combusted(FACTS, "RAHU", "DIRECT", 0.5) is False
    assert derive_combusted(FACTS, "KETU", "DIRECT", 0.5) is False


def test_combusted_field_uniform_in_enriched_snapshot():
    snapshot = yoga_snapshot()
    for entry in snapshot["planets"]:
        assert "combusted" in entry, entry["body"]
        assert isinstance(entry["combusted"], bool)


# --------------------------------------------------------------------------- #
# Aspect strength (BPHS ch. 26 v. 2-5, Phaladīpikā ch. 2 v. 23)
# --------------------------------------------------------------------------- #


def test_aspect_strength_positions():
    assert derive_aspect_strength(FACTS, "SUN", 3) == "QUARTER"
    assert derive_aspect_strength(FACTS, "SUN", 5) == "HALF"
    assert derive_aspect_strength(FACTS, "SUN", 8) == "THREE_QUARTER"
    assert derive_aspect_strength(FACTS, "SUN", 7) == "FULL"
    assert derive_aspect_strength(FACTS, "SUN", 2) is None  # no classical aspect


def test_aspect_doctrine_schema_matches_facts_catalog():
    """ADR-012: the evaluator's pinned doctrine and the facts catalog table
    are two copies of one doctrine — they must agree exactly."""
    from knowledge.schema import ASPECT_POSITION_STRENGTHS, SPECIAL_ASPECT_POSITIONS

    schema_positions = {k: tuple(v) for k, v in ASPECT_POSITION_STRENGTHS.items()}
    schema_special = {k: tuple(v) for k, v in SPECIAL_ASPECT_POSITIONS.items()}
    assert schema_positions == FACTS.aspect_strength_positions
    assert schema_special == FACTS.special_aspects


def test_special_full_aspects():
    assert derive_aspect_strength(FACTS, "SATURN", 3) == "FULL"
    assert derive_aspect_strength(FACTS, "SATURN", 10) == "FULL"
    assert derive_aspect_strength(FACTS, "JUPITER", 9) == "FULL"
    assert derive_aspect_strength(FACTS, "MARS", 4) == "FULL"
    assert derive_aspect_strength(FACTS, "SATURN", 5) == "HALF"  # non-special stays half


def test_aspect_strength_directional_through_catalog():
    # Jupiter is 9th from Venus (half glance by Venus) while Venus is 5th from
    # Jupiter (special-FULL glance by Jupiter): direction follows the path arg.
    snapshot = {
        "pairs": [{"first": "JUPITER", "second": "VENUS", "conjunction": False}],
        "relative_houses": {"VENUS": {"JUPITER": 9}, "JUPITER": {"VENUS": 5}},
    }
    from knowledge.models import ConditionOp, RuleCondition

    def atom(path: str, value: object) -> RuleCondition:
        return RuleCondition(combiner=None, op=ConditionOp.EQ, path=path, value=value, children=())

    assert evaluate(atom("pair(VENUS, JUPITER).aspect_strength", "HALF"), snapshot)
    assert evaluate(atom("pair(JUPITER, VENUS).aspect_strength", "FULL"), snapshot)
    assert not evaluate(atom("pair(VENUS, JUPITER).aspect_strength", "FULL"), snapshot)


# --------------------------------------------------------------------------- #
# Rashi lords + friendship (BPHS ch. 4, ch. 3 v. 55)
# --------------------------------------------------------------------------- #


def test_rashi_lords():
    assert FACTS.rashi_lords["MESHA"] == "MARS"
    assert FACTS.rashi_lords["KARKA"] == "MOON"
    assert FACTS.rashi_lords["KUMBHA"] == "SATURN"
    assert FACTS.rashi_lords["MEENA"] == "JUPITER"


def test_friendship_tables_symmetric():
    for body, relation in FACTS.friendship.items():
        assert set(relation) == {"friends", "enemies", "neutral"}
        # friendship is symmetric at the class level: if X is a friend of Y
        # then Y lists X in one of friends/enemies/neutral (never missing)
        others = [key for key, rel in FACTS.friendship.items() if key != body]
        for other in others:
            listed = relation["friends"] + relation["enemies"] + relation["neutral"]
            assert other in listed, f"{other} unlisted for {body}"


# The expected table below is encoded independently from the verified BPHS
# ch. 3 v. 55 reading (Santhanam ed., verse + Notes + the edition's published
# table): friends = lords of the 2nd/4th/5th/8th/9th/12th from the planet's
# moolatrikona PLUS the lord of its exaltation sign; enemies = lords of the
# 3rd/6th/7th/10th/11th; a planet on both lists is NEUTRAL (the Notes' worked
# example: "Saturn becomes equal to Mars"); the planet itself is never listed.
FRIENDSHIP_EXPECTED = {
    "SUN": {
        "friends": ("MOON", "MARS", "JUPITER"),
        "enemies": ("VENUS", "SATURN"),
        "neutral": ("MERCURY",),
    },
    "MOON": {
        "friends": ("SUN", "MERCURY"),
        "enemies": (),
        "neutral": ("MARS", "JUPITER", "VENUS", "SATURN"),
    },
    "MARS": {
        "friends": ("SUN", "MOON", "JUPITER"),
        "enemies": ("MERCURY",),
        "neutral": ("VENUS", "SATURN"),
    },
    "MERCURY": {
        "friends": ("SUN", "VENUS"),
        "enemies": ("MOON",),
        "neutral": ("MARS", "JUPITER", "SATURN"),
    },
    "JUPITER": {
        "friends": ("SUN", "MOON", "MARS"),
        "enemies": ("MERCURY", "VENUS"),
        "neutral": ("SATURN",),
    },
    "VENUS": {
        "friends": ("MERCURY", "SATURN"),
        "enemies": ("SUN", "MOON"),
        "neutral": ("MARS", "JUPITER"),
    },
    "SATURN": {
        "friends": ("MERCURY", "VENUS"),
        "enemies": ("SUN", "MOON", "MARS"),
        "neutral": ("JUPITER",),
    },
}


def test_natural_friendship_values_match_verse_55():
    """Every value of the committed table matches the verified verse-55 reading."""
    for body in FRIENDSHIP_EXPECTED:
        assert FACTS.friendship[body] == FRIENDSHIP_EXPECTED[body], (
            f"{body} friendship row deviates from the BPHS ch. 3 v. 55 reading"
        )


def test_natural_friendship_self_excluded():
    """A planet is never listed in its own friends/enemies/neutral lists."""
    for body, relation in FACTS.friendship.items():
        for role in ("friends", "enemies", "neutral"):
            assert body not in relation[role], f"{body} listed as its own {role}"


def test_natural_friendship_mutual_friendship():
    assert "MOON" in FACTS.friendship["SUN"]["friends"]
    assert "SUN" in FACTS.friendship["MOON"]["friends"]
    assert "MERCURY" in FACTS.friendship["VENUS"]["friends"]
    assert "VENUS" in FACTS.friendship["MERCURY"]["friends"]


def test_natural_friendship_mutual_enmity():
    assert "SATURN" in FACTS.friendship["SUN"]["enemies"]
    assert "SUN" in FACTS.friendship["SATURN"]["enemies"]
    assert "VENUS" in FACTS.friendship["SUN"]["enemies"]
    assert "SUN" in FACTS.friendship["VENUS"]["enemies"]


def test_natural_friendship_mercury_moon_one_sided():
    # Mercury is an enemy of the Moon, but the Moon lists Mercury as a friend
    # (no enemies of the Moon at all per the verse-55 reading)
    assert "MOON" in FACTS.friendship["MERCURY"]["enemies"]
    assert "MERCURY" in FACTS.friendship["MOON"]["friends"]
    assert FACTS.friendship["MOON"]["enemies"] == ()


def test_natural_friendship_asymmetry():
    """Friend/enemy relations need not be reciprocal (Venus↔Moon, Sun↔Mercury)."""
    assert "MOON" in FACTS.friendship["VENUS"]["enemies"]
    assert "VENUS" in FACTS.friendship["MOON"]["neutral"]
    assert "SUN" in FACTS.friendship["MERCURY"]["friends"]
    assert "MERCURY" in FACTS.friendship["SUN"]["neutral"]


def test_natural_friendship_both_conflict_resolves_neutral():
    """A planet on both the friend and enemy lists is NEUTRAL (v. 55 + Notes)."""
    assert "VENUS" in FACTS.friendship["MOON"]["neutral"]
    assert "SATURN" in FACTS.friendship["MARS"]["neutral"]
    assert "JUPITER" in FACTS.friendship["VENUS"]["neutral"]
    assert "SATURN" in FACTS.friendship["JUPITER"]["neutral"]


def test_natural_friendship_exaltation_lord_friend_when_unconflicted():
    """The exaltation lord is a friend when it is not also an enemy (v. 55 Notes)."""
    assert "MARS" in FACTS.friendship["SUN"]["friends"]
    assert "VENUS" in FACTS.friendship["SATURN"]["friends"]
    assert "MOON" in FACTS.friendship["JUPITER"]["friends"]


# --------------------------------------------------------------------------- #
# All-body relative_house references (v1.1.0)
# --------------------------------------------------------------------------- #


def test_relative_house_accepts_every_body_as_reference():
    for body in ("SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"):
        spec = parse_path(f"relative_house(MOON, {body})")
        assert spec.args == ("MOON", body)


def test_normalized_snapshot_spans_body_references():
    snapshot = yoga_snapshot()
    relative = snapshot["relative_houses"]
    assert "LAGNA" in relative and "ASC" in relative
    # every placed body is present as a reference and as a target
    placed = {entry["body"] for entry in snapshot["planets"]}
    for ref in placed:
        assert ref in relative, f"missing reference map for {ref}"
        assert set(relative[ref]) == placed


def test_sakata_uses_jupiter_reference():
    # the Phaladīpikā Sakata/Kesari rules count from JUPITER, not the lagna;
    # the MITHUNA lagna keeps the Moon out of a kendra so Sakata stands
    snapshot = yoga_snapshot(
        bodies={"MOON": 200.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 40.0},
        lagna_longitude=65.0,
    )
    assert snapshot["relative_houses"]["JUPITER"]["MOON"] == 6
    result = KnowledgeService().synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
        )
    )
    assert "phaladeepika.sakata.3" in [item.rule.rule_id for item in result.matched_rules]


# --------------------------------------------------------------------------- #
# Corrected Gaja-Kesari variants (BPHS ch. 36 v. 3-4 vs JP Adhyāya VII v. 116)
# --------------------------------------------------------------------------- #


def test_bphs_gajakesari_requires_benefic_aspect_and_no_combustion():
    service = KnowledgeService()

    # default geometry: Jupiter kendra from the KARKA lagna, aspected by Venus,
    # exalted, not combust -> Y1 matches, Y5 (JP) does not
    default = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(),
            profile_id="bphs-classical",
        )
    )
    ids = [item.rule.rule_id for item in default.matched_rules]
    assert "bphs.gajakesari.1" in ids
    assert "jataka-parijata.gajakesari.5" not in ids

    # combust Jupiter (separation from SUN <= 11 deg): Y1 must NOT match
    combust = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(
                bodies={"MOON": 125.0, "SUN": 95.0, "VENUS": 345.0, "JUPITER": 90.0}
            ),
            profile_id="bphs-classical",
        )
    )
    assert "bphs.gajakesari.1" not in [item.rule.rule_id for item in combust.matched_rules]

    # debilitated Jupiter (MAKARA) with no other match: Y1 must NOT match
    debilitated = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(
                bodies={"MOON": 125.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 275.0}
            ),
            profile_id="bphs-classical",
        )
    )
    assert "bphs.gajakesari.1" not in [item.rule.rule_id for item in debilitated.matched_rules]


def test_jp_gajakesari_second_form_moon_aspect_by_benefics():
    # JP second form: Moon aspected by Venus/Jupiter/Mercury, not combust,
    # and not "depressed" (debilitated) — Adhyāya VII sloka 116.
    # Venus in MEENA puts the TULA Moon in its 7th (full aspect); the Sun is
    # far from the Moon (135 deg) so the Moon is not combust; Jupiter is 3rd
    # from the Moon so the first (kendra) arm does not interfere.
    service = KnowledgeService()
    snapshot = yoga_snapshot(
        bodies={"MOON": 200.0, "SUN": 65.0, "MERCURY": 150.0, "VENUS": 330.0, "JUPITER": 260.0}
    )
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
        )
    )
    assert "jataka-parijata.gajakesari.5" in [item.rule.rule_id for item in result.matched_rules]


def test_jp_gajakesari_second_form_requires_moon_not_debilitated():
    # VALIDATOR re-check: the sloka's "without being depressed or obscured by
    # the Sun" is two conditions. A DEBILITATED Moon (VRISHCHIKA) that is
    # aspected by Venus (8th) and not combust must NOT form the second form.
    service = KnowledgeService()
    snapshot = yoga_snapshot(
        bodies={"MOON": 230.0, "SUN": 65.0, "MERCURY": 150.0, "VENUS": 20.0, "JUPITER": 260.0}
    )
    moon = next(entry for entry in snapshot["planets"] if entry["body"] == "MOON")
    assert moon["dignity"] == "DEBILITATED"
    assert moon["combusted"] is False
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
        )
    )
    assert "jataka-parijata.gajakesari.5" not in [
        item.rule.rule_id for item in result.matched_rules
    ]


# --------------------------------------------------------------------------- #
# Sakata + cancellation (Phaladīpikā ch. 6)
# --------------------------------------------------------------------------- #


def test_sakata_formed_and_cancelled():
    service = KnowledgeService()

    # Moon 6th from Jupiter and in a kendra from the lagna -> cancelled
    cancelled = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(
                bodies={"MOON": 200.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 40.0}
            ),
            profile_id="bphs-classical",
        )
    )
    assert "phaladeepika.sakata-cancellation.8" in [
        item.rule.rule_id for item in cancelled.matched_rules
    ]
    assert "phaladeepika.sakata.3" not in [
        item.rule.rule_id for item in cancelled.matched_rules
    ]

    # Moon 6th from Jupiter but 5th from the (MITHUNA) lagna -> Sakata stands
    standing = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(
                bodies={"MOON": 200.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 40.0},
                lagna_longitude=65.0,
            ),
            profile_id="bphs-classical",
        )
    )
    assert "phaladeepika.sakata.3" in [item.rule.rule_id for item in standing.matched_rules]
    assert "phaladeepika.sakata-cancellation.8" not in [
        item.rule.rule_id for item in standing.matched_rules
    ]


# --------------------------------------------------------------------------- #
# Preserved Y1-Y5 conflict
# --------------------------------------------------------------------------- #

#: Both corrected Gaja-Kesari rules match: Y1 (Jupiter kendra from the Moon via
#: its lagna/Moon kendra arms, aspected by benefic Venus) and Y5 (JP first
#: form: Jupiter kendra from the Moon). Their mutual ``conflicts_with`` is
#: preserved after the re-authoring (bphs wins in the bphs-classical profile).
CONFLICT_BODIES = {
    "MOON": 35.0,  # VRISHABHA
    "SUN": 65.0,  # MITHUNA
    "MERCURY": 70.0,  # MITHUNA
    "VENUS": 345.0,  # MEENA (8th from Jupiter -> three-quarter glance)
    "JUPITER": 125.0,  # SIMHA (4th from the Moon -> kendra; friend sign)
    "SATURN": 275.0,  # MAKARA
}


def test_y1_y5_conflict_preserved_and_resolved_first_wins(service):
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION,
            fact_snapshot=yoga_snapshot(bodies=CONFLICT_BODIES),
            profile_id="bphs-classical",
            include_suppressed=True,
        )
    )
    matched = [item.rule.rule_id for item in result.matched_rules]
    suppressed = [item.rule.rule_id for item in result.suppressed_rules]
    assert "bphs.gajakesari.1" in matched
    assert "jataka-parijata.gajakesari.5" in suppressed
    records = [record for record in result.conflicts if record.resolution == "first wins"]
    assert any(
        record.rule_a_id == "bphs.gajakesari.1"
        and record.rule_b_id == "jataka-parijata.gajakesari.5"
        for record in records
    )


# --------------------------------------------------------------------------- #
# INACTIVE rules (NEEDS-RESEARCH)
# --------------------------------------------------------------------------- #


def test_inactive_rules_never_match(service):
    from knowledge import load_rule_catalogs, load_sources

    rules = load_rule_catalogs(registry=load_sources())
    inactive = {
        "bphs.budhaditya.2",
        "prasna-marga.moon-lagna.6",
    }
    for rule_id in inactive:
        rule = rules.get(rule_id)
        assert rule is not None
        assert rule.status.value == "INACTIVE"
        assert "NEEDS-RESEARCH" in rule.provenance.commentary
    # a Sun-Mercury conjunction snapshot must NOT fire the inactive rule
    snapshot = yoga_snapshot(bodies={"MOON": 125.0, "SUN": 95.0, "MERCURY": 90.0, "VENUS": 345.0})
    result = service.synthesize(
        RuleQuery(
            domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot, profile_id="bphs-classical"
        )
    )
    assert "bphs.budhaditya.2" not in [item.rule.rule_id for item in result.matched_rules]


# --------------------------------------------------------------------------- #
# Vocabulary pin + enrichment determinism
# --------------------------------------------------------------------------- #


def test_vocabulary_version_and_paths_pinned():
    assert FACT_VOCABULARY_VERSION == "1.1.0"
    for path in (
        "planet(<BODY>).nature",
        "planet(<BODY>).dignity",
        "planet(<BODY>).combusted",
        "pair(<A>,<B>).aspect_strength",
    ):
        assert path in FACT_VOCABULARY


def test_enrichment_is_deterministic():
    first = normalize_snapshot(
        yoga_snapshot(), facts=FACTS
    )
    second = normalize_snapshot(
        yoga_snapshot(), facts=FACTS
    )
    assert first == second
    # enriching an already-enriched dict is stable (idempotent)
    assert normalize_snapshot(first, facts=FACTS) == first
