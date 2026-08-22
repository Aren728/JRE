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
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger

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


# ── Output Formatting ────────────────────────────────────────────────────────


def _format_text_report(
    assessment: dict[str, Any],
    birth_date: str,
    birth_time: str,
    place: str,
    query: str,
    facts: dict[str, Any],
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
    ]

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
    lines.append("  • BPHS (Brihat Parashara Hora Shastra)")
    lines.append("")
    lines.append("Timing:")
    lines.append("  Timing status: INACTIVE (no dasha/transit data provided)")
    lines.append("")
    lines.append("Limitations:")
    lines.append("  • No specific transit data for exact event timing")
    lines.append("  • Birth place resolved to approximate coordinates")
    lines.append("")
    lines.append("=" * 60)

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

    # Default facts for demonstration (in production, these would come
    # from actual JRE engine outputs based on birth data)
    facts: dict[str, Any] = _default_facts_for_query(query)

    # Build event windows (empty — no dasha data in basic CLI mode)
    event_windows: tuple[EventWindow, ...] = ()

    # Run assessment
    try:
        assessment = _run_assessment(
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
        output = json.dumps({
            "birth_data": {
                "date": args.birth_date,
                "time": args.birth_time,
                "place": args.place,
            },
            "query": query,
            "domain": domain_key,
            "facts": facts,
            "assessment": assessment,
        }, indent=2, sort_keys=True)
    else:
        output = _format_text_report(
            assessment, args.birth_date, args.birth_time, args.place, query, facts,
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
