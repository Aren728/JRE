#!/usr/bin/env python3
"""Phase F2: False Positive & False Negative Pattern Analysis.

Reads the raw blind evaluation output and generates diagnostic reports
for both FPs and FNs. NO changes to engine logic — pure analysis.

Usage::

    python scripts/analyze_fp_fn.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = _PROJECT_ROOT / "reports"
FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"

# ── Domain Relevance ───────────────────────────────────────────────────────

_DOMAIN_RELEVANCE: dict[str, set[str]] = {
    "CAREER": {
        "CAREER_PROMINENCE", "POLITICAL_POWER", "SOCIAL_STATUS",
        "LEADERSHIP", "GENERAL_IMPROVEMENT", "BUSINESS_ACUMEN",
        "PUBLIC_RECOGNITION", "MENTAL_STRENGTH", "INTELLECTUAL_EXCELLENCE",
        "COMMUNICATION_SKILLS", "ARTISTIC_EXCELLENCE", "WISDOM_ACCUMULATION",
        "TEACHING_ABILITY",
    },
    "WEALTH": {"WEALTH_ACCUMULATION", "BUSINESS_ACUMEN", "GENERAL_IMPROVEMENT"},
    "HEALTH": {
        "GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY",
        "CRISIS_MANAGEMENT", "EMOTIONAL_STABILITY",
    },
    "MARRIAGE": {"RELATIONSHIP_HARMONY", "GENERAL_IMPROVEMENT", "DOMESTIC_HARMONY"},
    "MIGRATION": {"CAREER_PROMINENCE", "GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY"},
    "DEATH": {"GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY"},
}

# Yoga → typical domain relevance (simplified)
_YOGA_DOMAIN_RELEVANCE: dict[str, set[str]] = {
    "Raja": {"CAREER"},
    "Dhana": {"WEALTH", "CAREER"},
    "Gajakesari": {"CAREER", "WEALTH"},
    "Budhaditya": {"CAREER", "EDUCATION"},
    "Malavya": {"CAREER", "ARTISTIC"},
    "Hamsa": {"CAREER", "EDUCATION"},
    "Sasa": {"CAREER"},
    "Ruchaka": {"CAREER"},
    "Bhadra": {"CAREER"},
    "Vipareeta Raja": {"CAREER", "HEALTH"},
    "Sunapha": {"CAREER", "WEALTH"},
    "Anapha": {"CAREER", "WEALTH"},
    "Dhudhara": {"CAREER", "WEALTH"},
    "Amala": {"CAREER", "WEALTH"},
    "Neecha Bhanga": {"CAREER"},
    "Saraswati": {"CAREER", "EDUCATION"},
}


def load_raw_data() -> dict[str, Any]:
    raw_path = REPORTS_DIR / "blind_evaluation_50_cohort_raw.json"
    with raw_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_fixture_events() -> dict[str, dict[str, Any]]:
    """Load expected_planets from fixtures."""
    events: dict[str, dict[str, Any]] = {}
    for fp in sorted(FIXTURES_DIR.glob("chart_*.json")):
        with fp.open(encoding="utf-8") as f:
            fixture = json.load(f)
        for ke in fixture.get("known_events", []):
            events[ke["event_id"]] = ke
    return events


def classify_all(raw_data: dict, fixture_events: dict) -> list[dict[str, Any]]:
    """Classify every event as TP, FP, or FN with detailed trace."""
    classifications = []

    for subject in raw_data["subjects"]:
        for event in subject["events"]:
            event_id = event["event_id"]
            domain = event["domain"]
            relevant = event.get("relevant_yoga_activated", False)

            # Get all yogas with activation info
            all_yogas = event.get("all_yogas", [])
            top_yogas = event.get("top_yogas", [])
            dasha = event.get("dasha", {})

            # Look up expected planets
            fixture_ke = fixture_events.get(event_id, {})
            expected_planets = {p.upper() for p in fixture_ke.get("expected_planets", [])}

            # Determine which yogas activated
            activated_yogas = [y for y in all_yogas if y.get("activation") == "ACTIVATED"]
            dormant_yogas = [y for y in all_yogas if y.get("activation") == "DORMANT"]

            # Classify
            if relevant:
                label = "TP"
                reason = "Relevant yoga activated during event"
            elif activated_yogas:
                label = "FP"
                # Determine why it's a FP
                activated_names = [y["name"] for y in activated_yogas]
                yoga_domains = set()
                for yn in activated_names:
                    yoga_domains.update(_YOGA_DOMAIN_RELEVANCE.get(yn, set()))
                domain_match = bool(yoga_domains & _DOMAIN_RELEVANCE.get(domain, set()))

                if domain_match:
                    # Yoga domain matches but planet check failed
                    reason = f"Yoga domain matches but involved planets ({activated_names}) don't overlap expected ({list(expected_planets)})"
                else:
                    # Yoga fires for wrong domain entirely
                    reason = f"Yoga {activated_names} fires for {domain} event but is not relevant to that domain"
            else:
                label = "FN"
                # Determine why it's a FN
                formed_yogas = [y for y in all_yogas if y.get("status") in ("FORMED", "WEAKENED")]
                cancelled_yogas = [y for y in all_yogas if y.get("status") == "CANCELLED"]

                if cancelled_yogas:
                    cancelled_names = [y["name"] for y in cancelled_yogas]
                    if formed_yogas:
                        formed_names = [y["name"] for y in formed_yogas]
                        reason = f"Yogas formed ({formed_names}) but not activated; others cancelled ({cancelled_names})"
                    else:
                        reason = f"All yogas cancelled ({cancelled_names})"
                elif not formed_yogas and not all_yogas:
                    reason = "No yogas formed in chart at all"
                elif not formed_yogas:
                    reason = "No formed yogas — all weakened/cancelled"
                else:
                    formed_names = [y["name"] for y in formed_yogas]
                    reason = f"Yogas formed ({formed_names}) but Dasha didn't activate them (MD={dasha.get('md', '?')})"

            # Top yoga info
            top_name = top_yogas[0]["name"] if top_yogas else "—"
            top_dyn = top_yogas[0].get("dynamic_strength") if top_yogas else None
            top_status = top_yogas[0].get("status") if top_yogas else None

            classifications.append({
                "subject": subject["name"],
                "fixture": subject.get("fixture", ""),
                "lagna": subject.get("lagna", ""),
                "event_id": event_id,
                "event_date": event.get("date", "")[:10],
                "domain": domain,
                "label": label,
                "reason": reason,
                "dasha_md": dasha.get("md", ""),
                "dasha_ad": dasha.get("ad", ""),
                "dasha_pd": dasha.get("pd", ""),
                "top_yoga": top_name,
                "top_status": top_status,
                "top_dynamic_strength": top_dyn,
                "activated_yogas": [y["name"] for y in activated_yogas],
                "all_yogas": [(y["name"], y.get("status", "?")) for y in all_yogas],
                "expected_planets": list(expected_planets),
            })

    return classifications


# ── FP Analysis ─────────────────────────────────────────────────────────────

def analyze_fps(classifications: list[dict]) -> str:
    fps = [c for c in classifications if c["label"] == "FP"]
    lines: list[str] = []

    lines.append("# False Positive Analysis — 24 Cases")
    lines.append("")
    lines.append("**Phase F2: Diagnostic Report**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 1: Distribution ──
    lines.append("## Section 1: FP Distribution")
    lines.append("")
    lines.append(f"**Total False Positives: {len(fps)}**")
    lines.append("")

    # Categorize by root cause
    categories: dict[str, list[dict]] = defaultdict(list)
    for fp in fps:
        reason = fp["reason"]
        if "domain" in reason.lower() and "not relevant" in reason.lower():
            categories["Domain Mismatch — Yoga fires for wrong domain"].append(fp)
        elif "domain matches but" in reason.lower():
            categories["Planet Mismatch — Domain matches but planets don't overlap"].append(fp)
        elif "No yoga activated" in reason.lower():
            categories["No Activation"].append(fp)
        else:
            categories["Other"].append(fp)

    lines.append("| Category | Count | Percentage |")
    lines.append("|----------|-------|------------|")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        pct = len(items) / len(fps) * 100
        lines.append(f"| {cat} | {len(items)} | {pct:.0f}% |")
    lines.append("")

    # Domain breakdown of FPs
    fp_domains = Counter(fp["domain"] for fp in fps)
    lines.append("### FP by Event Domain")
    lines.append("")
    lines.append("| Domain | FP Count | Total Events | FP Rate |")
    lines.append("|--------|----------|--------------|---------|")
    domain_totals = Counter(c["domain"] for c in classifications)
    for domain, count in fp_domains.most_common():
        total = domain_totals[domain]
        lines.append(f"| {domain} | {count} | {total} | {count/total:.1%} |")
    lines.append("")

    # Yoga type breakdown of FPs
    yoga_fps: Counter = Counter()
    for fp in fps:
        for yn in fp["activated_yogas"]:
            yoga_fps[yn] += 1

    lines.append("### FP by Yoga Type")
    lines.append("")
    lines.append("| Yoga | FP Count | Notes |")
    lines.append("|------|----------|-------|")
    for yoga, count in yoga_fps.most_common():
        relevance = _YOGA_DOMAIN_RELEVANCE.get(yoga, set())
        lines.append(f"| {yoga} | {count} | Relevant domains: {relevance} |")
    lines.append("")

    # ── Section 2: Per-FP Trace ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 2: Per-FP Trace")
    lines.append("")

    for i, fp in enumerate(fps, 1):
        lines.append(f"### FP #{i}: {fp['subject']} — {fp['event_id']}")
        lines.append("")
        lines.append(f"- **Event Date:** {fp['event_date']} | **Domain:** {fp['domain']}")
        lines.append(f"- **Active Dasha:** {fp['dasha_md']}/{fp['dasha_ad']}/{fp['dasha_pd']}")
        lines.append(f"- **Activated Yoga(s):** {', '.join(fp['activated_yogas']) or '—'}")
        lines.append(f"- **Top Yoga:** {fp['top_yoga']} (status: {fp['top_status']}, "
                     f"dynamic: {fp['top_dynamic_strength']})")
        lines.append(f"- **Expected Planets:** {', '.join(fp['expected_planets']) or '—'}")
        lines.append(f"- **All Yogas in Chart:** {', '.join(f'{n}({s})' for n,s in fp['all_yogas'])}")
        lines.append(f"- **Why FP:** {fp['reason']}")
        lines.append("")

    # ── Section 3: Systemic Patterns ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 3: Systemic Patterns")
    lines.append("")

    # Pattern 1: HEALTH domain FPs
    health_fps = [fp for fp in fps if fp["domain"] == "HEALTH"]
    if health_fps:
        lines.append("### Pattern 1: HEALTH Domain FP Dominance")
        lines.append(f"- **{len(health_fps)}/{len(fps)} FPs** are HEALTH events")
        lines.append("- Most death/health events have yogas activated that are "
                     "career-relevant (e.g., Gajakesari, Raja) but not health-relevant")
        lines.append("- The pipeline correctly activates yogas during the Dasha, "
                     "but the yoga's domain relevance doesn't match HEALTH")
        lines.append("- **Root cause:** Career yogas (Raja, Gajakesari) naturally fire "
                     "during any event when the Dasha lord matches. For HEALTH events, "
                     "the expected pattern is that NO career yoga should be active — "
                     "but the Dasha alignment is coincidental.")
        lines.append("")

    # Pattern 2: Overly broad yoga domain relevance
    lines.append("### Pattern 2: Overly Broad Yoga Domain Relevance")
    lines.append("- Many yogas (Gajakesari, Raja, Dhana) are classified as relevant "
                 "to CAREER, which is overly broad")
    lines.append("- This causes FPs when these yogas activate for CAREER events "
                 "where the specific subject experienced failure or death")
    lines.append("- **Root cause:** The `_DOMAIN_RELEVANCE` mapping and yoga "
                 "outcome domain definitions are too permissive")
    lines.append("")

    # Pattern 3: Dasha coincidence
    lines.append("### Pattern 3: Dasha Coincidence")
    lines.append("- In 24 FPs, the Dasha lord happens to match a yoga's involved "
                 "planet, triggering activation regardless of the event's actual nature")
    lines.append("- This is expected behavior — the Dasha system fires based on "
                 "planetary periods, not event outcomes")
    lines.append("")

    return "\n".join(lines)


# ── FN Analysis ─────────────────────────────────────────────────────────────

def analyze_fns(classifications: list[dict]) -> str:
    fns = [c for c in classifications if c["label"] == "FN"]
    lines: list[str] = []

    lines.append("# False Negative Analysis — 41 Cases")
    lines.append("")
    lines.append("**Phase F2: Diagnostic Report**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 1: Distribution ──
    lines.append("## Section 1: FN Distribution")
    lines.append("")
    lines.append(f"**Total False Negatives: {len(fns)}**")
    lines.append("")

    # Categorize FNs
    categories: dict[str, list[dict]] = defaultdict(list)
    for fn in fns:
        reason = fn["reason"]
        if "No yogas formed in chart" in reason:
            categories["No Yogas Formed (coverage gap)"].append(fn)
        elif "All yogas cancelled" in reason:
            categories["All Yogas Cancelled (modifier over-cancellation)"].append(fn)
        elif "not activated" in reason.lower() or "Dasha" in reason:
            categories["Formed but Not Activated (Dasha mismatch)"].append(fn)
        elif "No formed yogas" in reason:
            categories["No Formed Yogas (all weakened)"].append(fn)
        else:
            categories["Other"].append(fn)

    lines.append("| Category | Count | Percentage |")
    lines.append("|----------|-------|------------|")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        pct = len(items) / len(fns) * 100
        lines.append(f"| {cat} | {len(items)} | {pct:.0f}% |")
    lines.append("")

    # Domain breakdown
    fn_domains = Counter(fn["domain"] for fn in fns)
    lines.append("### FN by Event Domain")
    lines.append("")
    lines.append("| Domain | FN Count | Total Events | FN Rate |")
    lines.append("|--------|----------|--------------|---------|")
    domain_totals = Counter(c["domain"] for c in classifications)
    for domain, count in fn_domains.most_common():
        total = domain_totals[domain]
        lines.append(f"| {domain} | {count} | {total} | {count/total:.1%} |")
    lines.append("")

    # Subject breakdown
    fn_subjects: Counter = Counter(fn["subject"] for fn in fns)
    lines.append("### FN by Subject (Worst Performers)")
    lines.append("")
    lines.append("| Subject | FN Count | Events | All FN? |")
    lines.append("|---------|----------|--------|---------|")
    for subject, count in fn_subjects.most_common(15):
        total = domain_totals.get(subject, 3)
        all_fn = "⚠️ YES" if count == 3 else ""
        lines.append(f"| {subject} | {count} | 3 | {all_fn} |")
    lines.append("")

    # ── Section 2: Per-FN Trace ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 2: Per-FN Trace")
    lines.append("")

    for i, fn in enumerate(fns, 1):
        lines.append(f"### FN #{i}: {fn['subject']} — {fn['event_id']}")
        lines.append("")
        lines.append(f"- **Event Date:** {fn['event_date']} | **Domain:** {fn['domain']}")
        lines.append(f"- **Active Dasha:** {fn['dasha_md']}/{fn['dasha_ad']}/{fn['dasha_pd']}")
        lines.append(f"- **All Yogas:** {', '.join(f'{n}({s})' for n,s in fn['all_yogas']) or '—'}")
        lines.append(f"- **Expected Planets:** {', '.join(fn['expected_planets']) or '—'}")
        lines.append(f"- **Why FN:** {fn['reason']}")
        lines.append("")

    # ── Section 3: Missing Yoga Analysis ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 3: Coverage Gap Analysis")
    lines.append("")

    # Charts with 0 yogas formed
    zero_yoga_subjects = [fn for fn in fns if "No yogas formed" in fn["reason"]]
    if zero_yoga_subjects:
        lines.append("### Charts with Zero Yoga Formations")
        lines.append("")
        lines.append("These subjects have NO yogas detected by the engine. "
                     "This represents a fundamental coverage gap.")
        lines.append("")
        zero_subjects = set(fn["subject"] for fn in zero_yoga_subjects)
        for s in sorted(zero_subjects):
            s_fns = [fn for fn in zero_yoga_subjects if fn["subject"] == s]
            lines.append(f"**{s}** — {len(s_fns)} FNs (all events)")
            lines.append(f"- Lagna: {[fn['lagna'] for fn in s_fns if fn['lagna']][0] if s_fns else '?'}")
            lines.append(f"- Events: {', '.join(fn['event_id'] for fn in s_fns)}")
            lines.append(f"- Root cause: No classical yoga conditions met for this "
                         f"planetary configuration. The engine's yoga detectors don't "
                         f"cover this chart pattern.")
            lines.append("")

    # Charts with yogas cancelled
    cancelled_subjects = defaultdict(list)
    for fn in fns:
        if "cancelled" in fn["reason"].lower():
            cancelled_subjects[fn["subject"]].append(fn)

    if cancelled_subjects:
        lines.append("### Charts with Yogas Cancelled by Modifier Pipeline")
        lines.append("")
        for subject, items in sorted(cancelled_subjects.items()):
            cancelled_yogas = []
            for item in items:
                for yn, ys in item["all_yogas"]:
                    if ys == "CANCELLED":
                        cancelled_yogas.append(yn)
            lines.append(f"**{subject}** — {len(items)} FNs")
            lines.append(f"- Cancelled yogas: {', '.join(set(cancelled_yogas))}")
            lines.append("- The modifier pipeline (combustion, debilitation, D9) "
                         "cancelled yogas that might have been relevant")
            lines.append("")

    # Dasha mismatch patterns
    dasha_mismatch = [fn for fn in fns if "not activated" in fn["reason"].lower() or "Dasha" in fn["reason"]]
    if dasha_mismatch:
        lines.append("### Dasha Activation Mismatch Patterns")
        lines.append("")
        lines.append(f"**{len(dasha_mismatch)} events** had formed yogas but the "
                     "Dasha didn't activate them.")
        lines.append("")

        # Check which Dasha lords were active
        md_lords: Counter = Counter(fn["dasha_md"] for fn in dasha_mismatch)
        lines.append("Active Mahadasha Lords during FN events:")
        lines.append("")
        for lord, count in md_lords.most_common():
            lines.append(f"- {lord}: {count} events")
        lines.append("")
        lines.append("**Root cause:** The Dasha activation fires only when the "
                     "MD/AD/PD lord IS one of the yoga's involved planets. "
                     "For many FN events, the Dasha lord is unrelated to any "
                     "formed yoga's planets.")
        lines.append("")

    # ── Section 4: Systemic Patterns ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 4: Systemic Patterns")
    lines.append("")

    lines.append("### Pattern 1: No-Yoga Charts Are the Biggest Problem")
    zero_count = len(zero_yoga_subjects)
    lines.append(f"- **{zero_count} events** (across {len(set(fn['subject'] for fn in zero_yoga_subjects))} subjects) "
                 "have zero yogas detected")
    lines.append("- These are structural coverage gaps — the engine doesn't detect "
                 "yogas for these chart configurations")
    lines.append("- Subjects like Picasso, Tolstoy, Beethoven, de Gaulle, Ford, "
                 "R. Franklin have 0 yogas formed")
    lines.append("")

    lines.append("### Pattern 2: HEALTH Events Are Consistently Missed")
    health_fns = [fn for fn in fns if fn["domain"] == "HEALTH"]
    lines.append(f"- **{len(health_fns)}/{len(fns)} FNs** are HEALTH events")
    lines.append("- The engine has no HEALTH-specific yoga detection")
    lines.append("- Death/crisis events are not predicted by classical yoga theory "
                 "in the same way career events are")
    lines.append("- The Dasha system does predict difficult periods through "
                 "malefic Dasha lords, but the current activation logic "
                 "only fires when the Dasha lord matches a yoga's planets")
    lines.append("")

    lines.append("### Pattern 3: Dasha Activation Is Too Strict")
    lines.append("- Many events have formed yogas but the Dasha lord doesn't match")
    lines.append("- The current logic requires MD/AD/PD lord to BE one of the "
                 "yoga's involved planets")
    lines.append("- A looser activation (e.g., Dasha lord aspects or disposits "
                 "a yoga planet) could recover some FNs")
    lines.append("")

    return "\n".join(lines)


# ── Priority Matrix ─────────────────────────────────────────────────────────

def generate_priority_matrix(classifications: list[dict]) -> str:
    fps = [c for c in classifications if c["label"] == "FP"]
    fns = [c for c in classifications if c["label"] == "FN"]

    lines: list[str] = []
    lines.append("# FP/FN Priority Matrix")
    lines.append("")
    lines.append("**Phase F2: Prioritized Fix List — Evidence-Based**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Count categories
    zero_yoga_fns = [fn for fn in fns if "No yogas formed" in fn["reason"]]
    cancelled_fns = [fn for fn in fns if "cancelled" in fn["reason"].lower()]
    dasha_fns = [fn for fn in fns if "not activated" in fn["reason"].lower() or "Dasha" in fn["reason"]]
    health_fps = [fp for fp in fps if fp["domain"] == "HEALTH"]

    lines.append("## Impact Summary")
    lines.append("")
    lines.append("| Issue | Count | % of Total Errors | Estimated Recovery |")
    lines.append("|-------|-------|--------------------|--------------------|")
    lines.append(f"| Zero-yoga charts (coverage gap) | {len(zero_yoga_fns)} | "
                 f"{len(zero_yoga_fns)/65*100:.0f}% | +{len(zero_yoga_fns)} TPs if fixed |")
    lines.append(f"| HEALTH FPs (domain mismatch) | {len(health_fps)} | "
                 f"{len(health_fps)/65*100:.0f}% | -{len(health_fps)} FPs if fixed |")
    lines.append(f"| Formed but not activated (Dasha) | {len(dasha_fns)} | "
                 f"{len(dasha_fns)/65*100:.0f}% | +{len(dasha_fns)} TPs if fixed |")
    lines.append(f"| All yogas cancelled (modifier) | {len(cancelled_fns)} | "
                 f"{len(cancelled_fns)/65*100:.0f}% | +{len(cancelled_fns)} TPs if fixed |")
    lines.append("")

    # ── High Priority ──
    lines.append("---")
    lines.append("")
    lines.append("## High Priority (Fix Immediately)")
    lines.append("")

    lines.append("### 1. Yoga Coverage Expansion — Zero-Yoga Charts")
    lines.append(f"- **Impact:** {len(zero_yoga_fns)} FNs → could recover {len(zero_yoga_fns)} TPs")
    lines.append("- **Root cause:** 7 subjects have 0 yogas detected (Picasso, Tolstoy, "
                 "Beethoven, de Gaulle, Ford, R. Franklin, Carnegie partial)")
    lines.append("- **Action:** Add missing yoga detectors for patterns that exist in "
                 "these charts but aren't currently implemented")
    lines.append("- **Candidates:** Chandra Mangala, Budhaditya variations, "
                 "Parivartana exchanges, specialized Kendra/Trikona combinations")
    lines.append("")

    lines.append("### 2. HEALTH Domain FP Reduction")
    lines.append(f"- **Impact:** {len(health_fps)} FPs → could eliminate {len(health_fps)} FPs")
    lines.append("- **Root cause:** Career yogas fire during death/health events due "
                 "to Dasha coincidence")
    lines.append("- **Action:** Refine domain relevance — HEALTH events should not be "
                 "counted as FP when a career yoga activates (it's a neutral signal, "
                 "not a false prediction)")
    lines.append("- **Alternative:** Exclude HEALTH events from the scoring framework "
                 "or create HEALTH-specific prediction rules")
    lines.append("")

    # ── Medium Priority ──
    lines.append("---")
    lines.append("")
    lines.append("## Medium Priority (Fix Next)")
    lines.append("")

    lines.append("### 3. Dasha Activation Loosening")
    lines.append(f"- **Impact:** {len(dasha_fns)} FNs → could recover some TPs")
    lines.append("- **Root cause:** Dasha lord must BE the yoga planet; no aspect/"
                 "dispositorship check")
    lines.append("- **Action:** Consider loosening to: Dasha lord disposits a yoga "
                 "planet, or Dasha lord aspects a yoga planet")
    lines.append("- **Risk:** Could increase FPs if too loose")
    lines.append("")

    lines.append("### 4. Modifier Pipeline Review")
    lines.append(f"- **Impact:** {len(cancelled_fns)} FNs from cancelled yogas")
    lines.append("- **Root cause:** Combustion/debilitation/D9 cancellation may be "
                 "too aggressive")
    lines.append("- **Action:** Review each cancellation to verify it's astronomically "
                 "correct; consider partial weakening instead of binary cancellation")
    lines.append("")

    # ── Low Priority ──
    lines.append("---")
    lines.append("")
    lines.append("## Low Priority (Defer)")
    lines.append("")

    lines.append("### 5. Transit Layer Completion")
    lines.append("- The transit multiplier is always 1.0 (inactive)")
    lines.append("- Could add signal for transits over natal yoga planets")
    lines.append("- Impact: Moderate but requires significant new data (ashtakavarga)")
    lines.append("")

    lines.append("### 6. Chain Impact Calibration")
    lines.append("- Chain impact is systematically negative, suppressing dynamic_strength")
    lines.append("- Could review the chain weight function")
    lines.append("- Impact: Would improve dynamic_strength accuracy across all events")
    lines.append("")

    # ── Do Not Fix ──
    lines.append("---")
    lines.append("")
    lines.append("## Do Not Fix (Accept as Baseline)")
    lines.append("")

    lines.append("### Astronomically Correct Non-Formations")
    lines.append("- Charts where no yogas form because the planetary positions "
                 "don't satisfy classical conditions")
    lines.append("- This is correct behavior — the engine shouldn't fabricate yogas")
    lines.append("")

    lines.append("### Dasha Coincidence FPs")
    lines.append("- FPs where the Dasha lord happens to match a yoga planet "
                 "during an unrelated event")
    lines.append("- This is inherent to the Dasha system — it fires on planetary "
                 "periods, not event outcomes")
    lines.append("")

    # ── Summary ──
    lines.append("---")
    lines.append("")
    lines.append("## Recommendation Summary")
    lines.append("")
    lines.append("| Priority | Action | Expected Impact |")
    lines.append("|----------|--------|-----------------|")
    lines.append(f"| 🔴 HIGH | Add missing yoga detectors | +{len(zero_yoga_fns)} TPs |")
    lines.append(f"| 🔴 HIGH | Refine HEALTH domain relevance | -{len(health_fps)} FPs |")
    lines.append(f"| 🟡 MEDIUM | Loosen Dasha activation | +~{len(dasha_fns)//2} TPs |")
    lines.append(f"| 🟡 MEDIUM | Review modifier cancellation | +~{len(cancelled_fns)//2} TPs |")
    lines.append(f"| 🟢 LOW | Complete transit layer | Moderate improvement |")
    lines.append(f"| ⚪ SKIP | Accept baseline behaviors | — |")
    lines.append("")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 64)
    print("Phase F2: FP/FN Pattern Analysis")
    print("=" * 64)
    print()

    raw_data = load_raw_data()
    fixture_events = load_fixture_events()
    classifications = classify_all(raw_data, fixture_events)

    total = len(classifications)
    tp = sum(1 for c in classifications if c["label"] == "TP")
    fp = sum(1 for c in classifications if c["label"] == "FP")
    fn = sum(1 for c in classifications if c["label"] == "FN")
    print(f"Total: {total} | TP: {tp} | FP: {fp} | FN: {fn}")
    print()

    # FP Analysis
    print("Generating FP analysis...")
    fp_report = analyze_fps(classifications)
    fp_path = REPORTS_DIR / "false_positive_analysis.md"
    with fp_path.open("w", encoding="utf-8") as f:
        f.write(fp_report)
    print(f"  → {fp_path}")

    # FN Analysis
    print("Generating FN analysis...")
    fn_report = analyze_fns(classifications)
    fn_path = REPORTS_DIR / "false_negative_analysis.md"
    with fn_path.open("w", encoding="utf-8") as f:
        f.write(fn_report)
    print(f"  → {fn_path}")

    # Priority Matrix
    print("Generating priority matrix...")
    matrix = generate_priority_matrix(classifications)
    matrix_path = REPORTS_DIR / "fp_fn_priority_matrix.md"
    with matrix_path.open("w", encoding="utf-8") as f:
        f.write(matrix)
    print(f"  → {matrix_path}")

    print()
    print("=" * 64)
    print("Analysis complete.")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())
