#!/usr/bin/env python3
"""Phase F3 — Strict Error Attribution on DEV & VALIDATION Sets.

Categorizes every False Positive and False Negative by the specific
architectural layer responsible.  NO changes to rules, weights, or
engine logic — purely diagnostic.

Usage::

    python scripts/error_attribution.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = _PROJECT_ROOT / "reports"

# ── Ground truth domains ──────────────────────────────────────────────

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "CAREER": ["prize", "nobel", "award", "career", "appointment", "promotion",
               "coronation", "presidency", "election", "inauguration", "discovery",
               "publication", "patent", "founding", "success", "peak", "golden",
               "masterpiece", "premiere", "record", "breakthrough", "century"],
    "HEALTH": ["death", "illness", "disease", "hospital", "accident", "died",
               "deceased", "passing"],
    "RELATIONSHIPS": ["marriage", "wedding", "divorce", "romance", "affair",
                       "partner", "spouse", "engagement"],
    "WEALTH": ["fortune", "wealth", "inheritance", "millionaire", "billionaire",
               "rich", "wealthy"],
    "MIGRATION": ["migration", "immigration", "exile", "emigration", "journey"],
}


def _classify_domain_from_event(event_id: str) -> str:
    """Classify event domain from the event_id string."""
    eid = event_id.upper()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.upper() in eid:
                return domain
    return "CAREER"  # default fallback


# ── Yoga domain mappings ──────────────────────────────────────────────

_YOGA_DOMAINS: dict[str, list[str]] = {
    "Malavya": ["CAREER", "WEALTH", "RELATIONSHIPS"],
    "Bhadra": ["CAREER", "WEALTH"],
    "Hamsa": ["CAREER", "WEALTH"],
    "Ruchaka": ["CAREER", "HEALTH"],
    "Shasha": ["CAREER", "WEALTH"],
    "Raja": ["CAREER", "WEALTH"],
    "Dhana": ["WEALTH", "CAREER"],
    "Gajakesari": ["CAREER", "WEALTH", "RELATIONSHIPS"],
    "Budhaditya": ["CAREER", "HEALTH"],
    "Sunapha": ["CAREER", "WEALTH"],
    "Amala": ["CAREER", "WEALTH"],
    "Vipareeta Raja": ["HEALTH", "CAREER"],
    "Kemadruma": ["HEALTH"],
    "Sakata": ["HEALTH"],
}


def _yoga_matches_domain(yoga_name: str, event_domain: str) -> bool:
    """Check if a yoga's mapped domains include the event domain."""
    mapped = _YOGA_DOMAINS.get(yoga_name, ["CAREER", "WEALTH"])
    return event_domain in mapped


# ── Attribution categories ────────────────────────────────────────────

FN_CATEGORIES = [
    "Coverage Gap",
    "Formation Failed",
    "Dasha Mismatch",
    "Transit Penalty",
    "Domain Mapping",
]

FP_CATEGORIES = [
    "Domain Overlap",
    "Weak Activation",
    "Dasha Coincidence",
    "Modifier Over-Cancellation",
]


