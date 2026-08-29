#!/usr/bin/env python3
"""Phase E6f — Diagnose the 13% Hit Rate Plateau.

For each of the 15 life events across the 5-chart cohort, traces exactly
why no relevant yoga was activated. Categorizes failure modes into
categories A-F to identify the dominant bottleneck.

NO changes to rules, weights, or engine logic.
STRICTLY DIAGNOSE.

Usage::

    python scripts/diagnose_hit_rate_plateau.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone as _tz
from pathlib import Path
from typing import Any

# ── Path setup ──────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

FIXTURES_DIR = (
    _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"
)

# ── Constants (shared with blind_evaluation_cohort.py) ──────────────────────

_RASHI_NUM: dict[str, int] = {
    "MESHA": 1, "VRISHABHA": 2, "MITHUNA": 3, "KARKA": 4,
    "SIMHA": 5, "KANYA": 6, "TULA": 7, "VRISHCHIKA": 8,
    "DHANUSHA": 9, "MAKARA": 10, "KUMBHA": 11, "MEENA": 12,
}

_SIGN_LORDS: dict[int, str] = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

_SIGN_TYPES: dict[int, str] = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}

_RASHI_ORDER: list[str] = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]

_CHART_FILES = [
    "chart_001_pilot.json",
    "chart_002_curie.json",
    "chart_003_mozart.json",
    "chart_004_tesla.json",
    "chart_005_gandhi.json",
]

# Yoga → domain mapping (mirrors map_outcome in service.py)
_YOGA_OUTCOME_MAP: dict[str, str] = {
    "RAJA": "CAREER_PROMINENCE",
    "DHANA": "WEALTH_ACCUMULATION",
    "GAJAKESARI": "GENERAL_IMPROVEMENT",
    "VIPAREETA RAJA": "CAREER_PROMINENCE",
    "NEECHA BHANGA": "GENERAL_IMPROVEMENT",
    "RUCHAKA": "CAREER_PROMINENCE",
    "BHADRA": "CAREER_PROMINENCE",
    "HAMSA": "CAREER_PROMINENCE",
    "MALAVYA": "RELATIONSHIP_HARMONY",
    "SASA": "CAREER_PROMINENCE",
    "ANAPHA": "WEALTH_ACCUMULATION",
    "SUNAPHA": "WEALTH_ACCUMULATION",
    "DHUDHARA": "WEALTH_ACCUMULATION",
}

# Event domain → yoga domains that would be "relevant"
_DOMAIN_RELEVANCE: dict[str, set[str]] = {
    "CAREER": {"CAREER_PROMINENCE", "GENERAL_IMPROVEMENT"},
    "WEALTH": {"WEALTH_ACCUMULATION", "GENERAL_IMPROVEMENT"},
    "HEALTH": {"GENERAL_IMPROVEMENT"},  # health yogas rare
    "MARRIAGE": {"RELATIONSHIP_HARMONY", "GENERAL_IMPROVEMENT"},
    "MIGRATION": {"CAREER_PROMINENCE", "GENERAL_IMPROVEMENT"},
    "DEATH": {"GENERAL_IMPROVEMENT"},  # death yogas rare
}


# ── D9 Helpers (shared) ─────────────────────────────────────────────────────

def _compute_d9_sign(longitude_used: float) -> str:
    sign_index = int(longitude_used / 30.0)
    degree_in_sign = longitude_used - (sign_index * 30.0)
    navamsha_within_sign = int(degree_in_sign / (30.0 / 9.0))
    sign_type = _SIGN_TYPES[sign_index]
    if sign_type == "fire":
        start = sign_index
    elif sign_type == "earth":
        start = (sign_index + 5) % 12
    elif sign_type == "air":
        start = (sign_index + 4) % 12
    else:
        start = (sign_index + 8) % 12
    return _RASHI_ORDER[(start + navamsha_within_sign) % 12]


def _compute_d9_house(longitude_used: float, d9_lagna_lon: float) -> int:
    d9_sign = _compute_d9_sign(longitude_used)
    d9_lagna_sign = _compute_d9_sign(d9_lagna_lon)
    return (_RASHI_ORDER.index(d9_sign) - _RASHI_ORDER.index(d9_lagna_sign)) % 12 + 1


# ── JRE Facts Builder (shared) ──────────────────────────────────────────────

def _build_jre_facts(chart: Any, target_ts: datetime | None = None) -> dict[str, Any]:
    from jyotish.rashi import RASHI_ORDER as JYOTISH_RASHI_ORDER

    lagna_rashi = chart.lagna.rashi.value
    lagna_sign_num = _RASHI_NUM.get(lagna_rashi, 1)
    lagna_longitude = chart.lagna.ascendant_longitude_deg

    lagna_idx = list(JYOTISH_RASHI_ORDER).index(chart.lagna.rashi)
    house_lords: dict[int, str] = {}
    for i in range(12):
        rashi_idx = (lagna_idx + i) % 12
        rashi_name = list(JYOTISH_RASHI_ORDER)[rashi_idx]
        house_lords[i + 1] = _SIGN_LORDS.get(_RASHI_NUM.get(rashi_name, rashi_idx + 1), "")

    _DEBILITATION = {
        "SUN": 7, "MOON": 8, "MARS": 4, "MERCURY": 12,
        "JUPITER": 10, "VENUS": 6, "SATURN": 1,
    }

    planets: dict[str, dict[str, Any]] = {}
    moon_nakshatra = ""
    moon_nakshatra_degree = 0.0

    for ps in chart.planet_states:
        pname = ps.body.value
        planet_rashi = ps.rashi.value
        planet_rashi_idx = list(JYOTISH_RASHI_ORDER).index(ps.rashi)
        house_num = (planet_rashi_idx - lagna_idx) % 12 + 1
        rashi_num = _RASHI_NUM.get(planet_rashi, 0)

        sun_state = next((s for s in chart.planet_states if s.body.value == "SUN"), None)
        is_combust = False
        if sun_state and pname != "SUN":
            diff = abs(ps.longitude_used - sun_state.longitude_used)
            if diff > 180:
                diff = 360 - diff
            is_combust = diff < 8.0

        planets[pname] = {
            "house": house_num,
            "rashi": planet_rashi,
            "rashi_num": rashi_num,
            "combust": is_combust,
            "debilitated": rashi_num == _DEBILITATION.get(pname, -1),
            "retrograde": ps.retrograde.value == "RETROGRADE",
            "longitude": ps.longitude_used,
            "sign_lord": _SIGN_LORDS.get(rashi_num, ""),
        }

        if pname == "MOON":
            moon_nakshatra = ps.nakshatra.value
            moon_nakshatra_degree = ps.longitude_used

    planet_d9_house: dict[str, int] = {}
    planet_d9_sign: dict[str, str] = {}
    for ps in chart.planet_states:
        pname = ps.body.value
        planet_d9_sign[pname] = _compute_d9_sign(ps.longitude_used)
        planet_d9_house[pname] = _compute_d9_house(ps.longitude_used, lagna_longitude)

    moon_data = planets.get("MOON", {})
    natal_moon_house = moon_data.get("house", 1)

    facts: dict[str, Any] = {
        "planets": planets,
        "house_lords": house_lords,
        "lagna_sign": lagna_sign_num,
        "lagna_house": 1,
        "planet_d9_house": planet_d9_house,
        "planet_d9_sign": planet_d9_sign,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_nakshatra_degree,
        "natal_moon_house": natal_moon_house,
    }
    if target_ts is not None:
        facts["target_timestamp"] = target_ts
    return facts


# ── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class YogaTrace:
    yoga_name: str
    status: str
    involved_planets: list[str]
    yoga_domain: str  # from map_outcome
    dynamic_strength: float | None
    chain_impact: float | None
    dasha_multiplier: float | None
    activation_status: str
    activation_source: str
    cancellation_reason: str | None
    modifier_status: str | None


@dataclass
class EventTrace:
    event_id: str
    event_date: str
    domain: str
    description: str
    expected_planets: list[str]
    dasha_md: str
    dasha_ad: str
    dasha_pd: str
    yogas: list[YogaTrace]
    relevant_yoga_activated: bool
    failure_category: str = ""
    failure_reason: str = ""


# ── Main Diagnostic Logic ───────────────────────────────────────────────────

def _diagnose_event(
    chart: Any,
    event: dict[str, Any],
    all_yogas: list[Any],
    birth_dt: datetime,
) -> EventTrace:
    """Trace one event through the pipeline and diagnose failure mode."""
    from jrs.temporal.dasha_engine import VimshottariDashaEngine, DashaHierarchy
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    event_ts = datetime.fromisoformat(event["event_date_utc"].replace("Z", "+00:00"))
    jre_facts = _build_jre_facts(chart, target_ts=event_ts)

    # ── Dasha ──
    dasha_engine = VimshottariDashaEngine()
    moon_nak = jre_facts["moon_nakshatra"]
    moon_deg = jre_facts["moon_nakshatra_degree"]

    hierarchy_at_birth = dasha_engine.compute_dasha_at(birth_dt, moon_nak, moon_deg)
    birth_epoch = hierarchy_at_birth.mahadasha.start_utc
    md_periods = dasha_engine._compute_md_periods(birth_epoch)

    active_md = dasha_engine._find_active_period(md_periods, event_ts)
    if active_md is None:
        active_md = hierarchy_at_birth.mahadasha

    ad_periods = dasha_engine._compute_sub_periods(active_md, "AD")
    active_ad = dasha_engine._find_active_period(ad_periods, event_ts)
    if active_ad is None:
        active_ad = ad_periods[0]

    pd_periods = dasha_engine._compute_sub_periods(active_ad, "PD")
    active_pd = dasha_engine._find_active_period(pd_periods, event_ts)
    if active_pd is None:
        active_pd = pd_periods[0]

    hierarchy = DashaHierarchy(mahadasha=active_md, antardasha=active_ad, pratyantardasha=active_pd)

    # ── Yoga evaluation ──
    evaluator = YogaEvaluatorService()
    yoga_traces: list[YogaTrace] = []

    event_domain = event["domain"]
    relevant_domains = _DOMAIN_RELEVANCE.get(event_domain, set())

    for yoga_eval in all_yogas:
        involved: list[str] = []
        if yoga_eval.modifier_report is not None:
            involved = [pr.planet for pr in yoga_eval.modifier_report.planet_results]

        dasha_mult_result = dasha_engine.get_dasha_multiplier(hierarchy, involved)

        activation_status = "DORMANT"
        activation_source = ""
        if dasha_mult_result.matched_level != "NONE":
            activation_status = "ACTIVATED"
            activation_source = f"Dasha {dasha_mult_result.matched_level}: {dasha_mult_result.matched_planet}"

        static_strength = 1.0
        if yoga_eval.modifier_report is not None:
            static_strength = yoga_eval.modifier_report.overall_strength

        yoga_domain = evaluator.map_outcome(yoga_eval.yoga_name)

        yoga_traces.append(YogaTrace(
            yoga_name=yoga_eval.yoga_name,
            status=yoga_eval.status.value,
            involved_planets=involved,
            yoga_domain=yoga_domain,
            dynamic_strength=yoga_eval.dynamic_strength,
            chain_impact=yoga_eval.chain_impact,
            dasha_multiplier=dasha_mult_result.multiplier,
            activation_status=activation_status,
            activation_source=activation_source,
            cancellation_reason=yoga_eval.cancellation_reason,
            modifier_status=yoga_eval.modifier_report.overall_status.value
                if yoga_eval.modifier_report is not None else None,
        ))

    # ── Check activation (same logic as blind_evaluation_cohort.py) ──
    expected_planets_upper = {p.upper() for p in event.get("expected_planets", [])}
    relevant_activated = False
    for yt in yoga_traces:
        if yt.activation_status == "ACTIVATED" and yt.status != "CANCELLED":
            yoga_planets_upper = {p.upper() for p in yt.involved_planets}
            if yoga_planets_upper & expected_planets_upper:
                relevant_activated = True
                break

    # ── Diagnose failure mode ──
    failure_category = ""
    failure_reason = ""

    if relevant_activated:
        failure_category = "HIT"
        failure_reason = "Relevant yoga activated"
    else:
        # Check each yoga to determine why it didn't contribute
        reasons: list[str] = []

        # A. No yoga detected at all for this domain
        domain_yogas = [
            yt for yt in yoga_traces
            if yt.yoga_domain in relevant_domains or event_domain == yt.yoga_domain
        ]

        if not yoga_traces:
            failure_category = "A"
            failure_reason = "No yoga detected at all by the engine"
        else:
            # For each formed/weakened yoga, check why it wasn't activated
            formed_yogas = [yt for yt in yoga_traces if yt.status in ("FORMED", "WEAKENED")]
            if not formed_yogas:
                # All yogas cancelled
                cancelled = [yt for yt in yoga_traces if yt.status == "CANCELLED"]
                if cancelled:
                    failure_category = "B"
                    names = [f"{yt.yoga_name}({yt.cancellation_reason or yt.modifier_status})" for yt in cancelled]
                    failure_reason = f"All {len(cancelled)} yogas cancelled: {', '.join(names)}"
                else:
                    failure_category = "A"
                    failure_reason = "No formed/weakened yogas detected"
            else:
                # Check Dasha mismatch for formed yogas
                activated_yogas = [yt for yt in formed_yogas if yt.activation_status == "ACTIVATED"]
                non_activated = [yt for yt in formed_yogas if yt.activation_status == "DORMANT"]

                if activated_yogas:
                    # Yoga activated but planets don't match expected
                    for yt in activated_yogas:
                        yoga_set = {p.upper() for p in yt.involved_planets}
                        overlap = yoga_set & expected_planets_upper
                        if not overlap:
                            # Activated yoga doesn't involve expected planets
                            # Check domain alignment
                            yoga_domain_ok = yt.yoga_domain in relevant_domains
                            if yoga_domain_ok:
                                # Domain matches but planet mismatch
                                failure_category = "C"
                                failure_reason = (
                                    f"{yt.yoga_name} ACTIVATED with {yt.activation_source} "
                                    f"but involved_planets={yt.involved_planets} don't overlap "
                                    f"expected_planets={event.get('expected_planets', [])}"
                                )
                            else:
                                # Neither domain nor planet match
                                failure_category = "F"
                                failure_reason = (
                                    f"{yt.yoga_name} ACTIVATED but yoga_domain={yt.yoga_domain} "
                                    f"is not in relevant_domains={relevant_domains} "
                                    f"AND involved_planets={yt.involved_planets} don't match "
                                    f"expected_planets={event.get('expected_planets', [])}"
                                )
                            break
                elif non_activated:
                    # Formed yogas exist but none activated by Dasha
                    first = non_activated[0]
                    yoga_set = {p.upper() for p in first.involved_planets}
                    overlap = yoga_set & expected_planets_upper
                    if overlap:
                        # Planets match but Dasha doesn't activate
                        failure_category = "C"
                        failure_reason = (
                            f"{first.yoga_name} formed with matching planets {list(overlap)} "
                            f"but Dasha lords [{hierarchy.md_lord}/{hierarchy.ad_lord}/{hierarchy.pd_lord}] "
                            f"don't match involved_planets={first.involved_planets}"
                        )
                    else:
                        # Neither matches
                        yoga_domain_ok = first.yoga_domain in relevant_domains
                        if yoga_domain_ok:
                            failure_category = "C"
                            failure_reason = (
                                f"{first.yoga_name} formed, domain={first.yoga_domain} is relevant, "
                                f"but Dasha lords [{hierarchy.md_lord}/{hierarchy.ad_lord}/{hierarchy.pd_lord}] "
                                f"don't match involved_planets={first.involved_planets}"
                            )
                        else:
                            failure_category = "F"
                            failure_reason = (
                                f"{first.yoga_name} formed but yoga_domain={first.yoga_domain} "
                                f"not in relevant_domains={relevant_domains}, "
                                f"Dasha [{hierarchy.md_lord}/{hierarchy.ad_lord}/{hierarchy.pd_lord}] "
                                f"doesn't match involved_planets={first.involved_planets}"
                            )
                else:
                    failure_category = "D"
                    failure_reason = "No formed yogas with sufficient strength"

    return EventTrace(
        event_id=event["event_id"],
        event_date=event["event_date_utc"][:10],
        domain=event["domain"],
        description=event.get("description", ""),
        expected_planets=event.get("expected_planets", []),
        dasha_md=hierarchy.md_lord,
        dasha_ad=hierarchy.ad_lord,
        dasha_pd=hierarchy.pd_lord,
        yogas=yoga_traces,
        relevant_yoga_activated=relevant_activated,
        failure_category=failure_category,
        failure_reason=failure_reason,
    )


def _generate_report(
    traces: dict[str, list[EventTrace]],
    category_counts: Counter,
    total_events: int,
) -> str:
    lines: list[str] = []

    lines.append("# Hit Rate Plateau Diagnosis — Phase E6f")
    lines.append("")
    lines.append("**Objective:** Trace why the hit rate is stuck at 13% across all 15 events.")
    lines.append("")

    # ── Section 1: Failure Mode Distribution ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 1: Failure Mode Distribution")
    lines.append("")
    lines.append(f"**Total events:** {total_events}")
    lines.append("")

    category_names = {
        "HIT": "HIT (relevant yoga activated)",
        "A": "A — No Yoga Detected",
        "B": "B — Yoga Detected but All Cancelled",
        "C": "C — Yoga Formed but Dasha Mismatch",
        "D": "D — Yoga Formed but Strength Too Low",
        "E": "E — Transit Layer Inactive",
        "F": "F — Domain/Planet Alignment Issue",
    }

    lines.append("| Category | Count | Percentage | Description |")
    lines.append("|----------|-------|------------|-------------|")
    for cat in ["HIT", "A", "B", "C", "D", "E", "F"]:
        count = category_counts.get(cat, 0)
        pct = f"{count / total_events * 100:.0f}%" if total_events else "0%"
        desc = category_names.get(cat, cat)
        lines.append(f"| {cat} | {count} | {pct} | {desc} |")
    lines.append("")

    # ── Section 2: Per-Event Trace ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 2: Per-Event Trace")
    lines.append("")

    for subject_name, event_traces in traces.items():
        lines.append(f"### {subject_name}")
        lines.append("")

        for et in event_traces:
            hit_marker = "✅" if et.relevant_yoga_activated else "❌"
            lines.append(f"#### {et.event_id} — {et.event_date} ({et.domain}) {hit_marker}")
            lines.append(f"**Description:** {et.description}")
            lines.append(f"**Active Dasha:** {et.dasha_md} / {et.dasha_ad} / {et.dasha_pd}")
            lines.append(f"**Expected Planets:** {', '.join(et.expected_planets) if et.expected_planets else '—'}")
            lines.append("")

            if et.failure_category != "HIT":
                lines.append(f"**Failure Category:** {et.failure_category} — {et.failure_reason}")
                lines.append("")

            # Yoga table
            if et.yogas:
                lines.append("| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |")
                lines.append("|------|--------|----------|--------|-------------|--------------|------------|------------|")
                for yt in et.yogas:
                    dyn = f"{yt.dynamic_strength:.4f}" if yt.dynamic_strength is not None else "—"
                    chain = f"{yt.chain_impact:.4f}" if yt.chain_impact is not None else "—"
                    dm = f"{yt.dasha_multiplier:.2f}" if yt.dasha_multiplier is not None else "—"
                    inv = ", ".join(yt.involved_planets) if yt.involved_planets else "—"
                    act = f"{yt.activation_status}"
                    if yt.activation_source:
                        act += f" ({yt.activation_source})"
                    lines.append(
                        f"| {yt.yoga_name} | {yt.status} | {inv} | {yt.yoga_domain} "
                        f"| {dyn} | {chain} | {dm} | {act} |"
                    )
                lines.append("")

        lines.append("")

    # ── Section 3: Dominant Bottleneck Identification ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 3: Dominant Bottleneck Identification")
    lines.append("")

    # Find the dominant failure category (excluding HIT)
    non_hit = {k: v for k, v in category_counts.items() if k != "HIT"}
    if non_hit:
        dominant_cat = max(non_hit, key=non_hit.get)
        dominant_count = non_hit[dominant_cat]
        dominant_pct = dominant_count / total_events * 100
        lines.append(f"**Dominant failure category:** {dominant_cat} — "
                     f"{dominant_count}/{total_events} events ({dominant_pct:.0f}%)")
        lines.append("")
        lines.append(f"**Interpretation:** {category_names.get(dominant_cat, dominant_cat)}")
        lines.append("")

    # Analyze why C (Dasha Mismatch) is dominant
    c_events = []
    for subject_name, event_traces in traces.items():
        for et in event_traces:
            if et.failure_category == "C":
                c_events.append((subject_name, et))

    if c_events:
        lines.append("### Dasha Mismatch Analysis (Category C)")
        lines.append("")
        lines.append("For each Category C event, the chain of failure is:")
        lines.append("")
        for subject_name, et in c_events:
            # Analyze the specific mismatch
            involved_set = set()
            for yt in et.yogas:
                if yt.status in ("FORMED", "WEAKENED"):
                    involved_set.update(yt.involved_planets)

            expected_set = {p.upper() for p in et.expected_planets}
            overlap = involved_set & expected_set

            lines.append(f"- **{et.event_id}** ({subject_name}):")
            lines.append(f"  - Yoga involved_planets: {sorted(involved_set)}")
            lines.append(f"  - Fixture expected_planets: {sorted(expected_set)}")
            lines.append(f"  - Overlap: {sorted(overlap) if overlap else 'NONE'}")
            lines.append(f"  - Dasha lords: {et.dasha_md}/{et.dasha_ad}/{et.dasha_pd}")

            # Check if any dasha lord is in involved_planets
            dasha_lords = {et.dasha_md, et.dasha_ad, et.dasha_pd}
            dasha_overlap = dasha_lords & involved_set
            lines.append(f"  - Dasha lords in involved_planets: {sorted(dasha_overlap) if dasha_overlap else 'NONE'}")
            lines.append("")

    # Analyze B (All Cancelled) events
    b_events = []
    for subject_name, event_traces in traces.items():
        for et in event_traces:
            if et.failure_category == "B":
                b_events.append((subject_name, et))

    if b_events:
        lines.append("### Cancellation Analysis (Category B)")
        lines.append("")
        for subject_name, et in b_events:
            lines.append(f"- **{et.event_id}** ({subject_name}):")
            for yt in et.yogas:
                if yt.status == "CANCELLED":
                    lines.append(f"  - {yt.yoga_name}: cancelled by {yt.cancellation_reason or yt.modifier_status}")
            lines.append("")

    # Analyze F (Alignment) events
    f_events = []
    for subject_name, event_traces in traces.items():
        for et in event_traces:
            if et.failure_category == "F":
                f_events.append((subject_name, et))

    if f_events:
        lines.append("### Domain/Planet Alignment Analysis (Category F)")
        lines.append("")
        for subject_name, et in f_events:
            lines.append(f"- **{et.event_id}** ({subject_name}): {et.failure_reason}")
        lines.append("")

    # ── Section 4: Recommended Next Actions ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 4: Recommended Next Actions")
    lines.append("")

    if non_hit:
        dominant_cat = max(non_hit, key=non_hit.get)
        dominant_count = non_hit[dominant_cat]

        if dominant_cat == "C":
            lines.append("### Fix 1: Bridge Dasha-Planet Mismatch (Category C — "
                        f"{dominant_count}/{total_events} events)")
            lines.append("")
            lines.append("The activation check requires the Dasha lord to be one of the "
                        "yoga's *involved_planets*. But the fixture's expected_planets "
                        "may reference planets that are relevant to the event's domain "
                        "but are NOT the primary yoga participants.")
            lines.append("")
            lines.append("**Surgical fix:** In the activation check, also consider "
                        "planets that are:")
            lines.append("- Functional lords of houses the yoga affects (e.g., 10th lord for career)")
            lines.append("- Dispositor chain members of the yoga's primary planet")
            lines.append("- Nakshatra lords of the yoga's primary planet")
            lines.append("")

        if dominant_cat == "B":
            lines.append("### Fix 1: Investigate Modifier Cancellation Thresholds "
                        f"(Category B — {dominant_count}/{total_events} events)")
            lines.append("")
            lines.append("All yogas for these events were cancelled by the modifier "
                        "pipeline. This suggests the cancellation conditions are too "
                        "aggressive (e.g., any debilitation anywhere cancels a yoga).")
            lines.append("")

        if dominant_cat == "F":
            lines.append("### Fix 1: Improve Domain Mapping and Planet Alignment "
                        f"(Category F — {dominant_count}/{total_events} events)")
            lines.append("")
            lines.append("Yogas are detected but their domains don't match the event's "
                        "domain, AND their involved_planets don't match expected_planets. "
                        "This indicates a gap between the engine's yoga detection scope "
                        "and the event's astrological relevance.")
            lines.append("")

    # Always recommend transit data
    transit_events = sum(
        1 for subjects in traces.values()
        for et in subjects
        if any(yt.activation_status == "DORMANT" for yt in et.yogas)
    )
    lines.append("### Fix 2: Activate Transit Layer (Layer 3)")
    lines.append("")
    lines.append("All transit multipliers are 1.0 (inactive). Adding ashtakavarga_scores "
                "and transit_houses to jre_facts would differentiate dynamic strengths "
                "and potentially activate yogas that are currently DORMANT.")
    lines.append("")

    lines.append("### Fix 3: Expand Yoga Detection Scope")
    lines.append("")
    lines.append("Some events have NO yogas detected (Category A) or only yogas with "
                "wrong domains (Category F). Consider adding detection for:")
    lines.append("- Career-specific yogas (D10-based)")
    lines.append("- Event-specific yogas (e.g., Mars-Saturn for accidents)")
    lines.append("- Neecha Bhanga for debilitated planets in key houses")
    lines.append("")

    # ── Methodology Footer ──
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("This diagnostic traces each of 15 events through the full 5-layer "
                "JRE pipeline, comparing the engine's output against the fixture's "
                "expected_planets. No calibration or tuning was applied.")
    lines.append("")
    lines.append("### Failure Mode Categories:")
    lines.append("- **A — No Yoga Detected:** Engine didn't detect any yoga for this event")
    lines.append("- **B — Not Formed:** Yoga exists but formation conditions failed (cancellation)")
    lines.append("- **C — Dasha Mismatch:** Yoga is strong but Dasha lord doesn't match participants")
    lines.append("- **D — Strength Too Low:** Dynamic strength below activation threshold")
    lines.append("- **E — Transit Inactive:** Layer 3 transit multiplier not contributing")
    lines.append("- **F — Alignment Issue:** Fixture expected_planets doesn't match engine's yoga tracking")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    from jyotish.models import BirthData
    from jyotish.service import JyotishService
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    svc = JyotishService()
    evaluator = YogaEvaluatorService()

    traces: dict[str, list[EventTrace]] = {}
    category_counts: Counter = Counter()
    total_events = 0

    print("=" * 70)
    print("HIT RATE PLATEAU DIAGNOSIS — Phase E6f")
    print("=" * 70)
    print()

    for chart_file in _CHART_FILES:
        fixture_path = FIXTURES_DIR / chart_file
        if not fixture_path.exists():
            print(f"  SKIP: {fixture_path} not found", file=sys.stderr)
            continue

        with fixture_path.open(encoding="utf-8") as f:
            fixture = json.load(f)

        subject_name = fixture["_meta"]["subject"]
        print(f"{'=' * 60}")
        print(f"  {subject_name} ({chart_file})")
        print(f"{'=' * 60}")

        raw = fixture["raw_birth_data"]
        birth = BirthData(
            date=raw["date"], time=raw["time"], timezone=raw["timezone"],
            latitude=float(raw["latitude"]), longitude=float(raw["longitude"]),
        )
        chart = svc.chart(birth)

        if chart.planet_states:
            utc_str = chart.planet_states[0].timestamp_utc_iso
            birth_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        else:
            birth_dt = datetime.fromisoformat(f"{raw['date']}T{raw['time']}").replace(tzinfo=_tz.utc)

        jre_facts_natal = _build_jre_facts(chart)
        all_yogas = evaluator.evaluate_classical_yogas(jre_facts_natal)

        print(f"  Lagna: {chart.lagna.rashi.value} | Yogas: {len(all_yogas)}")
        for y in all_yogas:
            inv = [pr.planet for pr in y.modifier_report.planet_results] if y.modifier_report else []
            print(f"    - {y.yoga_name}: {y.status.value} ({', '.join(inv) if inv else '—'})")
        print()

        subject_traces: list[EventTrace] = []
        for event in fixture["known_events"]:
            et = _diagnose_event(chart, event, all_yogas, birth_dt)
            subject_traces.append(et)
            total_events += 1
            category_counts[et.failure_category] += 1

            status = "✅" if et.relevant_yoga_activated else "❌"
            print(f"    {et.event_id}: [{et.failure_category}] {et.failure_reason[:80]} {status}")

        traces[subject_name] = subject_traces
        print()

    # ── Summary ──
    print("=" * 70)
    print(f"FAILURE MODE DISTRIBUTION ({total_events} events)")
    print("=" * 70)
    for cat in ["HIT", "A", "B", "C", "D", "E", "F"]:
        count = category_counts.get(cat, 0)
        if count > 0:
            print(f"  {cat}: {count}/{total_events} ({count/total_events*100:.0f}%)")
    print()

    # ── Generate report ──
    report = _generate_report(traces, category_counts, total_events)

    output_dir = _PROJECT_ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "hit_rate_plateau_diagnosis.md"

    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to: {report_path}")
    print()

    # Also output full trace as JSON for programmatic consumption
    json_data: dict[str, Any] = {}
    for subject_name, subject_traces in traces.items():
        json_data[subject_name] = []
        for et in subject_traces:
            json_data[subject_name].append({
                "event_id": et.event_id,
                "date": et.event_date,
                "domain": et.domain,
                "dasha": f"{et.dasha_md}/{et.dasha_ad}/{et.dasha_pd}",
                "expected_planets": et.expected_planets,
                "failure_category": et.failure_category,
                "failure_reason": et.failure_reason,
                "relevant_yoga_activated": et.relevant_yoga_activated,
                "yogas": [
                    {
                        "name": yt.yoga_name,
                        "status": yt.status,
                        "involved_planets": yt.involved_planets,
                        "yoga_domain": yt.yoga_domain,
                        "dynamic_strength": yt.dynamic_strength,
                        "chain_impact": yt.chain_impact,
                        "dasha_multiplier": yt.dasha_multiplier,
                        "activation": yt.activation_status,
                    }
                    for yt in et.yogas
                ],
            })

    json_path = output_dir / "hit_rate_plateau_diagnosis.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, sort_keys=True)

    print(f"JSON data written to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
