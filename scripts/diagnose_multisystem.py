#!/usr/bin/env python3
"""Multi-System Diagnostic Script (JRS-074).

Iterates through all Tier-1 validation fixtures and runs the multi-system
pipeline, printing a summary table showing per-system evidence record counts.
This proves whether the Western/Numerology engines are actually firing or
remaining silent on each fixture.

Usage::

    python scripts/diagnose_multisystem.py
    python scripts/diagnose_multisystem.py --domain marriage
    python scripts/diagnose_multisystem.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


def _count_evidence_records(
    chart: dict[str, Any],
    domain: str,
    outcome_taxonomy: str,
    system: str,
) -> int:
    """Run a single system pipeline and return evidence record count.

    Args:
        chart: The validation fixture dict.
        domain: The domain name (e.g., "marriage").
        outcome_taxonomy: The outcome taxonomy string.
        system: System name ("vedic", "western", or "numerology").

    Returns:
        The number of EvidenceRecord objects produced by the system.
    """
    if system == "vedic":
        from tests.calibration.pipeline import (
            _evaluate_domain_facts,
            _get_domain_service,
        )

        facts = chart.get("natal_facts", {})
        domain_svc = _get_domain_service(domain)
        if domain_svc is None:
            return 0
        records = _evaluate_domain_facts(domain_svc, facts)
        return len(records)

    if system == "western":
        import datetime as dt

        from jrs.western.service import WesternDomainService
        from western.models import WesternHouseSystem
        from western.service import WesternCalculationService

        birth_data = chart.get("birth_data", {})
        date_str = birth_data.get("date", "1980-01-01")
        time_str = birth_data.get("time", "12:00:00")
        latitude = float(birth_data.get("latitude", 19.076))
        longitude = float(birth_data.get("longitude", 72.8777))

        time_parts = time_str.split(":")
        parsed_time = dt.time(
            int(time_parts[0]),
            int(time_parts[1]),
            int(time_parts[2]) if len(time_parts) > 2 else 0,
        )

        western_calc = WesternCalculationService()
        western_chart = western_calc.calculate(
            birth_date=dt.date.fromisoformat(date_str),
            birth_time=parsed_time,
            latitude=latitude,
            longitude=longitude,
            house_system=WesternHouseSystem.PLACIDUS,
        )

        western_svc = WesternDomainService()
        records = western_svc.evaluate_chart_facts(western_chart)
        return len(records)

    if system == "numerology":
        from jrs.numerology.service import NumerologyDomainService
        from numerology.service import NumerologyCalculationService

        birth_data = chart.get("birth_data", {})
        date_str = birth_data.get("date", "1980-01-01")
        birth_name = chart.get("birth_name", "Default Test Name")

        num_calc = NumerologyCalculationService()
        num_chart = num_calc.calculate(
            birth_date=date_str,
            birth_name=birth_name,
        )

        num_svc = NumerologyDomainService()
        records = num_svc.evaluate_chart_facts(num_chart)
        return len(records)

    return 0


def diagnose(
    target_domain: str | None = None,
    verbose: bool = False,
) -> None:
    """Run the diagnostic across all validation fixtures.

    Args:
        target_domain: Optional domain to limit the diagnostic to.
        verbose: If True, print individual fixture details.
    """
    from tests.calibration.pipeline import (
        discover_fixtures,
        load_fixture,
    )

    fixture_map = discover_fixtures()

    if target_domain:
        fixture_map = {
            d: paths
            for d, paths in fixture_map.items()
            if d == target_domain
        }
        if not fixture_map:
            print(f"Error: Domain '{target_domain}' not found.")
            print("Available domains:", ", ".join(sorted(
                discover_fixtures().keys(),
            )))
            return

    # Header
    print("=" * 80)
    print("JRS-074 MULTI-SYSTEM DIAGNOSTIC")
    print("=" * 80)
    print()

    total_vedic = 0
    total_western = 0
    total_numerology = 0
    total_fixtures = 0
    total_outcomes = 0

    for domain, fixture_paths in sorted(fixture_map.items()):
        print(f"--- {domain.upper()} ---")
        print()

        if verbose:
            header = (
                f"{'Fixture':<45} "
                f"{'Outcome':<30} "
                f"{'Vedic':>5} {'West':>5} {'Num':>5}"
            )
            print(header)
            print("-" * len(header))

        domain_vedic = 0
        domain_western = 0
        domain_numerology = 0
        domain_fixtures = 0
        domain_outcomes = 0

        for fixture_path in fixture_paths:
            chart = load_fixture(fixture_path)
            expected = chart.get("expected_assessments", {})
            fixture_name = fixture_path.stem

            for outcome in expected:
                v_count = _count_evidence_records(
                    chart, domain, outcome, "vedic",
                )
                w_count = _count_evidence_records(
                    chart, domain, outcome, "western",
                )
                n_count = _count_evidence_records(
                    chart, domain, outcome, "numerology",
                )

                domain_vedic += v_count
                domain_western += w_count
                domain_numerology += n_count
                domain_outcomes += 1

                if verbose:
                    print(
                        f"{fixture_name:<45} "
                        f"{outcome:<30} "
                        f"{v_count:>5} {w_count:>5} {n_count:>5}"
                    )

        domain_fixtures = len(fixture_paths)
        total_vedic += domain_vedic
        total_western += domain_western
        total_numerology += domain_numerology
        total_fixtures += domain_fixtures
        total_outcomes += domain_outcomes

        print()
        print(
            f"  Summary: {domain_fixtures} fixtures, "
            f"{domain_outcomes} outcomes | "
            f"Vedic: {domain_vedic} records, "
            f"Western: {domain_western} records, "
            f"Numerology: {domain_numerology} records"
        )
        print()

    # Overall summary
    print("=" * 80)
    print("OVERALL DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"  Total Fixtures:    {total_fixtures}")
    print(f"  Total Outcomes:    {total_outcomes}")
    print(f"  Vedic Evidence:    {total_vedic} records")
    print(f"  Western Evidence:  {total_western} records")
    print(f"  Numerology Evidence: {total_numerology} records")
    print()

    # Status assessment
    if total_western == 0:
        print("  ⚠  Western engine: SILENT (0 evidence records)")
        print("     → Western rules may not be matching any chart facts.")
    else:
        print(f"  ✓  Western engine: ACTIVE ({total_western} records)")

    if total_numerology == 0:
        print("  ⚠  Numerology engine: SILENT (0 evidence records)")
        print("     → Numerology rules may not be matching any chart facts.")
    else:
        print(
            f"  ✓  Numerology engine: ACTIVE "
            f"({total_numerology} records)"
        )

    print()
    print("=" * 80)


def main() -> int:
    """Entry point for the diagnostic script."""
    parser = argparse.ArgumentParser(
        description="JRS-074 Multi-System Diagnostic",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Limit diagnostic to a specific domain (e.g., marriage)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-fixture, per-outcome detail rows",
    )
    args = parser.parse_args()

    diagnose(target_domain=args.domain, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