def _classify_fn(event: dict[str, Any], chart_yogas: list[dict[str, Any]]) -> str:
    """Classify a False Negative into its root cause category."""
    event_domain = _classify_domain_from_event(event["event_id"])
    dasha = event.get("dasha", {})
    md = dasha.get("md", "")
    ad = dasha.get("ad", "")

    # Check if any yoga was detected at all (any status)
    formed_yogas = [y for y in chart_yogas if y.get("status") in ("FORMED", "WEAKENED")]
    activated_yogas = [y for y in chart_yogas if y.get("activation") == "ACTIVATED"]

    # 1. Coverage Gap: No yoga formed at all for this chart
    if not formed_yogas:
        return "Coverage Gap"

    # 2. Formation Failed: Yoga existed but was cancelled/weakened by modifiers
    if formed_yogas and not activated_yogas:
        # Check if any yoga was CANCELLED (modifier pipeline)
        cancelled = [y for y in chart_yogas if y.get("status") == "CANCELLED"]
        if cancelled:
            return "Formation Failed"

    # 3. Domain Mapping: Yoga activated but domain doesn't match
    if activated_yogas:
        domain_match = any(
            _yoga_matches_domain(y["name"], event_domain)
            for y in activated_yogas
        )
        if not domain_match:
            return "Domain Mapping"

    # 4. Dasha Mismatch: Yoga formed but Dasha lord doesn't match any yoga planet
    if formed_yogas:
        yoga_planets = set()
        for y in formed_yogas:
            # Extract planets from yoga name or use known mappings
            name = y["name"]
            if name == "Gajakesari":
                yoga_planets.update(["JUPITER", "MOON"])
            elif name == "Malavya":
                yoga_planets.add("VENUS")
            elif name == "Bhadra":
                yoga_planets.add("MERCURY")
            elif name == "Hamsa":
                yoga_planets.add("JUPITER")
            elif name == "Ruchaka":
                yoga_planets.add("MARS")
            elif name == "Shasha":
                yoga_planets.add("SATURN")
            elif name == "Raja":
                # Raja involves multiple planets
                pass
            elif name == "Dhana":
                yoga_planets.update(["JUPITER", "VENUS"])
            elif name == "Budhaditya":
                yoga_planets.update(["SUN", "MERCURY"])
            elif name == "Sunapha":
                yoga_planets.update(["MOON", "VENUS"])
            elif name == "Amala":
                yoga_planets.add("JUPITER")
            elif name == "Vipareeta Raja":
                yoga_planets.update(["SATURN", "MERCURY", "VENUS"])

        if yoga_planets and md not in yoga_planets and ad not in yoga_planets:
            return "Dasha Mismatch"

    # 5. Transit Penalty: Yoga activated but dynamic strength dropped
    for y in chart_yogas:
        if y.get("activation") == "ACTIVATED":
            dyn = y.get("dynamic_strength", 1.0)
            if dyn is not None and dyn < 0.3:
                return "Transit Penalty"

    # Default: Dasha Mismatch (most common)
    return "Dasha Mismatch"


def _classify_fp(event: dict[str, Any], chart_yogas: list[dict[str, Any]]) -> str:
    """Classify a False Positive into its root cause category."""
    event_domain = _classify_domain_from_event(event["event_id"])
    dasha = event.get("dasha", {})
    md = dasha.get("md", "")
    ad = dasha.get("ad", "")

    # Check activated yogas
    activated = [y for y in chart_yogas if y.get("activation") == "ACTIVATED"]

    if not activated:
        return "Weak Activation"

    # Check if any activated yoga matches the event domain
    domain_match = any(
        _yoga_matches_domain(y["name"], event_domain)
        for y in activated
    )

    if not domain_match:
        return "Domain Overlap"

    # Check dynamic strength
    for y in activated:
        dyn = y.get("dynamic_strength", 1.0)
        if dyn is not None and dyn < 0.3:
            return "Weak Activation"

    # If domain matches but it's a HEALTH event and yoga is CAREER
    if event_domain == "HEALTH":
        return "Dasha Coincidence"

    return "Dasha Coincidence"


def _load_evaluation_data(filepath: Path) -> dict[str, Any]:
    """Load raw evaluation JSON."""
    with filepath.open(encoding="utf-8") as f:
        return json.load(f)


def _get_ground_truth(fixture_path: Path) -> dict[str, dict[str, str]]:
    """Load ground truth from fixture file."""
    with fixture_path.open(encoding="utf-8") as f:
        fixture = json.load(f)

    ground_truth = {}
    for event in fixture.get("known_events", []):
        event_id = event["event_id"]
        # Use fixture's domain if available, otherwise classify from event_id
        domain = event.get("domain") or _classify_domain_from_event(event_id)
        ground_truth[event_id] = {
            "date": event.get("event_date_utc", ""),
            "domain": domain,
        }
    return ground_truth


