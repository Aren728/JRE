#!/usr/bin/env python3
"""Blind Empirical Evaluation — Einstein Chart (Phase E3).

Loads the immutable Einstein fixture, passes canonical facts through the
complete 5-layer JRE pipeline, and generates a blind prediction report
for the 3 known life events.

NO changes to rules, weights, or engine logic.
NO calibration or tuning.
STRICTLY OBSERVE what the engine produces and record it.

Usage::

    python scripts/blind_evaluation_einstein.py
    python scripts/blind_evaluation_einstein.py --output reports/
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Path setup ──────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# ── Constants ───────────────────────────────────────────────────────────────

_RASHI_NUM: dict[str, int] = {
    "MESHA": 1, "VRISHABHA": 2, "MITHUNA": 3, "KARKA": 4,
    "SIMHA": 5, "KANYA": 6, "TULA": 7, "VRISHCHIKA": 8,
    "DHANUSHA": 9, "MAKARA": 10, "KUMBHA": 11, "MEENA": 12,
}

_RASHI_ORDER: list[str] = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]

# Sign ownership (1-indexed rashi number → planet)
_SIGN_LORDS: dict[int, str] = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

# Navamsha sign types
_SIGN_TYPES: dict[int, str] = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}

# ── D9 Helper ───────────────────────────────────────────────────────────────


def _compute_d9_sign(longitude_used: float) -> str:
    """Classical navamsha sign from a sidereal longitude."""
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
    else:  # water
        start = (sign_index + 8) % 12

    d9_index = (start + navamsha_within_sign) % 12
    return _RASHI_ORDER[d9_index]


def _compute_d9_house(
    longitude_used: float,
    d9_lagna_longitude: float,
) -> int:
    """Compute D9 house (1-12) from D1 longitude using Whole-Sign from D9 Lagna."""
    d9_sign = _compute_d9_sign(longitude_used)
    d9_lagna_sign = _compute_d9_sign(d9_lagna_longitude)
    d9_lagna_idx = _RASHI_ORDER.index(d9_lagna_sign)
    planet_idx = _RASHI_ORDER.index(d9_sign)
    return (planet_idx - d9_lagna_idx) % 12 + 1


# ── Data structures ─────────────────────────────────────────────────────────


@dataclass
class YogaReport:
    """A single yoga's evaluation result for the report."""
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
    outcome_domain: str = ""
    modifier_overall_strength: float | None = None
    modifier_status: str | None = None


@dataclass
class EventReport:
    """Complete evaluation report for a single known event."""
    event_id: str
    event_date_utc: str
    domain: str
    description: str
    dasha_md_lord: str = ""
    dasha_ad_lord: str = ""
    dasha_pd_lord: str = ""
    all_yogas: list[YogaReport] = field(default_factory=list)
    top_yogas: list[YogaReport] = field(default_factory=list)
    timing_overlap: dict[str, str] = field(default_factory=dict)


# ── JRE Facts Builder ──────────────────────────────────────────────────────


