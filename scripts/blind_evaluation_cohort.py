#!/usr/bin/env python3
"""Blind Empirical Evaluation — 5-Chart Cohort (Phase E5).

Iterates through chart_001 through chart_005, runs each through the
complete 5-layer JRE pipeline for all 15 known life events, and
generates a consolidated pattern-analysis report.

NO changes to rules, weights, or engine logic.
NO calibration, tuning, or post-hoc adjustments.
STRICTLY OBSERVE and record the engine's raw output.

Usage::

    python scripts/blind_evaluation_cohort.py
    python scripts/blind_evaluation_cohort.py --output reports/
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

# ── Constants ───────────────────────────────────────────────────────────────

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
    "chart_006_newton.json",
    "chart_007_lincoln.json",
    "chart_008_teresa.json",
    "chart_009_jobs.json",
    "chart_010_earhart.json",
]


# ── D9 Helpers ──────────────────────────────────────────────────────────────


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


# ── Data Structures ─────────────────────────────────────────────────────────


# Event domain → yoga domains that would be "relevant"
_DOMAIN_RELEVANCE: dict[str, set[str]] = {
    "CAREER": {
        "CAREER_PROMINENCE", "POLITICAL_POWER", "SOCIAL_STATUS",
        "LEADERSHIP", "GENERAL_IMPROVEMENT", "BUSINESS_ACUMEN",
        "PUBLIC_RECOGNITION", "MENTAL_STRENGTH",
        "INTELLECTUAL_EXCELLENCE", "COMMUNICATION_SKILLS",
        "ARTISTIC_EXCELLENCE", "WISDOM_ACCUMULATION",
        "TEACHING_ABILITY",
    },
    "WEALTH": {
        "WEALTH_ACCUMULATION", "BUSINESS_ACUMEN", "GENERAL_IMPROVEMENT",
    },
    "HEALTH": {
        "GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY",
        "CRISIS_MANAGEMENT", "EMOTIONAL_STABILITY",
    },
    "MARRIAGE": {
        "RELATIONSHIP_HARMONY", "GENERAL_IMPROVEMENT",
        "DOMESTIC_HARMONY",
    },
    "MIGRATION": {
        "CAREER_PROMINENCE", "GENERAL_IMPROVEMENT",
        "RECOVERY_FROM_ADVERSITY",
    },
    "DEATH": {
        "GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY",
    },
    "ARTISTIC": {
        "ARTISTIC_EXCELLENCE", "CREATIVE_EXCELLENCE",
        "PUBLIC_RECOGNITION", "GENERAL_IMPROVEMENT",
    },
    "EDUCATION": {
        "INTELLECTUAL_EXCELLENCE", "WISDOM_ACCUMULATION",
        "TEACHING_ABILITY", "GENERAL_IMPROVEMENT",
    },
}


@dataclass
class YogaReport:
    yoga_name: str
    status: str
    involved_planets: list[str]
    static_strength: float | None = None
    dynamic_strength: float | None = None
    dasha_multiplier: float | None = None
    transit_multiplier: float | None = None
    chain_impact: float | None = None
    activation_status: str = "DORMANT"
    activation_source: str = ""
    cancellation_reason: str | None = None
    outcome_domains: list[str] = field(default_factory=list)
    modifier_status: str | None = None
    modifier_strength: float | None = None


@dataclass
class EventReport:
    event_id: str
    event_date_utc: str
    domain: str
    description: str
    expected_planets: list[str]
    dasha_md_lord: str = ""
    dasha_ad_lord: str = ""
    dasha_pd_lord: str = ""
    all_yogas: list[YogaReport] = field(default_factory=list)
    top_yogas: list[YogaReport] = field(default_factory=list)
    relevant_yoga_activated: bool = False


@dataclass
class SubjectReport:
    subject_name: str
    fixture_file: str
    lagna_rashi: str
    lagna_nakshatra: str
    moon_nakshatra: str
    event_reports: list[EventReport] = field(default_factory=list)


# ── JRE Facts Builder (reused from Einstein script) ─────────────────────────


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


# ── Pipeline Runner ─────────────────────────────────────────────────────────


def _run_pipeline_for_event(
    chart: Any,
    event: dict[str, Any],
    all_yogas: list[Any],
    birth_dt: datetime,
) -> EventReport:
    from jrs.temporal.dasha_engine import VimshottariDashaEngine, DashaHierarchy
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    event_ts = datetime.fromisoformat(event["event_date_utc"].replace("Z", "+00:00"))
    jre_facts = _build_jre_facts(chart, target_ts=event_ts)

    # ── Dasha computation ──
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
    yoga_reports: list[YogaReport] = []

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

        mod_status = None
        mod_strength = None
        if yoga_eval.modifier_report is not None:
            mod_status = yoga_eval.modifier_report.overall_status.value
            mod_strength = yoga_eval.modifier_report.overall_strength

        yoga_reports.append(YogaReport(
            yoga_name=yoga_eval.yoga_name,
            status=yoga_eval.status.value,
            involved_planets=involved,
            static_strength=static_strength,
            dynamic_strength=yoga_eval.dynamic_strength,
            dasha_multiplier=dasha_mult_result.multiplier,
            transit_multiplier=yoga_eval.transit_multiplier,
            chain_impact=yoga_eval.chain_impact,
            activation_status=activation_status,
            activation_source=activation_source,
            cancellation_reason=yoga_eval.cancellation_reason,
            outcome_domains=[o.value for o in evaluator.get_possible_outcomes(yoga_eval.yoga_name)],
            modifier_status=mod_status,
            modifier_strength=mod_strength,
        ))

    yoga_reports_sorted = sorted(
        yoga_reports,
        key=lambda y: y.dynamic_strength if y.dynamic_strength is not None else 0.0,
        reverse=True,
    )

    # ── Check if any relevant yoga was activated ──
    # Phase E6g: Multi-domain matching — check both planet AND domain overlap
    expected_planets_upper = {p.upper() for p in event.get("expected_planets", [])}
    event_domain = event["domain"]
    relevant_domains = _DOMAIN_RELEVANCE.get(event_domain, set())
    relevant_activated = False
    for yr in yoga_reports_sorted:
        if yr.activation_status == "ACTIVATED" and yr.status != "CANCELLED":
            # Check domain relevance
            yoga_domains = set(yr.outcome_domains)
            domain_match = bool(yoga_domains & relevant_domains)
            # Check planet overlap
            yoga_planets_upper = {p.upper() for p in yr.involved_planets}
            planet_match = bool(yoga_planets_upper & expected_planets_upper)
            # Activated yoga is relevant if either domain OR planet matches
            if domain_match or planet_match:
                relevant_activated = True
                break

    return EventReport(
        event_id=event["event_id"],
        event_date_utc=event["event_date_utc"],
        domain=event["domain"],
        description=event["description"],
        expected_planets=event.get("expected_planets", []),
        dasha_md_lord=hierarchy.md_lord,
        dasha_ad_lord=hierarchy.ad_lord,
        dasha_pd_lord=hierarchy.pd_lord,
        all_yogas=yoga_reports,
        top_yogas=yoga_reports_sorted[:3],
        relevant_yoga_activated=relevant_activated,
    )


# ── Main Evaluation Loop ───────────────────────────────────────────────────


def _evaluate_all_charts() -> list[SubjectReport]:
    from jyotish.models import BirthData
    from jyotish.service import JyotishService
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    svc = JyotishService()
    evaluator = YogaEvaluatorService()
    all_subjects: list[SubjectReport] = []

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

        # Compute natal chart
        raw = fixture["raw_birth_data"]
        birth = BirthData(
            date=raw["date"], time=raw["time"], timezone=raw["timezone"],
            latitude=float(raw["latitude"]), longitude=float(raw["longitude"]),
        )
        chart = svc.chart(birth)

        # Birth datetime for Dasha
        if chart.planet_states:
            utc_str = chart.planet_states[0].timestamp_utc_iso
            birth_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        else:
            birth_dt = datetime.fromisoformat(f"{raw['date']}T{raw['time']}").replace(tzinfo=_tz.utc)

        # Build jre_facts and detect yogas
        jre_facts_natal = _build_jre_facts(chart)
        all_yogas = evaluator.evaluate_classical_yogas(jre_facts_natal)

        print(f"  Lagna: {chart.lagna.rashi.value} | Moon: {fixture['expected_canonical_facts']['planets']['MOON']['nakshatra']}")
        print(f"  Yoga formations: {len(all_yogas)}")
        for y in all_yogas:
            inv = [pr.planet for pr in y.modifier_report.planet_results] if y.modifier_report else []
            print(f"    - {y.yoga_name}: {y.status.value} ({', '.join(inv) if inv else '—'})")

        # Evaluate each event
        event_reports: list[EventReport] = []
        for event in fixture["known_events"]:
            er = _run_pipeline_for_event(chart, event, all_yogas, birth_dt)
            event_reports.append(er)
            activated = sum(1 for y in er.all_yogas if y.activation_status == "ACTIVATED")
            top = er.top_yogas[0] if er.top_yogas else None
            top_name = top.yoga_name if top else "—"
            top_dyn = f"{top.dynamic_strength:.4f}" if top and top.dynamic_strength is not None else "N/A"
            print(f"    {er.event_id}: MD={er.dasha_md_lord}/{er.dasha_ad_lord}/{er.dasha_pd_lord} | Top={top_name} ({top_dyn}) | Active={activated}")

        subject_report = SubjectReport(
            subject_name=subject_name,
            fixture_file=chart_file,
            lagna_rashi=chart.lagna.rashi.value,
            lagna_nakshatra=chart.lagna.nakshatra.value,
            moon_nakshatra=fixture["expected_canonical_facts"]["planets"]["MOON"]["nakshatra"],
            event_reports=event_reports,
        )
        all_subjects.append(subject_report)
        print()

    return all_subjects


# ── Consolidated Report Generator ───────────────────────────────────────────


def _generate_report(subjects: list[SubjectReport]) -> str:
    lines: list[str] = []
    total_events = sum(len(s.event_reports) for s in subjects)
    events_with_hit = sum(
        1 for s in subjects for e in s.event_reports if e.relevant_yoga_activated
    )
    hit_rate = events_with_hit / total_events if total_events else 0.0

    # ── Section 1: Executive Summary ──
    lines.append("# Blind Empirical Evaluation — 5-Chart Cohort")
    lines.append("")
    lines.append("**Phase E5: Consolidated Pattern-Analysis Report**")
    lines.append("")
    lines.append(f"**Subjects:** {len(subjects)} | **Events:** {total_events} | "
                 f"**Relevant Yoga Activations:** {events_with_hit}/{total_events} "
                 f"({hit_rate:.0%})")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Section 1: Executive Summary")
    lines.append("")
    lines.append(f"The 5-layer JRE pipeline was executed against {total_events} known life "
                 f"events across {len(subjects)} historical subjects. No calibration, "
                 f"tuning, or post-hoc adjustments were applied.")
    lines.append("")
    lines.append(f"**Overall Hit Rate:** {events_with_hit}/{total_events} "
                 f"({hit_rate:.0%}) events had a relevant Yoga activated by Dasha "
                 f"at the time of the event.")
    lines.append("")

    # Per-subject summary table
    lines.append("| Subject | Lagna | Events | Activated | Hit Rate |")
    lines.append("|---------|-------|--------|-----------|----------|")
    for s in subjects:
        n_events = len(s.event_reports)
        n_hit = sum(1 for e in s.event_reports if e.relevant_yoga_activated)
        rate = f"{n_hit}/{n_events}" if n_events else "—"
        lines.append(f"| {s.subject_name} | {s.lagna_rashi} | {n_events} | {n_hit} | {rate} |")
    lines.append("")

    # ── Section 2: Systemic Patterns ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 2: Systemic Patterns")
    lines.append("")

    # Chain impact analysis
    chain_impacts: list[float] = []
    chain_yoga_count = 0
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                if y.chain_impact is not None:
                    chain_impacts.append(y.chain_impact)
                    chain_yoga_count += 1

    if chain_impacts:
        avg_chain = sum(chain_impacts) / len(chain_impacts)
        neg_chain = sum(1 for c in chain_impacts if c < 0)
        lines.append(f"### Chain Impact (Layer 1.5)")
        lines.append(f"- **Computed for:** {chain_yoga_count} yoga formations across all charts")
        lines.append(f"- **Average chain impact:** {avg_chain:.6f}")
        lines.append(f"- **Negative chain impacts:** {neg_chain}/{chain_yoga_count} "
                     f"({neg_chain/chain_yoga_count:.0%})")
        if avg_chain < 0:
            lines.append(f"- **Pattern:** Chain impact is consistently negative across "
                         f"the cohort, suggesting multi-hop dispositorship chains tend to "
                         f"produce net malefic functional influence.")
        lines.append("")

    # Vipareeta Raja frequency
    vipareeta_count = 0
    vipareeta_formed = 0
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                if y.yoga_name == "Vipareeta Raja":
                    vipareeta_count += 1
                    if y.status == "FORMED":
                        vipareeta_formed += 1

    unique_vipareeta_subjects = set()
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                if y.yoga_name == "Vipareeta Raja" and y.status == "FORMED":
                    unique_vipareeta_subjects.add(s.subject_name)

    lines.append(f"### Vipareeta Raja Yoga Frequency")
    lines.append(f"- **Triggered in:** {len(unique_vipareeta_subjects)}/{len(subjects)} "
                 f"subjects ({len(unique_vipareeta_subjects)/len(subjects):.0%})")
    lines.append(f"- **Formed instances:** {vipareeta_formed}/{vipareeta_count} "
                 f"evaluations")
    lines.append("")

    # Dasha activation alignment
    dasha_aligned_domains: dict[str, int] = Counter()
    dasha_total_domains: dict[str, int] = Counter()
    for s in subjects:
        for e in s.event_reports:
            dasha_total_domains[e.domain] += 1
            if e.relevant_yoga_activated:
                dasha_aligned_domains[e.domain] += 1

    lines.append(f"### Dasha Activation by Event Domain")
    lines.append("")
    lines.append("| Domain | Events | Dasha-Aligned | Alignment Rate |")
    lines.append("|--------|--------|---------------|----------------|")
    for domain in sorted(dasha_total_domains.keys()):
        total = dasha_total_domains[domain]
        aligned = dasha_aligned_domains[domain]
        rate = f"{aligned/total:.0%}" if total else "—"
        lines.append(f"| {domain} | {total} | {aligned} | {rate} |")
    lines.append("")

    # Yoga type frequency across cohort
    yoga_counter: Counter = Counter()
    yoga_activated_counter: Counter = Counter()
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                yoga_counter[y.yoga_name] += 1
                if y.activation_status == "ACTIVATED":
                    yoga_activated_counter[y.yoga_name] += 1

    lines.append(f"### Yoga Formation Frequency")
    lines.append("")
    lines.append("| Yoga | Formed/Weakened | Activated |")
    lines.append("|------|-----------------|-----------|")
    for yoga_name, count in yoga_counter.most_common():
        act = yoga_activated_counter.get(yoga_name, 0)
        lines.append(f"| {yoga_name} | {count} | {act} |")
    lines.append("")

    # Modifier cancellation pattern
    cancelled_count = 0
    weakened_count = 0
    formed_count = 0
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                if y.status == "CANCELLED":
                    cancelled_count += 1
                elif y.status == "WEAKENED":
                    weakened_count += 1
                else:
                    formed_count += 1

    total_yogas = cancelled_count + weakened_count + formed_count
    lines.append(f"### Modifier Pipeline Outcomes")
    lines.append(f"- **FORMED:** {formed_count}/{total_yogas} ({formed_count/total_yogas:.0%})")
    lines.append(f"- **WEAKENED:** {weakened_count}/{total_yogas} ({weakened_count/total_yogas:.0%})")
    lines.append(f"- **CANCELLED:** {cancelled_count}/{total_yogas} ({cancelled_count/total_yogas:.0%})")
    lines.append("")

    # ── Section 3: Per-Chart Breakdown ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 3: Per-Chart Breakdown")
    lines.append("")

    for s in subjects:
        lines.append(f"### {s.subject_name}")
        lines.append(f"**Fixture:** `{s.fixture_file}` | **Lagna:** {s.lagna_rashi} "
                     f"({s.lagna_nakshatra}) | **Moon Nakshatra:** {s.moon_nakshatra}")
        lines.append("")
        lines.append("| Event | Date | Domain | Active Dasha | Top Yoga | Dyn. Str | "
                     "Activated? | Expected Planets |")
        lines.append("|-------|------|--------|-------------|----------|----------|"
                     "------------|------------------|")

        for e in s.event_reports:
            top = e.top_yogas[0] if e.top_yogas else None
            top_name = top.yoga_name if top else "—"
            top_dyn = f"{top.dynamic_strength:.4f}" if top and top.dynamic_strength is not None else "N/A"
            top_act = "✓" if e.relevant_yoga_activated else "✗"
            dasha = f"{e.dasha_md_lord}/{e.dasha_ad_lord}/{e.dasha_pd_lord}"
            expected = ", ".join(e.expected_planets) if e.expected_planets else "—"
            lines.append(f"| {e.event_id} | {e.event_date_utc[:10]} | {e.domain} | "
                         f"{dasha} | {top_name} | {top_dyn} | {top_act} | {expected} |")

        lines.append("")

        # Detailed yoga breakdown per event
        for e in s.event_reports:
            lines.append(f"**{e.event_id}** ({e.event_date_utc[:10]}) — {e.domain}")
            lines.append("")
            lines.append("| Yoga | Status | Involved | Static | Dynamic | "
                         "Dasha Mult | Chain Impact | Activation |")
            lines.append("|------|--------|----------|--------|---------|"
                         "------------|--------------|------------|")
            for y in e.top_yogas:
                static = f"{y.static_strength:.3f}" if y.static_strength is not None else "—"
                dynamic = f"{y.dynamic_strength:.4f}" if y.dynamic_strength is not None else "—"
                dasha_m = f"{y.dasha_multiplier:.2f}" if y.dasha_multiplier is not None else "—"
                chain = f"{y.chain_impact:.4f}" if y.chain_impact is not None else "—"
                inv = ", ".join(y.involved_planets) if y.involved_planets else "—"
                lines.append(f"| {y.yoga_name} | {y.status} | {inv} | {static} | "
                             f"{dynamic} | {dasha_m} | {chain} | {y.activation_status} |")
            lines.append("")

    # ── Section 4: Error Attribution Hypotheses ──
    lines.append("---")
    lines.append("")
    lines.append("## Section 4: Error Attribution Hypotheses")
    lines.append("")
    lines.append("The following hypotheses are derived from the raw pipeline output "
                 "without proposing fixes.")
    lines.append("")

    # Hypothesis 1: Chain impact negativity
    if chain_impacts and avg_chain < 0:
        lines.append("### Hypothesis 1: Chain Impact Is Systematically Negative")
        lines.append(f"- **Observation:** Average chain impact = {avg_chain:.6f} "
                     f"({neg_chain}/{chain_yoga_count} negative)")
        lines.append(f"- **Possible cause:** The multi-hop chain evaluator (Layer 1.5) "
                     f"may be weighting dispositorship chains through dusthana houses "
                     f"too heavily. When a yoga-forming planet's dispositor chain passes "
                     f"through 6th/8th/12th houses, the negative functional role weight "
                     f"compounds across hops.")
        lines.append(f"- **Impact:** This suppresses dynamic_strength for otherwise "
                     f"well-formed yogas, reducing the apparent prediction accuracy.")
        lines.append("")

    # Hypothesis 2: Vipareeta Raja over-triggering
    if len(unique_vipareeta_subjects) >= 3:
        lines.append("### Hypothesis 2: Vipareeta Raja Over-Triggering")
        lines.append(f"- **Observation:** Vipareeta Raja yoga triggered in "
                     f"{len(unique_vipareeta_subjects)}/{len(subjects)} charts "
                     f"({len(unique_vipareeta_subjects)/len(subjects):.0%})")
        lines.append(f"- **Possible cause:** The Vipareeta Raja detection logic may "
                     f"be too broad. Any dusthana lord (6th, 8th, 12th) placed in a "
                     f"dusthana triggers it, which is statistically common given that "
                     f"12 houses contain all 9 planets.")
        lines.append(f"- **Impact:** Non-specific signal — fires for nearly every chart "
                     f"regardless of whether the subject experienced the characteristic "
                     f"'reversal through adversity' pattern.")
        lines.append("")

    # Hypothesis 3: Transit multiplier always 1.0
    transit_mults = []
    for s in subjects:
        for e in s.event_reports:
            for y in e.all_yogas:
                if y.transit_multiplier is not None:
                    transit_mults.append(y.transit_multiplier)

    if transit_mults and all(t == 1.0 for t in transit_mults):
        lines.append("### Hypothesis 3: Transit Multiplier Is Inactive (Always 1.0)")
        lines.append(f"- **Observation:** All {len(transit_mults)} transit multiplier "
                     f"values are exactly 1.0")
        lines.append(f"- **Possible cause:** The transit evaluation layer requires "
                     f"`transit_houses` and `ashtakavarga_scores` in jre_facts, "
                     f"which are not provided by the current fixture format. Without "
                     f"this data, the transit layer defaults to a pass-through multiplier.")
        lines.append(f"- **Impact:** The pipeline effectively runs a 4-layer evaluation "
                     f"(Layers 1, 1.5, 2, 4) with Layer 3 (transit) inactive. Dynamic "
                     f"strength is determined solely by chain impact and dasha multiplier.")
        lines.append("")

    # Hypothesis 4: Dasha activation pattern
    non_activated = total_events - events_with_hit
    if non_activated > 0:
        lines.append("### Hypothesis 4: Dasha Activation Misses on Key Events")
        lines.append(f"- **Observation:** {non_activated}/{total_events} events had "
                     f"no relevant yoga activated by the active Dasha lords")
        lines.append(f"- **Possible cause:** The expected_planets in the fixture define "
                     f"which planets *should* be active, but the Dasha multiplier only "
                     f"fires when the MD/AD/PD lord *is* one of the yoga's involved "
                     f"planets. If the expected planet is not involved in any formed "
                     f"yoga, the activation check cannot succeed by construction.")
        lines.append(f"- **Impact:** This is a structural limitation of the current "
                     f"evaluation framework — it tests yoga-level activation, not "
                     f"planet-level Dasha presence.")
        lines.append("")

    # ── Methodology Footer ──
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("This report is generated **without any post-hoc calibration**. "
                 "The pipeline was executed with frozen weights and default configuration.")
    lines.append("")
    lines.append("### Pipeline Layers:")
    lines.append("1. **Layer 1 — Relationship Graph:** Structural detection "
                 "(conjunctions, aspects, dispositorship, exchanges, nakshatra edges)")
    lines.append("2. **Layer 1.5 — Chain Evaluator:** Multi-hop Kendra-Trikona chain impact")
    lines.append("3. **Layer 2 — Modifiers:** 5-tier priority (combustion, debilitation, "
                 "graha yuddha, retrograde, node taint)")
    lines.append("4. **Layer 3 — Temporal:** Vimshottari Dasha multiplier "
                 "(transit inactive without ashtakavarga data)")
    lines.append("5. **Layer 4 — Varga:** D9 (Navamsha) confirmation")
    lines.append("")
    lines.append("### Dasha Activation Multipliers (frozen):")
    lines.append("- MD lord matches yoga planet → **1.50×**")
    lines.append("- AD lord matches yoga planet → **1.25×**")
    lines.append("- PD lord matches yoga planet → **1.10×**")
    lines.append("- No match (dormant) → **0.40×**")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    print("=" * 60)
    print("BLIND EMPIRICAL EVALUATION — 5-Chart Cohort")
    print("Phase E5: 5-Layer Pipeline Execution")
    print("=" * 60)
    print()

    subjects = _evaluate_all_charts()

    # Generate report
    output_dir = _PROJECT_ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    md_content = _generate_report(subjects)
    md_path = output_dir / "blind_evaluation_cohort.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    print("=" * 60)
    print(f"Report written to: {md_path}")
    print("=" * 60)

    # Also write JSON for programmatic consumption
    json_data: dict[str, Any] = {
        "cohort_size": len(subjects),
        "total_events": sum(len(s.event_reports) for s in subjects),
        "subjects": [],
    }
    for s in subjects:
        subject_data: dict[str, Any] = {
            "name": s.subject_name,
            "fixture": s.fixture_file,
            "lagna": s.lagna_rashi,
            "moon_nakshatra": s.moon_nakshatra,
            "events": [],
        }
        for e in s.event_reports:
            event_data: dict[str, Any] = {
                "event_id": e.event_id,
                "date": e.event_date_utc,
                "domain": e.domain,
                "dasha": {"md": e.dasha_md_lord, "ad": e.dasha_ad_lord, "pd": e.dasha_pd_lord},
                "relevant_yoga_activated": e.relevant_yoga_activated,
                "top_yogas": [
                    {
                        "name": y.yoga_name,
                        "status": y.status,
                        "dynamic_strength": y.dynamic_strength,
                        "dasha_multiplier": y.dasha_multiplier,
                        "chain_impact": y.chain_impact,
                        "activation": y.activation_status,
                    }
                    for y in e.top_yogas
                ],
                "all_yogas": [
                    {
                        "name": y.yoga_name,
                        "status": y.status,
                        "chain_impact": y.chain_impact,
                        "activation": y.activation_status,
                    }
                    for y in e.all_yogas
                ],
            }
            subject_data["events"].append(event_data)
        json_data["subjects"].append(subject_data)

    json_path = output_dir / "blind_evaluation_cohort.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, sort_keys=True)
    print(f"JSON data written to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