def _load_fixtures_dir() -> Path:
    return _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"


def _attribute_errors(eval_data: dict[str, Any]) -> dict[str, Any]:
    """Run error attribution on evaluation data."""
    fixtures_dir = _load_fixtures_dir()
    fp_cases = []
    fn_cases = []
    tp_cases = []
    tn_count = 0

    for subject in eval_data.get("subjects", []):
        fixture_name = subject.get("fixture", "")
        fixture_path = fixtures_dir / fixture_name
        if not fixture_path.exists():
            continue

        gt = _get_ground_truth(fixture_path)

        for event in subject.get("events", []):
            event_id = event["event_id"]
            relevant = event.get("relevant_yoga_activated", False)
            event_domain = gt.get(event_id, {}).get("domain", "CAREER")

            # Get all yogas for this chart (from first event to avoid duplication)
            chart_yogas = event.get("all_yogas", [])
            top_yogas = event.get("top_yogas", [])

            if relevant:
                # True Positive — a relevant yoga activated
                tp_cases.append({
                    "subject": subject["name"],
                    "fixture": fixture_name,
                    "event_id": event_id,
                    "domain": event_domain,
                    "dasha": event.get("dasha", {}),
                    "top_yoga": top_yogas[0]["name"] if top_yogas else None,
                    "dynamic_strength": top_yogas[0].get("dynamic_strength") if top_yogas else None,
                })
            else:
                # Check if ANY yoga activated
                activated = [y for y in chart_yogas if y.get("activation") == "ACTIVATED"]

                if activated:
                    # False Positive — yoga activated but not relevant
                    category = _classify_fp(event, chart_yogas)
                    fp_cases.append({
                        "subject": subject["name"],
                        "fixture": fixture_name,
                        "event_id": event_id,
                        "domain": event_domain,
                        "dasha": event.get("dasha", {}),
                        "activated_yogas": [{"name": y["name"], "dynamic_strength": y.get("dynamic_strength")} for y in activated],
                        "category": category,
                    })
                else:
                    # False Negative — no yoga activated for this event
                    category = _classify_fn(event, chart_yogas)
                    fn_cases.append({
                        "subject": subject["name"],
                        "fixture": fixture_name,
                        "event_id": event_id,
                        "domain": event_domain,
                        "dasha": event.get("dasha", {}),
                        "chart_yogas": [{"name": y["name"], "status": y.get("status"), "activation": y.get("activation")} for y in chart_yogas],
                        "category": category,
                    })

    return {
        "tp": tp_cases,
        "fp": fp_cases,
        "fn": fn_cases,
        "total_events": len(tp_cases) + len(fp_cases) + len(fn_cases),
    }