def _build_jre_facts(chart: Any, target_ts: datetime | None = None) -> dict[str, Any]:
    """Convert a JyotishService NatalChart into the jre_facts dict
    expected by YogaEvaluatorService.evaluate_classical_yogas().

    This is the canonical bridge between JRE-003 output and JRS-075+ input.
    """
    from jyotish.rashi import RASHI_ORDER as JYOTISH_RASHI_ORDER

    lagna_rashi = chart.lagna.rashi.value
    lagna_sign_num = _RASHI_NUM.get(lagna_rashi, 1)
    lagna_longitude = chart.lagna.ascendant_longitude_deg

    # Build house_lords: house_number -> planet_name
    # Whole-Sign: house 1 starts at the lagna rashi
    lagna_idx = list(JYOTISH_RASHI_ORDER).index(chart.lagna.rashi)
    house_lords: dict[int, str] = {}
    for i in range(12):
        house_num = i + 1
        rashi_idx = (lagna_idx + i) % 12
        rashi_name = list(JYOTISH_RASHI_ORDER)[rashi_idx]
        rashi_num = _RASHI_NUM.get(rashi_name, rashi_idx + 1)
        lord = _SIGN_LORDS.get(rashi_num, "")
        house_lords[house_num] = lord

    # Build planet data
    planets: dict[str, dict[str, Any]] = {}
    moon_nakshatra = ""
    moon_nakshatra_degree = 0.0

    for ps in chart.planet_states:
        pname = ps.body.value

        # Determine house number from whole-sign
        planet_rashi = ps.rashi.value
        planet_rashi_idx = list(JYOTISH_RASHI_ORDER).index(ps.rashi)
        house_num = (planet_rashi_idx - lagna_idx) % 12 + 1

        # Rashi number (1-indexed)
        rashi_num = _RASHI_NUM.get(planet_rashi, 0)

        # Determine combust (within ~8° of Sun, simplified)
        sun_state = next(
            (s for s in chart.planet_states if s.body.value == "SUN"), None
        )
        is_combust = False
        if sun_state and pname != "SUN":
            diff = abs(ps.longitude_used - sun_state.longitude_used)
            if diff > 180:
                diff = 360 - diff
            is_combust = diff < 8.0

        # Determine debilitated
        _DEBILITATION = {
            "SUN": 7, "MOON": 8, "MARS": 4, "MERCURY": 12,
            "JUPITER": 10, "VENUS": 6, "SATURN": 1,
        }
        is_debilitated = rashi_num == _DEBILITATION.get(pname, -1)

        # Sign lord
        sign_lord = _SIGN_LORDS.get(rashi_num, "")

        pdata: dict[str, Any] = {
            "house": house_num,
            "rashi": planet_rashi,
            "rashi_num": rashi_num,
            "combust": is_combust,
            "debilitated": is_debilitated,
            "retrograde": ps.retrograde.value == "RETROGRADE",
            "longitude": ps.longitude_used,
            "sign_lord": sign_lord,
        }
        planets[pname] = pdata

        # Track Moon's nakshatra for Dasha
        if pname == "MOON":
            moon_nakshatra = ps.nakshatra.value
            moon_nakshatra_degree = ps.longitude_used

    # D9 houses and signs
    planet_d9_house: dict[str, int] = {}
    planet_d9_sign: dict[str, str] = {}
    for ps in chart.planet_states:
        pname = ps.body.value
        d9_sign = _compute_d9_sign(ps.longitude_used)
        d9_house = _compute_d9_house(ps.longitude_used, lagna_longitude)
        planet_d9_house[pname] = d9_house
        planet_d9_sign[pname] = d9_sign

    # Moon natal house
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
    birth_dt: datetime | None = None,
) -> EventReport:
    """Run the full 5-layer pipeline for a single event timestamp.

    Returns an EventReport with per-yoga details.
    """
    from jrs.temporal.dasha_engine import VimshottariDashaEngine

    event_ts = datetime.fromisoformat(
        event["event_date_utc"].replace("Z", "+00:00")
    )

    # Build jre_facts at this target timestamp
    jre_facts = _build_jre_facts(chart, target_ts=event_ts)

    # ── Compute Dasha at event timestamp ──
    # Use the actual birth datetime to compute the Dasha epoch correctly.
    # The engine's compute_dasha_at back-calculates the birth epoch from the
    # target, so we pass the actual birth time to get a correct epoch.
    dasha_engine = VimshottariDashaEngine()
    moon_nak = jre_facts["moon_nakshatra"]
    moon_deg = jre_facts["moon_nakshatra_degree"]
    if birth_dt is not None:
        # Compute birth epoch from actual birth time
        hierarchy_at_birth = dasha_engine.compute_dasha_at(
            birth_dt, moon_nak, moon_deg,
        )
        # The birth epoch is the start of the first MD period
        birth_epoch = hierarchy_at_birth.mahadasha.start_utc
        # Now compute MD periods from the correct birth epoch
        md_periods = dasha_engine._compute_md_periods(birth_epoch)
        # Find the active MD at the event timestamp
        active_md = dasha_engine._find_active_period(md_periods, event_ts)
        if active_md is None:
            active_md = hierarchy_at_birth.mahadasha
        # Compute AD within active MD
        ad_periods = dasha_engine._compute_sub_periods(active_md, "AD")
        active_ad = dasha_engine._find_active_period(ad_periods, event_ts)
        if active_ad is None:
            active_ad = ad_periods[0]
        # Compute PD within active AD
        pd_periods = dasha_engine._compute_sub_periods(active_ad, "PD")
        active_pd = dasha_engine._find_active_period(pd_periods, event_ts)
        if active_pd is None:
            active_pd = pd_periods[0]
        from jrs.temporal.dasha_engine import DashaHierarchy
        hierarchy = DashaHierarchy(
            mahadasha=active_md,
            antardasha=active_ad,
            pratyantardasha=active_pd,
        )
    else:
        hierarchy = dasha_engine.compute_dasha_at(event_ts, moon_nak, moon_deg)

    # ── Evaluate each yoga with temporal activation ──
    from jrs.yoga_evaluator.service import YogaEvaluatorService
    evaluator = YogaEvaluatorService()

    yoga_reports: list[YogaReport] = []

    for yoga_eval in all_yogas:
        yoga_name = yoga_eval.yoga_name

        # Get involved planets from modifier report
        involved: list[str] = []
        if yoga_eval.modifier_report is not None:
            involved = [pr.planet for pr in yoga_eval.modifier_report.planet_results]

        # Compute dasha multiplier for this yoga
        dasha_mult_result = dasha_engine.get_dasha_multiplier(hierarchy, involved)

        # Determine activation: is the Dasha lord one of the yoga planets?
        activation_status = "DORMANT"
        activation_source = ""
        if dasha_mult_result.matched_level != "NONE":
            activation_status = "ACTIVATED"
            activation_source = (
                f"Dasha {dasha_mult_result.matched_level}: "
                f"{dasha_mult_result.matched_planet}"
            )

        # Build outcome domain
        outcome_domain = evaluator.map_outcome(yoga_name)

        # Static strength from modifier report
        static_strength = 1.0
        if yoga_eval.modifier_report is not None:
            static_strength = yoga_eval.modifier_report.overall_strength

        # Chain impact
        chain_impact = yoga_eval.chain_impact

        # Dynamic strength
        dynamic_strength = yoga_eval.dynamic_strength

        # Modifier info
        mod_status = None
        mod_strength = None
        if yoga_eval.modifier_report is not None:
            mod_status = yoga_eval.modifier_report.overall_status.value
            mod_strength = yoga_eval.modifier_report.overall_strength

        yr = YogaReport(
            yoga_name=yoga_name,
            status=yoga_eval.status.value,
            involved_planets=involved,
            static_strength=static_strength,
            dynamic_strength=dynamic_strength,                dasha_multiplier=dasha_mult_result.multiplier,
            transit_multiplier=yoga_eval.transit_multiplier,
            chain_impact=chain_impact,
            activation_status=activation_status,
            activation_source=activation_source,
            cancellation_reason=yoga_eval.cancellation_reason,
            outcome_domain=outcome_domain,
            modifier_overall_strength=mod_strength,
            modifier_status=mod_status,
        )
        yoga_reports.append(yr)

    # Sort by dynamic_strength (descending), None treated as 0
    yoga_reports_sorted = sorted(
        yoga_reports,
        key=lambda y: y.dynamic_strength if y.dynamic_strength is not None else 0.0,
        reverse=True,
    )

    # Timing overlap: check if active dasha overlaps event window
    timing_overlap: dict[str, str] = {}
    event_start = event["event_date_utc"]
    for yr in yoga_reports_sorted:
        if yr.activation_status == "ACTIVATED":
            timing_overlap[yr.yoga_name] = (
                f"MD={hierarchy.md_lord}, AD={hierarchy.ad_lord}, "
                f"PD={hierarchy.pd_lord} → Dasha lord "
                f"{dasha_mult_result.matched_planet} matches yoga planet"
            )
        else:
            timing_overlap[yr.yoga_name] = (
                f"MD={hierarchy.md_lord}, AD={hierarchy.ad_lord}, "
                f"PD={hierarchy.pd_lord} → No yoga planet in active Dasha"
            )

    return EventReport(
        event_id=event["event_id"],
        event_date_utc=event["event_date_utc"],
        domain=event["domain"],
        description=event["description"],
        dasha_md_lord=hierarchy.md_lord,
        dasha_ad_lord=hierarchy.ad_lord,
        dasha_pd_lord=hierarchy.pd_lord,
        all_yogas=yoga_reports,
        top_yogas=yoga_reports_sorted[:10],
        timing_overlap=timing_overlap,
    )


