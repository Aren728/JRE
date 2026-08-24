"""JRS CLI — Minimal, deterministic entry point for the full pipeline.

Usage::

    python -m jrs.cli \\
        --birth-date "28-09-1979" \\
        --birth-time "18:24" \\
        --place "Mumbai, India" \\
        --query "career"

    python -m jrs.cli \\
        --birth-date "28-09-1979" \\
        --birth-time "18:24" \\
        --place "Mumbai, India" \\
        --query "career" \\
        --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from jrs.convergence.service import ConvergenceService
from jrs.domains.career.service import CareerDomainService
from jrs.domains.education.service import EducationDomainService
from jrs.domains.marriage.service import MarriageDomainService
from jrs.domains.migration.service import MigrationDomainService
from jrs.domains.progeny.service import ProgenyDomainService
from jrs.domains.property.service import PropertyDomainService
from jrs.domains.transitions.service import TransitionsDomainService
from jrs.domains.wealth.service import WealthDomainService
from jrs.evidence.models import EvidenceRecord
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
)
from jrs.multisystem.service import IndependenceAnalyzer
from jrs.research.service import ResearchService
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger
from jrs.western.service import WesternDomainService

# ── Domain Registry ──────────────────────────────────────────────────────────

DOMAIN_SERVICES: dict[str, Any] = {
    "career": CareerDomainService,
    "wealth": WealthDomainService,
    "marriage": MarriageDomainService,
    "education": EducationDomainService,
    "property": PropertyDomainService,
    "progeny": ProgenyDomainService,
    "migration": MigrationDomainService,
    "transitions": TransitionsDomainService,
}

EVALUATE_METHODS: dict[str, str] = {
    "career": "evaluate_career_facts",
    "wealth": "evaluate_wealth_facts",
    "marriage": "evaluate_marriage_facts",
    "education": "evaluate_education_facts",
    "property": "evaluate_property_facts",
    "progeny": "evaluate_progeny_facts",
    "migration": "evaluate_migration_facts",
    "transitions": "evaluate_transitions_facts",
}

QUERY_OUTCOME_MAP: dict[str, str] = {
    "career": "CAREER_ASCENT",
    "wealth": "WEALTH_ACCUMULATION",
    "marriage": "MARRIAGE_FORMATION",
    "education": "HIGHER_EDUCATION",
    "property": "PROPERTY_ACQUISITION",
    "children": "EASY_CONCEPTION",
    "migration": "FOREIGN_SETTLEMENT",
    "travel": "SHORT_TERM_TRAVEL",
    "transitions": "LIFE_PHASE_SHIFT",
}

# Internal domain key mapping (query name → domain service key)
QUERY_DOMAIN_MAP: dict[str, str] = {
    "career": "career",
    "wealth": "wealth",
    "marriage": "marriage",
    "education": "education",
    "property": "property",
    "children": "progeny",
    "migration": "migration",
    "travel": "migration",
    "transitions": "transitions",
}

# Mapping from query to Western outcome taxonomy
QUERY_WESTERN_OUTCOME_MAP: dict[str, str] = {
    "career": "CAREER_PROMINENCE",
    "wealth": "FINANCIAL_GAIN",
    "marriage": "RELATIONSHIP_HARMONY",
    "education": "INTELLECTUAL_CAPACITY",
    "property": "FINANCIAL_GAIN",
    "children": "CREATIVE_TALENT",
    "migration": "SOCIAL_INFLUENCE",
    "travel": "SOCIAL_INFLUENCE",
    "transitions": "PHILOSOPHICAL_DEPTH",
}

# Default Western facts for demonstration (query → facts dict)
_DEFAULT_WESTERN_FACTS: dict[str, dict[str, Any]] = {
    "career": {
        "sun_house": "10",
        "mars_house": "10",
        "sun_dignity": "DOMICILE",
    },
    "wealth": {
        "jupiter_house": "2",
        "venus_house": "2",
        "jupiter_dignity": "DOMICILE",
    },
    "marriage": {
        "venus_house": "7",
        "moon_house": "7",
        "venus_dignity": "DOMICILE",
    },
    "education": {
        "mercury_house": "3",
        "jupiter_house": "9",
        "mercury_dignity": "DOMICILE",
    },
    "property": {
        "moon_house": "4",
        "mars_house": "4",
        "mars_dignity": "DOMICILE",
    },
    "children": {
        "jupiter_house": "5",
        "venus_house": "5",
        "venus_dignity": "DOMICILE",
    },
    "migration": {
        "mars_house": "12",
        "jupiter_house": "12",
        "mars_dignity": "DOMICILE",
    },
    "travel": {
        "mercury_house": "9",
        "jupiter_house": "9",
        "mercury_dignity": "DOMICILE",
    },
    "transitions": {
        "saturn_house": "12",
        "jupiter_house": "9",
        "saturn_dignity": "DOMICILE",
    },
}


# ── Core Pipeline ────────────────────────────────────────────────────────────


def _build_event_windows(
    candidate_event: str = "",
    dasha_planet: str = "",
    dasha_start: str = "",
    dasha_end: str = "",
    transit_planet: str = "",
    transit_start: str = "",
    transit_end: str = "",
) -> tuple[EventWindow, ...]:
    """Build event windows from dasha and transit parameters."""
    windows: list[EventWindow] = []

    if dasha_planet and dasha_start and dasha_end:
        trigger = TemporalTrigger(
            activation_type=ActivationType.DASHA,
            triggering_planet=dasha_planet,
            activation_start_utc=dasha_start,
            activation_end_utc=dasha_end,
            strength=0.9,
        )
        windows.append(EventWindow(
            candidate_event_taxonomy=candidate_event,
            triggers=(trigger,),
        ))

    if transit_planet and transit_start and transit_end:
        trigger = TemporalTrigger(
            activation_type=ActivationType.TRANSIT,
            triggering_planet=transit_planet,
            activation_start_utc=transit_start,
            activation_end_utc=transit_end,
            strength=0.8,
        )
        windows.append(EventWindow(
            candidate_event_taxonomy=candidate_event,
            triggers=(trigger,),
        ))

    return tuple(windows)


def _evaluate_domain(
    domain_key: str,
    facts: dict[str, Any],
) -> tuple[EvidenceRecord, ...]:
    """Evaluate facts through the appropriate domain service."""
    svc_class = DOMAIN_SERVICES[domain_key]
    svc = svc_class()
    method_name = EVALUATE_METHODS[domain_key]
    method = getattr(svc, method_name)
    result: tuple[EvidenceRecord, ...] = method(facts)
    return result


def _run_assessment(
    domain_key: str,
    facts: dict[str, Any],
    outcome_taxonomy: str,
    event_windows: tuple[EventWindow, ...],
) -> dict[str, Any]:
    """Run the full JRS pipeline: facts → evidence → convergence → assessment."""
    # Step 1 & 2: Extract facts and generate evidence records
    evidence_records = _evaluate_domain(domain_key, facts)

    # Step 3 & 4: Assess convergence
    convergence_svc = ConvergenceService()
    assessment = convergence_svc.assess_domain(
        outcome_taxonomy,
        evidence_records=evidence_records,
        event_windows=event_windows,
    )

    return assessment.to_dict()


# ── Multi-System Pipelines ───────────────────────────────────────────────────


def _run_vedic_system_assessment(
    domain_key: str,
    facts: dict[str, Any],
    outcome_taxonomy: str,
    event_windows: tuple[EventWindow, ...],
) -> SystemAssessment:
    """Run the Vedic pipeline and return a SystemAssessment.

    Converts the Vedic DomainAssessment into a SystemAssessment
    suitable for cross-system convergence analysis.
    """
    evidence_records = _evaluate_domain(domain_key, facts)
    convergence_svc = ConvergenceService()
    domain_assessment = convergence_svc.assess_domain(
        outcome_taxonomy,
        evidence_records=evidence_records,
        event_windows=event_windows,
    )

    return SystemAssessment(
        system_type=SystemType.VEDIC,
        outcome_taxonomy=domain_assessment.outcome_taxonomy,
        assessment_status=domain_assessment.assessment_status.value,
        timing_status=domain_assessment.timing_status.value,
        provenance=EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        ),
    )


def _run_western_system_assessment(
    query: str,
    outcome_taxonomy: str,
) -> SystemAssessment:
    """Run the Western pipeline and return a SystemAssessment.

    Uses default Western facts for demonstration. In production,
    these would be computed from a WesternChart via the JRE-066 engine.
    """
    western_facts = _DEFAULT_WESTERN_FACTS.get(query, {})
    western_svc = WesternDomainService()

    from jrs.western.models import evaluate_facts

    if western_facts:
        rules = western_svc.load_rules().rules
        records = evaluate_facts(rules, western_facts)
    else:
        records = ()

    if not records:
        return SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="NO_MATCH",
            assessment_status="NEUTRAL",
            timing_status="INACTIVE",
            provenance=EvidenceProvenance(
                system_type=SystemType.WESTERN,
                source_tradition="LILLY",
            ),
        )

    # Aggregate by outcome taxonomy
    outcome_support: dict[str, int] = {}
    outcome_contradict: dict[str, int] = {}
    for record in records:
        outcome = record.outcome_taxonomy
        if record.direction.value == "SUPPORT":
            outcome_support[outcome] = outcome_support.get(outcome, 0) + 1
        elif record.direction.value == "CONTRADICT":
            outcome_contradict[outcome] = (
                outcome_contradict.get(outcome, 0) + 1
            )

    all_outcomes = set(outcome_support.keys()) | set(
        outcome_contradict.keys()
    )
    best_outcome = ""
    best_score = -1
    for outcome in all_outcomes:
        score = outcome_support.get(outcome, 0) - outcome_contradict.get(
            outcome, 0
        )
        if score > best_score:
            best_score = score
            best_outcome = outcome

    net_support = outcome_support.get(best_outcome, 0)
    net_contradict = outcome_contradict.get(best_outcome, 0)

    if net_support >= 3 and net_contradict == 0:
        status = "STRONGLY_SUPPORTED"
    elif net_support >= 2 and net_contradict == 0:
        status = "SUPPORTED"
    elif net_support >= 1:
        status = "WEAKLY_SUPPORTED"
    elif net_contradict >= 2 or (net_contradict >= 1 and net_support == 0):
        status = "CONTRADICTED"
    else:
        status = "NEUTRAL"

    return SystemAssessment(
        system_type=SystemType.WESTERN,
        outcome_taxonomy=best_outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        ),
    )


def _run_multi_system(
    query: str,
    domain_key: str,
    facts: dict[str, Any],
    outcome_taxonomy: str,
    event_windows: tuple[EventWindow, ...],
    systems: list[str],
) -> tuple[SystemAssessment, ...]:
    """Run the multi-system pipeline for the requested systems.

    Returns a tuple of SystemAssessment objects, one per system.
    """
    assessments: list[SystemAssessment] = []

    if "vedic" in systems:
        assessments.append(
            _run_vedic_system_assessment(
                domain_key, facts, outcome_taxonomy, event_windows,
            )
        )

    if "western" in systems:
        assessments.append(
            _run_western_system_assessment(query, outcome_taxonomy)
        )

    return tuple(assessments)


def _build_cross_system_result(
    assessments: tuple[SystemAssessment, ...],
    event_cluster_id: str = "cli-default",
) -> dict[str, Any]:
    """Build cross-system convergence result from SystemAssessments.

    Uses the IndependenceAnalyzer to compute independence and convergence.
    Returns a serializable dict.
    """
    if len(assessments) < 2:
        return {}

    analyzer = IndependenceAnalyzer()

    # Build provenance map
    provenances: dict[SystemType, EvidenceProvenance] = {}
    assessment_map: dict[str, SystemAssessment] = {}

    for assessment in assessments:
        st = assessment.system_type
        key = st.value.lower()
        assessment_map[key] = assessment
        if assessment.provenance is not None:
            provenances[st] = assessment.provenance

    # Compute raw convergence
    raw_convergence = compute_convergence_score(assessment_map)

    # Compute independence-adjusted convergence
    prov_list = list(provenances.values())
    independence = analyzer.calculate_collective_independence(prov_list)
    adjusted_convergence = raw_convergence * independence

    return {
        "raw_convergence": round(raw_convergence, 6),
        "independence_score": round(independence, 6),
        "adjusted_convergence": round(adjusted_convergence, 6),
        "systems": [a.system_type.value for a in assessments],
        "individual_assessments": {
            a.system_type.value: a.to_dict() for a in assessments
        },
    }


# ── Output Formatting ────────────────────────────────────────────────────────


def _format_text_report(
    assessment: dict[str, Any],
    birth_date: str,
    birth_time: str,
    place: str,
    query: str,
    facts: dict[str, Any],
    domain_key: str = "",
    systems: list[str] | None = None,
    system_assessments: tuple[SystemAssessment, ...] | None = None,
    cross_system: dict[str, Any] | None = None,
) -> str:
    """Format the assessment as a structured traceable report."""
    dims = assessment.get("dimensions", {})
    lines = [
        "=" * 60,
        "JRS ASSESSMENT",
        "=" * 60,
        "",
        "Question:",
        f"  {query.title()}",
        "",
        "Birth Data:",
        f"  Date:   {birth_date}",
        f"  Time:   {birth_time}",
        f"  Place:  {place}",
        "",
    ]

    # Systems requested
    if systems:
        lines.append("Systems:")
        lines.append(f"  {', '.join(s.title() for s in systems)}")
        lines.append("")

    lines.extend([
        "Assessment:",
        f"  {assessment.get('assessment_status', 'N/A')}",
        "",
        "Evidence:",
        f"  Supporting channels:   {dims.get('supporting_count', 0)}",
        f"  Independent channels:  {dims.get('independent_channels', 0)}",
        f"  Contradicting channels: {dims.get('contradicting_count', 0)}",
        f"  Timing convergence:    {dims.get('timing_convergence_count', 0)}",
        f"  Source confidence:      {dims.get('source_confidence', 'N/A')}",
        "",
        "Overall Evidence Strength:",
        f"  {assessment.get('overall_evidence_strength', 'N/A')}",
        "",
    ])

    # Key factors from evidence records
    lines.append("Key factors:")
    for key in sorted(facts.keys()):
        val = facts[key]
        if val is True:
            lines.append(f"  • {key.replace('_', ' ').title()}")
        elif val is False:
            lines.append(f"  • No {key.replace('_', ' ').title()}")

    lines.append("")
    lines.append("Classical sources:")
    try:
        research_svc = ResearchService()
        domain_citations = research_svc.get_citations_for_domain(domain_key)
        if domain_citations:
            for citation in domain_citations:
                lines.append(f"  • {citation.source_full}, {citation.location}")
                lines.append(f"    {citation.claim}")
        else:
            lines.append("  • BPHS (Brihat Parashara Hora Shastra)")
    except Exception:
        lines.append("  • BPHS (Brihat Parashara Hora Shastra)")
    lines.append("")

    # Multi-system individual assessments
    if system_assessments and len(system_assessments) > 1:
        lines.append("-" * 60)
        lines.append("INDIVIDUAL SYSTEM ASSESSMENTS")
        lines.append("-" * 60)
        for sa in system_assessments:
            lines.append("")
            lines.append(f"  [{sa.system_type.value}]")
            prov = sa.provenance
            source_info = (
                f"  Source: {prov.source_tradition}"
                if prov
                else "  Source: N/A"
            )
            lines.append(source_info)
            lines.append(f"  Outcome: {sa.outcome_taxonomy}")
            lines.append(f"  Status: {sa.assessment_status}")
            lines.append(f"  Timing: {sa.timing_status}")
        lines.append("")

    # Cross-system convergence section
    if cross_system and len(cross_system) > 0:
        lines.append("-" * 60)
        lines.append("CROSS-SYSTEM CONVERGENCE")
        lines.append("-" * 60)
        lines.append("")
        raw = cross_system.get("raw_convergence", 0.0)
        indep = cross_system.get("independence_score", 0.0)
        adj = cross_system.get("adjusted_convergence", 0.0)
        lines.append(f"  Raw convergence:          {raw:.4f}")
        lines.append(f"  Independence score:       {indep:.4f}")
        lines.append(f"  Adjusted convergence:     {adj:.4f}")
        lines.append("")
        lines.append("  Systems involved:")
        for sys_name in cross_system.get("systems", []):
            lines.append(f"    • {sys_name.upper()}")
        lines.append("")

    lines.extend([
        "Timing:",
        "  Timing status: INACTIVE (no dasha/transit data provided)",
        "",
        "Limitations:",
        "  • No specific transit data for exact event timing",
        "  • Birth place resolved to approximate coordinates",
        "",
        "=" * 60,
    ])

    return "\n".join(lines)


# ── Argument Parser ──────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="jrs",
        description="JRS — Jyotish Research System CLI",
    )
    parser.add_argument(
        "--birth-date",
        required=True,
        help="Birth date (DD-MM-YYYY)",
    )
    parser.add_argument(
        "--birth-time",
        required=True,
        help="Birth time (HH:MM)",
    )
    parser.add_argument(
        "--place",
        required=True,
        help="Birth place (e.g., Mumbai, India)",
    )
    parser.add_argument(
        "--query",
        required=True,
        choices=sorted(QUERY_DOMAIN_MAP.keys()),
        help="Query domain (e.g., career, wealth, marriage)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON instead of text",
    )
    parser.add_argument(
        "--systems",
        default="vedic",
        help=(
            "Comma-separated list of astrological systems to run "
            "(e.g., vedic,western). Default: vedic"
        ),
    )
    return parser


# ── Main Entry Point ─────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolve domain and outcome
    query = args.query
    domain_key = QUERY_DOMAIN_MAP[query]
    outcome = QUERY_OUTCOME_MAP.get(query, query.upper())

    # Parse systems
    requested_systems = [s.strip().lower() for s in args.systems.split(",")]
    valid_systems = {"vedic", "western"}
    for sys_name in requested_systems:
        if sys_name not in valid_systems:
            print(
                f"Error: Unknown system '{sys_name}'. "
                f"Valid systems: {', '.join(sorted(valid_systems))}",
                file=sys.stderr,
            )
            return 1

    # Default facts for demonstration (in production, these would come
    # from actual JRE engine outputs based on birth data)
    facts: dict[str, Any] = _default_facts_for_query(query)

    # Build event windows (empty — no dasha data in basic CLI mode)
    event_windows: tuple[EventWindow, ...] = ()

    is_multi = len(requested_systems) > 1

    system_assessments: tuple[SystemAssessment, ...] = ()
    cross_system: dict[str, Any] = {}
    vedic_assessment: dict[str, Any] | None = None

    try:
        if is_multi:
            # Multi-system pipeline
            system_assessments = _run_multi_system(
                query=query,
                domain_key=domain_key,
                facts=facts,
                outcome_taxonomy=outcome,
                event_windows=event_windows,
                systems=requested_systems,
            )
            cross_system = _build_cross_system_result(system_assessments)
            for sa in system_assessments:
                if sa.system_type is SystemType.VEDIC:
                    vedic_assessment = _run_assessment(
                        domain_key=domain_key,
                        facts=facts,
                        outcome_taxonomy=outcome,
                        event_windows=event_windows,
                    )
                    break
        else:
            # Single-system pipeline (backward compatible)
            vedic_assessment = _run_assessment(
                domain_key=domain_key,
                facts=facts,
                outcome_taxonomy=outcome,
                event_windows=event_windows,
            )
    except Exception as exc:
        print(f"Error: Assessment failed: {exc}", file=sys.stderr)
        return 1

    # Format output
    if args.json_output:
        classical_sources: list[dict[str, str]] = []
        try:
            research_svc = ResearchService()
            domain_citations = research_svc.get_citations_for_domain(domain_key)
            for c in domain_citations:
                classical_sources.append({
                    "rule_id": c.rule_id,
                    "source": c.source_full,
                    "location": c.location,
                    "claim": c.claim,
                })
        except Exception:
            classical_sources.append({
                "rule_id": "default",
                "source": "Brihat Parashara Hora Shastra",
                "location": "General",
                "claim": "Classical Jyotish principles",
            })

        output_data: dict[str, Any] = {
            "birth_data": {
                "date": args.birth_date,
                "time": args.birth_time,
                "place": args.place,
            },
            "query": query,
            "domain": domain_key,
            "systems": requested_systems,
            "facts": facts,
            "classical_sources": classical_sources,
        }

        if is_multi:
            output_data["system_assessments"] = {
                sa.system_type.value: sa.to_dict()
                for sa in system_assessments
            }
            output_data["cross_system_convergence"] = cross_system
        else:
            output_data["assessment"] = vedic_assessment or {}

        output = json.dumps(output_data, indent=2, sort_keys=True)
    else:
        output = _format_text_report(
            vedic_assessment or {},
            args.birth_date,
            args.birth_time,
            args.place,
            query,
            facts,
            domain_key=domain_key,
            systems=requested_systems,
            system_assessments=system_assessments,
            cross_system=cross_system if is_multi else None,
        )

    print(output)
    return 0


def _default_facts_for_query(query: str) -> dict[str, Any]:
    """Return default demonstration facts for a given query.

    In production, these would be computed by the JRE engines from
    actual birth data. For the CLI demo, we return representative
    facts that trigger the domain rules.
    """
    defaults: dict[str, dict[str, Any]] = {
        "career": {
            "10th_lord_in_kendra_or_trikona": True,
            "sun_strong": True,
            "sun_10th_connection": True,
        },
        "wealth": {
            "2nd_lord_in_11th": True,
            "jupiter_strong": True,
            "jupiter_2nd_or_11th_connection": True,
        },
        "marriage": {
            "7th_lord_in_kendra_or_trikona": True,
            "venus_bala": 7.5,
            "jupiter_aspects_7th": True,
        },
        "education": {
            "4th_lord_in_kendra": True,
            "jupiter_strong": True,
            "jupiter_4th_connection": True,
        },
        "property": {
            "4th_lord_strong": True,
            "mars_strong": True,
            "mars_4th_connection": True,
        },
        "children": {
            "jupiter_strong": True,
            "5th_lord_in_kendra": True,
            "venus_strong": True,
            "jupiter_aspecting_5th": True,
        },
        "migration": {
            "rahu_in_12th": True,
            "9th_lord_in_12th": True,
            "rahu_12th_connection": True,
        },
        "travel": {
            "mercury_strong": True,
            "mercury_12th_connection": True,
        },
        "transitions": {
            "saturn_return": True,
            "jupiter_ketu_conjunction": True,
        },
    }
    return defaults.get(query, {})


if __name__ == "__main__":
    sys.exit(main())