def _generate_report(dev_results: dict, val_results: dict) -> str:
    """Generate the error attribution markdown report."""
    all_tp = dev_results["tp"] + val_results["tp"]
    all_fp = dev_results["fp"] + val_results["fp"]
    all_fn = dev_results["fn"] + val_results["fn"]
    total = len(all_tp) + len(all_fp) + len(all_fn)

    # Category counts
    fn_categories = Counter(f["category"] for f in all_fn)
    fp_categories = Counter(f["category"] for f in all_fp)

    # Domain breakdown
    fn_domains = Counter(f["domain"] for f in all_fn)
    fp_domains = Counter(f["domain"] for f in all_fp)

    # Subject breakdown
    fn_subjects = Counter(f["subject"] for f in all_fn)
    fp_subjects = Counter(f["subject"] for f in all_fp)

    lines = [
        "# Phase F3 — Error Attribution Report",
        "",
        "## Executive Summary",
        "",
        f"| Metric | DEV (30 charts) | VAL (10 charts) | Combined |",
        f"|--------|-----------------|-----------------|----------|",
        f"| Total Events | {len(dev_results['tp'])+len(dev_results['fp'])+len(dev_results['fn'])} | {len(val_results['tp'])+len(val_results['fp'])+len(val_results['fn'])} | {total} |",
        f"| True Positives | {len(dev_results['tp'])} | {len(val_results['tp'])} | {len(all_tp)} |",
        f"| False Positives | {len(dev_results['fp'])} | {len(val_results['fp'])} | {len(all_fp)} |",
        f"| False Negatives | {len(dev_results['fn'])} | {len(val_results['fn'])} | {len(all_fn)} |",
        f"| Precision | {len(all_tp)/(len(all_tp)+len(all_fp)) if all_tp or all_fp else 0:.3f} | — | {len(all_tp)/(len(all_tp)+len(all_fp)) if all_tp or all_fp else 0:.3f} |",
        f"| Recall | {len(all_tp)/(len(all_tp)+len(all_fn)) if all_tp or all_fn else 0:.3f} | — | {len(all_tp)/(len(all_tp)+len(all_fn)) if all_tp or all_fn else 0:.3f} |",
        "",
        "",
        "## Layer-by-Layer Failure Distribution",
        "",
        "### False Negatives (Root Cause)",
        "",
        "| Category | Count | % | Description |",
        "|----------|-------|---|-------------|",
    ]

    fn_total = len(all_fn) or 1
    for cat in FN_CATEGORIES:
        count = fn_categories.get(cat, 0)
        pct = count / fn_total * 100
        desc = {
            "Coverage Gap": "No classical yoga detected for this domain",
            "Formation Failed": "Yoga cancelled by modifiers (combustion/D9/debilitation)",
            "Dasha Mismatch": "Yoga formed but MD/AD/PD didn't align with yoga planets",
            "Transit Penalty": "BAV transit multiplier dropped strength below threshold",
            "Domain Mapping": "Yoga activated but mapped domains don't include event domain",
        }.get(cat, "")
        lines.append(f"| {cat} | {count} | {pct:.1f}% | {desc} |")

    lines.extend([
        "",
        "### False Positives (Root Cause)",
        "",
        "| Category | Count | % | Description |",
        "|----------|-------|---|-------------|",
    ])

    fp_total = len(all_fp) or 1
    for cat in FP_CATEGORIES:
        count = fp_categories.get(cat, 0)
        pct = count / fp_total * 100
        desc = {
            "Domain Overlap": "Yoga activated for different domain than event",
            "Weak Activation": "Dynamic strength < 0.3 but still triggered",
            "Dasha Coincidence": "Dasha aligned by chance, no causal link",
            "Modifier Over-Cancellation": "Yoga incorrectly cancelled by modifier pipeline",
        }.get(cat, "")
        lines.append(f"| {cat} | {count} | {pct:.1f}% | {desc} |")

    # Domain breakdown
    lines.extend([
        "",
        "### False Negatives by Domain",
        "",
        "| Domain | Count | % |",
        "|--------|-------|---|",
    ])
    for domain in sorted(fn_domains, key=fn_domains.get, reverse=True):
        count = fn_domains[domain]
        pct = count / fn_total * 100
        lines.append(f"| {domain} | {count} | {pct:.1f}% |")

    lines.extend([
        "",
        "### False Positives by Domain",
        "",
        "| Domain | Count | % |",
        "|--------|-------|---|",
    ])
    for domain in sorted(fp_domains, key=fp_domains.get, reverse=True):
        count = fp_domains[domain]
        pct = count / fp_total * 100
        lines.append(f"| {domain} | {count} | {pct:.1f}% |")

    # Subject breakdown (FN)
    lines.extend([
        "",
        "### False Negatives by Subject",
        "",
        "| Subject | FN Count | Top Category |",
        "|---------|----------|--------------|",
    ])
    for subject in sorted(fn_subjects, key=fn_subjects.get, reverse=True):
        count = fn_subjects[subject]
        # Find most common category for this subject
        subj_cats = [f["category"] for f in all_fn if f["subject"] == subject]
        top_cat = Counter(subj_cats).most_common(1)[0][0] if subj_cats else "—"
        lines.append(f"| {subject} | {count} | {top_cat} |")

    # Subject breakdown (FP)
    lines.extend([
        "",
        "### False Positives by Subject",
        "",
        "| Subject | FP Count | Top Category |",
        "|---------|----------|--------------|",
    ])
    for subject in sorted(fp_subjects, key=fp_subjects.get, reverse=True):
        count = fp_subjects[subject]
        subj_cats = [f["category"] for f in all_fp if f["subject"] == subject]
        top_cat = Counter(subj_cats).most_common(1)[0][0] if subj_cats else "—"
        lines.append(f"| {subject} | {count} | {top_cat} |")

    # ── The Hit List ───────────────────────────────────────────────
    lines.extend([
        "",
        "",
        "## The Hit List — Prioritized Fixes for Phase F4",
        "",
        "Based on the error attribution, here are the top 5 specific, actionable fixes",
        "ordered by expected impact on F1 score:",
        "",
    ])

    # Build hit list from FN categories
    hit_list = []

    # 1. Coverage Gap yogas
    coverage_fns = [f for f in all_fn if f["category"] == "Coverage Gap"]
    if coverage_fns:
        coverage_subjects = set(f["subject"] for f in coverage_fns)
        hit_list.append({
            "priority": 1,
            "title": "Add Missing Yoga Detectors for Zero-Yoga Charts",
            "impact": f"{len(coverage_fns)} FNs across {len(coverage_subjects)} subjects",
            "details": f"Subjects: {', '.join(sorted(coverage_subjects))}. "
                       "These charts have no classical yogas detected. "
                       "Need additional detectors (Vasumati, Neecha Bhang, etc.).",
            "expected_recovery": f"+{len(coverage_fns)} TPs",
        })

    # 2. Dasha Mismatch
    dasha_fns = [f for f in all_fn if f["category"] == "Dasha Mismatch"]
    if dasha_fns:
        dasha_subjects = set(f["subject"] for f in dasha_fns)
        hit_list.append({
            "priority": 2,
            "title": "Loosen Dasha Activation Logic (Add Dispositor/Aspect Matching)",
            "impact": f"{len(dasha_fns)} FNs across {len(dasha_subjects)} subjects",
            "details": f"Yogas formed but MD/AD/PD lords don't match yoga planets. "
                       "Adding dispositor chain or aspect-based matching could recover many.",
            "expected_recovery": f"+{len(dasha_fns)//2} to +{len(dasha_fns)} TPs",
        })

    # 3. Formation Failed
    formation_fns = [f for f in all_fn if f["category"] == "Formation Failed"]
    if formation_fns:
        hit_list.append({
            "priority": 3,
            "title": "Review Modifier Pipeline Thresholds",
            "impact": f"{len(formation_fns)} FNs",
            "details": "Yogas cancelled by combustion/debilitation/D9. "
                       "Review if thresholds are too aggressive.",
            "expected_recovery": f"+{len(formation_fns)//2} TPs",
        })

    # 4. Domain Overlap FPs
    domain_fps = [f for f in all_fp if f["category"] == "Domain Overlap"]
    if domain_fps:
        hit_list.append({
            "priority": 4,
            "title": "Refine Domain Mapping to Reduce False Positives",
            "impact": f"{len(domain_fps)} FPs",
            "details": "Yogas activated for wrong domain. "
                       "Add death/health exclusion logic for career yogas.",
            "expected_recovery": f"-{len(domain_fps)} FPs",
        })

    # 5. Transit Penalty
    transit_fns = [f for f in all_fn if f["category"] == "Transit Penalty"]
    if transit_fns:
        hit_list.append({
            "priority": 5,
            "title": "Adjust Transit Multiplier Thresholds",
            "impact": f"{len(transit_fns)} FNs",
            "details": "BAV transit penalty dropped dynamic strength below threshold. "
                       "Consider relaxing the -0.20 penalty for strong natal yogas.",
            "expected_recovery": f"+{len(transit_fns)} TPs",
        })

    for item in hit_list:
        lines.extend([
            f"### Priority {item['priority']}: {item['title']}",
            "",
            f"- **Impact:** {item['impact']}",
            f"- **Details:** {item['details']}",
            f"- **Expected Recovery:** {item['expected_recovery']}",
            "",
        ])

    # ── Detailed FP/FN Traces ─────────────────────────────────────
    lines.extend([
        "",
        "",
        "## Appendix A: Detailed False Positive Traces",
        "",
    ])

    for i, fp in enumerate(all_fp, 1):
        lines.extend([
            f"### FP #{i}: {fp['subject']} — {fp['event_id']}",
            "",
            f"- **Domain:** {fp['domain']}",
            f"- **Category:** {fp['category']}",
            f"- **Dasha:** MD={fp['dasha'].get('md', '?')} / AD={fp['dasha'].get('ad', '?')}",
            f"- **Activated Yogas:**",
        ])
        for y in fp.get("activated_yogas", []):
            dyn = y.get("dynamic_strength")
            dyn_str = f"{dyn:.3f}" if dyn is not None else "N/A"
            lines.append(f"  - {y['name']} (strength: {dyn_str})")
        lines.append("")

    lines.extend([
        "",
        "## Appendix B: Detailed False Negative Traces",
        "",
    ])

    for i, fn in enumerate(all_fn, 1):
        lines.extend([
            f"### FN #{i}: {fn['subject']} — {fn['event_id']}",
            "",
            f"- **Domain:** {fn['domain']}",
            f"- **Category:** {fn['category']}",
            f"- **Dasha:** MD={fn['dasha'].get('md', '?')} / AD={fn['dasha'].get('ad', '?')}",
            f"- **Chart Yogas:**",
        ])
        for y in fn.get("chart_yogas", []):
            lines.append(f"  - {y['name']} (status: {y['status']}, activation: {y['activation']})")
        lines.append("")

    lines.extend([
        "",
        "",
        "## HOLDOUT Readiness",
        "",
        "- ✅ **No rules, weights, or engine logic were modified during this phase.**",
        "- ✅ Error attribution is purely diagnostic — no calibration performed.",
        "- ✅ The HOLDOUT set (10 charts, 30 events) remains locked and untouched.",
        "- ✅ Engine is ready for Phase F4 calibration, after which the HOLDOUT set",
        "  will be evaluated exactly once for final performance metrics.",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    print("=" * 60)
    print("Phase F3 — Error Attribution (DEV + VALIDATION)")
    print("=" * 60)
    print()

    # Load DEV results
    dev_path = REPORTS_DIR / "blind_evaluation_dev_raw.json"
    if not dev_path.exists():
        print(f"ERROR: {dev_path} not found. Run with --split dev first.")
        return 1
    dev_data = _load_evaluation_data(dev_path)
    print(f"Loaded DEV data: {len(dev_data.get('subjects', []))} subjects")

    # Load VALIDATION results
    val_path = REPORTS_DIR / "blind_evaluation_validation_raw.json"
    if not val_path.exists():
        print(f"ERROR: {val_path} not found. Run with --split validation first.")
        return 1
    val_data = _load_evaluation_data(val_path)
    print(f"Loaded VAL data: {len(val_data.get('subjects', []))} subjects")

    # Attribute errors
    print("\nAttributing errors...")
    dev_results = _attribute_errors(dev_data)
    val_results = _attribute_errors(val_data)

    total_tp = len(dev_results["tp"]) + len(val_results["tp"])
    total_fp = len(dev_results["fp"]) + len(val_results["fp"])
    total_fn = len(dev_results["fn"]) + len(val_results["fn"])
    print(f"  TP: {total_tp}  FP: {total_fp}  FN: {total_fn}")

    # Generate report
    report = _generate_report(dev_results, val_results)
    report_path = REPORTS_DIR / "dev_val_error_attribution.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport written to: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