# ── Report Generator ────────────────────────────────────────────────────────


def _generate_markdown(
    fixture: dict[str, Any],
    event_reports: list[EventReport],
) -> str:
    """Generate the blind evaluation markdown report."""
    lines: list[str] = []

    lines.append("# Blind Empirical Evaluation — Albert Einstein")
    lines.append("")
    lines.append("**Phase E3: Blind Prediction Report**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Subject Info ──
    lines.append("## Subject")
    lines.append("")
    raw = fixture["raw_birth_data"]
    lines.append(f"- **Name:** Albert Einstein")
    lines.append(f"- **Birth Date:** {raw['date']}")
    lines.append(f"- **Birth Time:** {raw['time']} ({raw['timezone']})")
    lines.append(f"- **Location:** {raw['latitude']}°N, {raw['longitude']}°E")
    lines.append(f"- **Rodden Rating:** AA (birth certificate)")
    lines.append("")

    # ── Pipeline Config ──
    meta = fixture["_meta"]["pipeline_config"]
    lines.append("## Pipeline Configuration")
    lines.append("")
    lines.append(f"- **Zodiac Mode:** {meta['zodiac_mode']}")
    lines.append(f"- **Ayanamsa:** {meta['ayanamsa']}")
    lines.append(f"- **House System:** {meta['house_system']}")
    lines.append(f"- **Node Model:** {meta['node_model']}")
    lines.append(f"- **Ephemeris:** Swiss Ephemeris v{meta['ephemeris_provider']}")
    lines.append("")

    # ── Chart Summary ──
    lagna = fixture["expected_canonical_facts"]["lagna"]
    lines.append("## Natal Chart Summary")
    lines.append("")
    lines.append(f"- **Lagna:** {lagna['rashi']} (Ascendant {lagna['ascendant_longitude_deg']:.4f}°)")
    lines.append(f"- **Lagna Nakshatra:** {lagna['nakshatra']} (Lord: {lagna['nakshatra_lord']}, Pada {lagna['pada']})")
    lines.append("")

    planets = fixture["expected_canonical_facts"]["planets"]
    lines.append("| Planet | Rashi | Longitude | Nakshatra | Pada | Retrograde | D9 Sign |")
    lines.append("|--------|-------|-----------|-----------|------|------------|---------|")
    for pname, pdata in planets.items():
        lines.append(
            f"| {pname} | {pdata['rashi']} | {pdata['longitude_used']:.4f}° | "
            f"{pdata['nakshatra']} | {pdata['pada']} | {pdata['retrograde']} | "
            f"{pdata['d9_sign']} |"
        )
    lines.append("")

    # ── Event Evaluations ──
    for er in event_reports:
        lines.append("---")
        lines.append("")
        lines.append(f"## Event: {er.event_id}")
        lines.append("")
        lines.append(f"- **Date:** {er.event_date_utc}")
        lines.append(f"- **Domain:** {er.domain}")
        lines.append(f"- **Description:** {er.description}")
        lines.append("")

        # Dasha
        lines.append("### Active Dasha at Event Time")
        lines.append("")
        lines.append(f"- **Mahadasha (MD):** {er.dasha_md_lord}")
        lines.append(f"- **Antardasha (AD):** {er.dasha_ad_lord}")
        lines.append(f"- **Pratyantardasha (PD):** {er.dasha_pd_lord}")
        lines.append("")

        # Top 10 Yogas
        lines.append("### Top 10 Yogas by Dynamic Strength")
        lines.append("")
        lines.append("| # | Yoga | Status | Static | Dynamic | Dasha Mult | Activation | Outcome |")
        lines.append("|---|------|--------|--------|---------|------------|------------|---------|")
        for i, yr in enumerate(er.top_yogas, 1):
            static = f"{yr.static_strength:.3f}" if yr.static_strength is not None else "—"
            dynamic = f"{yr.dynamic_strength:.3f}" if yr.dynamic_strength is not None else "—"
            dasha_m = f"{yr.dasha_multiplier:.2f}" if yr.dasha_multiplier is not None else "—"
            lines.append(
                f"| {i} | {yr.yoga_name} | {yr.status} | {static} | "
                f"{dynamic} | {dasha_m} | {yr.activation_status} | "
                f"{yr.outcome_domain} |"
            )
        lines.append("")

        # Detailed yoga breakdown
        lines.append("### Detailed Yoga Analysis")
        lines.append("")
        for yr in er.all_yogas:
            lines.append(f"#### {yr.yoga_name}")
            lines.append("")
            lines.append(f"- **Status:** {yr.status}")
            lines.append(f"- **Involved Planets:** {', '.join(yr.involved_planets) if yr.involved_planets else '—'}")
            if yr.cancellation_reason:
                lines.append(f"- **Cancellation Reason:** {yr.cancellation_reason}")
            lines.append(f"- **Static Strength:** {yr.static_strength:.4f}" if yr.static_strength is not None else "- **Static Strength:** —")
            lines.append(f"- **Dynamic Strength:** {yr.dynamic_strength:.6f}" if yr.dynamic_strength is not None else "- **Dynamic Strength:** —")
            if yr.chain_impact is not None:
                lines.append(f"- **Chain Impact (Layer 1.5):** {yr.chain_impact:.6f}")
            if yr.dasha_multiplier is not None:
                lines.append(f"- **Dasha Multiplier:** {yr.dasha_multiplier:.2f}")
            if yr.transit_multiplier is not None:
                lines.append(f"- **Transit Multiplier:** {yr.transit_multiplier:.2f}")
            lines.append(f"- **Activation:** {yr.activation_status}")
            if yr.activation_source:
                lines.append(f"- **Activation Source:** {yr.activation_source}")
            if yr.modifier_status:
                lines.append(f"- **Modifier Status:** {yr.modifier_status} (strength={yr.modifier_overall_strength:.4f})" if yr.modifier_overall_strength is not None else f"- **Modifier Status:** {yr.modifier_status}")
            lines.append(f"- **Outcome Domain:** {yr.outcome_domain}")
            lines.append("")

        # Timing overlap
        lines.append("### Timing Overlap Analysis")
        lines.append("")
        for yog, overlap_info in er.timing_overlap.items():
            lines.append(f"- **{yog}:** {overlap_info}")
        lines.append("")

    # ── Cross-Event Summary ──
    lines.append("---")
    lines.append("")
    lines.append("## Cross-Event Summary")
    lines.append("")
    lines.append("| Event | Date | Dasha MD/AD/PD | Top Yoga | Dynamic | Activated? |")
    lines.append("|-------|------|----------------|----------|---------|------------|")
    for er in event_reports:
        top = er.top_yogas[0] if er.top_yogas else None
        top_name = top.yoga_name if top else "—"
        top_dyn = f"{top.dynamic_strength:.4f}" if top and top.dynamic_strength is not None else "—"
        top_act = top.activation_status if top else "—"
        dasha = f"{er.dasha_md_lord}/{er.dasha_ad_lord}/{er.dasha_pd_lord}"
        lines.append(
            f"| {er.event_id} | {er.event_date_utc[:10]} | {dasha} | "
            f"{top_name} | {top_dyn} | {top_act} |"
        )
    lines.append("")

    # ── Methodology Note ──
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("This report is generated **without any post-hoc calibration**.")
    lines.append("The pipeline was executed with frozen weights and default configuration.")
    lines.append("All yogas detected, their formation status, strength scores, and")
    lines.append("temporal activation are exactly as produced by the engine.")
    lines.append("")
    lines.append("### Pipeline Layers Executed:")
    lines.append("1. **Layer 1 — Relationship Graph:** Structural detection (conjunctions,")
    lines.append("   aspects, dispositorship, exchanges, nakshatra edges)")
    lines.append("2. **Layer 1.5 — Chain Evaluator:** Multi-hop Kendra-Trikona chain impact")
    lines.append("3. **Layer 2 — Modifiers:** 5-tier priority (combustion, debilitation,")
    lines.append("   graha yuddha, retrograde, node taint)")
    lines.append("4. **Layer 3 — Temporal:** Vimshottari Dasha + Transit multipliers")
    lines.append("5. **Layer 4 — Varga:** D9 (Navamsha) confirmation + Saptavargaja Bala")
    lines.append("")
    lines.append("### Dasha Activation Multipliers (frozen):")
    lines.append("- MD lord matches yoga planet → **1.50×**")
    lines.append("- AD lord matches yoga planet → **1.25×**")
    lines.append("- PD lord matches yoga planet → **1.10×**")
    lines.append("- No match (dormant) → **0.40×**")
    lines.append("")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    """Run the blind evaluation and generate the report."""
    fixture_path = (
        _PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "validation_charts"
        / "chart_001_pilot.json"
    )

    if not fixture_path.exists():
        print(f"ERROR: Fixture not found at {fixture_path}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("BLIND EMPIRICAL EVALUATION — Einstein Chart")
    print("Phase E3: 5-Layer Pipeline Execution")
    print("=" * 60)
    print()

    # Load fixture
    with fixture_path.open(encoding="utf-8") as f:
        fixture = json.load(f)
    print(f"Loaded fixture: {fixture_path.name}")
    print(f"Subject: {_PROJECT_ROOT / 'tests' / 'fixtures'}")
    print()

    # Compute natal chart
    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    raw = fixture["raw_birth_data"]
    birth = BirthData(
        date=raw["date"],
        time=raw["time"],
        timezone=raw["timezone"],
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
    )

    print("Computing natal chart via JyotishService (Swiss Ephemeris)...")
    svc = JyotishService()
    chart = svc.chart(birth)
    print(f"  Lagna: {chart.lagna.rashi.value} ({chart.lagna.ascendant_longitude_deg:.4f}°)")
    print(f"  Planets: {len(chart.planet_states)} computed")
    print()

    # Build jre_facts and detect all yogas (run once at natal level)
    print("Building jre_facts and detecting classical yogas...")
    jre_facts_natal = _build_jre_facts(chart)

    from jrs.yoga_evaluator.service import YogaEvaluatorService
    evaluator = YogaEvaluatorService()
    all_yogas = evaluator.evaluate_classical_yogas(jre_facts_natal)
    print(f"  Detected {len(all_yogas)} yoga formations:")
    for y in all_yogas:
        inv = []
        if y.modifier_report is not None:
            inv = [pr.planet for pr in y.modifier_report.planet_results]
        print(f"    - {y.yoga_name}: {y.status.value} (planets: {', '.join(inv) if inv else '—'})")
    print()

    # Compute birth datetime for Dasha epoch
    from datetime import timezone as _tz
    birth_dt = datetime.fromisoformat(
        f"{raw['date']}T{raw['time']}",
    ).replace(tzinfo=_tz.utc)  # Approximate UTC from local time
    # For precise UTC, use the chart's UTC timestamp
    if chart.planet_states:
        utc_str = chart.planet_states[0].timestamp_utc_iso
        birth_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    print(f"Birth UTC for Dasha: {birth_dt.isoformat()}")
    print()

    # Run pipeline for each event
    events = fixture["known_events"]
    event_reports: list[EventReport] = []

    for event in events:
        print(f"{'─' * 60}")
        print(f"Evaluating: {event['event_id']}")
        print(f"  Date: {event['event_date_utc']}")
        print(f"  Domain: {event['domain']}")
        print(f"  {event['description']}")
        print()

        er = _run_pipeline_for_event(chart, event, all_yogas, birth_dt=birth_dt)
        event_reports.append(er)

        print(f"  Dasha: MD={er.dasha_md_lord}, AD={er.dasha_ad_lord}, PD={er.dasha_pd_lord}")
        print(f"  Active yogas: {sum(1 for y in er.all_yogas if y.activation_status == 'ACTIVATED')}")
        if er.top_yogas:
            top = er.top_yogas[0]
            dyn = f"{top.dynamic_strength:.4f}" if top.dynamic_strength is not None else "N/A"
            print(f"  Top yoga: {top.yoga_name} (dynamic={dyn}, {top.activation_status})")
        print()

    # Generate markdown report
    output_dir = _PROJECT_ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    md_content = _generate_markdown(fixture, event_reports)
    md_path = output_dir / "blind_evaluation_einstein.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    print("=" * 60)
    print(f"Report written to: {md_path}")
    print("=" * 60)

    # Also write JSON for programmatic consumption
    json_path = output_dir / "blind_evaluation_einstein.json"
    json_data = {
        "subject": "Albert Einstein",
        "fixture": str(fixture_path),
        "pipeline_config": fixture["_meta"]["pipeline_config"],
        "events": [],
    }
    for er in event_reports:
        json_data["events"].append({
            "event_id": er.event_id,
            "event_date_utc": er.event_date_utc,
            "domain": er.domain,
            "description": er.description,
            "dasha": {
                "md": er.dasha_md_lord,
                "ad": er.dasha_ad_lord,
                "pd": er.dasha_pd_lord,
            },
            "yogas": [
                {
                    "yoga_name": yr.yoga_name,
                    "status": yr.status,
                    "involved_planets": yr.involved_planets,
                    "static_strength": yr.static_strength,
                    "dynamic_strength": yr.dynamic_strength,
                    "dasha_multiplier": yr.dasha_multiplier,
                    "activation_status": yr.activation_status,
                    "activation_source": yr.activation_source,
                    "cancellation_reason": yr.cancellation_reason,
                    "outcome_domain": yr.outcome_domain,
                }
                for yr in er.all_yogas
            ],
        })

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, sort_keys=True)
    print(f"JSON data written to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
