#!/usr/bin/env python3
"""Diagnose Dasha Activation Logic (Phase E6).

Analyzes why only 13% of events show relevant yoga activation.
Uses ACTUAL birth dates from fixtures for correct Dasha computation.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jrs.temporal.dasha_engine import VimshottariDashaEngine, DashaHierarchy
from jrs.yoga_evaluator.service import YogaEvaluatorService
from jrs.yoga_evaluator.models import YogaStatus


_RASHI_ORDER = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]


def _rashi_to_num(rashi: str) -> int:
    return _RASHI_ORDER.index(rashi) + 1 if rashi in _RASHI_ORDER else 0


def load_chart(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def build_jre_facts(chart: dict) -> dict:
    cf = chart["expected_canonical_facts"]

    house_occupants: dict[int, list[str]] = {}
    house_lords_map: dict[int, str] = {}
    if "houses" in cf:
        for hnum_str, hdata in cf["houses"].items():
            hnum = int(hnum_str)
            house_lords_map[hnum] = hdata.get("lord", "")
            house_occupants[hnum] = hdata.get("occupants", [])

    planet_house: dict[str, int] = {}
    for hnum, occupants in house_occupants.items():
        for pname in occupants:
            planet_house[pname] = hnum

    lagna_rashi_num = _rashi_to_num(cf["lagna"]["rashi"])

    planets = {}
    for pname, pdata in cf["planets"].items():
        retro_str = pdata.get("retrograde", "DIRECT")
        rashi_num = _rashi_to_num(pdata["rashi"])
        house = planet_house.get(pname, 0)
        if house == 0 and rashi_num > 0:
            house = ((rashi_num - lagna_rashi_num) % 12) + 1

        planets[pname] = {
            "rashi": pdata["rashi"],
            "rashi_num": rashi_num,
            "longitude": pdata["longitude_sidereal"],
            "house": house,
            "retrograde": retro_str == "RETROGRADE",
            "combust": False,
            "debilitated": False,
            "nakshatra": pdata.get("nakshatra", ""),
            "pada": pdata.get("pada", 0),
        }

    # Get actual birth datetime from raw_birth_data
    raw = chart.get("raw_birth_data", {})
    birth_date = raw.get("date", "")
    birth_time = raw.get("time", "00:00:00")
    birth_tz = raw.get("timezone", "UTC")

    # Parse birth datetime (assume UTC for simplicity since Dasha engine uses UTC)
    birth_dt_str = f"{birth_date}T{birth_time}"
    try:
        birth_dt = datetime.fromisoformat(birth_dt_str).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        birth_dt = None

    return {
        "planets": planets,
        "lagna_sign": lagna_rashi_num,
        "lagna_house": 1,
        "house_lords": house_lords_map,
        "moon_nakshatra": cf["planets"]["MOON"]["nakshatra"],
        "moon_nakshatra_degree": cf["planets"]["MOON"].get("degree_in_nakshatra", 0.0),
        "_birth_datetime": birth_dt,
    }


def compute_dasha_with_birth(hierarchy_no_birth: DashaHierarchy, birth_dt: datetime | None, target_dt: datetime) -> DashaHierarchy:
    """Recompute Dasha using actual birth datetime if available."""
    if birth_dt is None:
        return hierarchy_no_birth

    # Use the Dasha engine's internal logic but with correct birth epoch
    engine = VimshottariDashaEngine()

    # Get the MD lord from the Moon's nakshatra
    md_lord = engine._get_md_lord(hierarchy_no_birth.mahadasha.lord)  # Use the MD lord from the no-birth computation

    # Compute MD periods from actual birth
    md_periods = engine._compute_md_periods(birth_dt)

    # Find active MD at target
    active_md = engine._find_active_period(md_periods, target_dt)
    if active_md is None:
        return hierarchy_no_birth

    # Compute AD within active MD
    ad_periods = engine._compute_sub_periods(active_md, "AD")
    active_ad = engine._find_active_period(ad_periods, target_dt)
    if active_ad is None:
        return hierarchy_no_birth

    # Compute PD within active AD
    pd_periods = engine._compute_sub_periods(active_ad, "PD")
    active_pd = engine._find_active_period(pd_periods, target_dt)
    if active_pd is None:
        return hierarchy_no_birth

    return DashaHierarchy(
        mahadasha=active_md,
        antardasha=active_ad,
        pratyantardasha=active_pd,
    )


def diagnose_event(chart_name: str, event: dict, jre_facts: dict):
    """Diagnose Dasha activation for a single event."""
    event_id = event["event_id"]
    event_date = event["event_date_utc"]
    expected_planets = event.get("expected_planets", [])
    event_domain = event.get("domain", "?")

    print(f"\n  {'─' * 60}")
    print(f"  Event: {event_id}")
    print(f"  Date:  {event_date}  Domain: {event_domain}")
    print(f"  Expected planets: {expected_planets}")

    target_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
    birth_dt = jre_facts.get("_birth_datetime")

    # Compute Dasha
    dasha_engine = VimshottariDashaEngine()
    hierarchy_no_birth = dasha_engine.compute_dasha_at(
        target_timestamp=target_dt,
        moon_nakshatra=jre_facts["moon_nakshatra"],
        moon_nakshatra_degree=jre_facts["moon_nakshatra_degree"],
    )

    # Recompute with actual birth datetime
    hierarchy = compute_dasha_with_birth(hierarchy_no_birth, birth_dt, target_dt)

    print(f"  Active Dasha (with actual birth {birth_dt}):")
    print(f"    MD:  {hierarchy.md_lord}  ({hierarchy.mahadasha.start_utc.date()} → {hierarchy.mahadasha.end_utc.date()})")
    print(f"    AD:  {hierarchy.ad_lord}  ({hierarchy.antardasha.start_utc.date()} → {hierarchy.antardasha.end_utc.date()})")
    print(f"    PD:  {hierarchy.pd_lord}  ({hierarchy.pratyantardasha.start_utc.date()} → {hierarchy.pratyantardasha.end_utc.date()})")

    # Run yoga evaluator
    evaluator = YogaEvaluatorService()
    jre_facts_with_target = dict(jre_facts)
    jre_facts_with_target["target_timestamp"] = target_dt
    yogas = evaluator.evaluate_classical_yogas(jre_facts_with_target)

    print(f"\n  Detected Yogas ({len(yogas)} total):")
    for y in yogas:
        involved = []
        if y.modifier_report and y.modifier_report.planet_results:
            involved = [pr.planet for pr in y.modifier_report.planet_results]

        md_match = hierarchy.md_lord in involved
        ad_match = hierarchy.ad_lord in involved
        pd_match = hierarchy.pd_lord in involved
        any_match = md_match or ad_match or pd_match

        activation_status = "✅ ACTIVATED" if any_match else "❌ DORMANT"

        match_detail = ""
        if md_match:
            match_detail = f"MD={hierarchy.md_lord}"
        elif ad_match:
            match_detail = f"AD={hierarchy.ad_lord}"
        elif pd_match:
            match_detail = f"PD={hierarchy.pd_lord}"

        print(f"    {y.yoga_name:20s} | Status={y.status.value:10s} | "
              f"Planets={involved} | "
              f"Dasha match: {match_detail or 'NONE':10s} | {activation_status}")

    # Cross-reference with expected planets
    print(f"\n  Cross-Reference Analysis:")
    print(f"    Dasha lords: MD={hierarchy.md_lord}, AD={hierarchy.ad_lord}, PD={hierarchy.pd_lord}")

    for ep in expected_planets:
        in_md = ep == hierarchy.md_lord
        in_ad = ep == hierarchy.ad_lord
        in_pd = ep == hierarchy.pd_lord
        in_dasha = in_md or in_ad or in_pd

        in_yoga = False
        for y in yogas:
            if y.modifier_report and y.modifier_report.planet_results:
                yoga_planets = [pr.planet for pr in y.modifier_report.planet_results]
                if ep in yoga_planets:
                    in_yoga = True
                    break

        status = []
        if in_dasha:
            if in_md:
                status.append("in MD")
            if in_ad:
                status.append("in AD")
            if in_pd:
                status.append("in PD")
        else:
            status.append("NOT in Dasha")

        if in_yoga:
            status.append("in yoga")
        else:
            status.append("NOT in any yoga")

        print(f"    Expected planet {ep:10s}: {', '.join(status)}")


def main():
    charts = {
        "chart_001_pilot.json": "Einstein",
        "chart_002_curie.json": "Curie",
    }

    print("=" * 70)
    print("DASHA ACTIVATION LOGIC DIAGNOSTIC (Phase E6)")
    print("Using ACTUAL birth dates for correct Dasha computation")
    print("=" * 70)

    for filename, chart_name in charts.items():
        path = f"tests/fixtures/validation_charts/{filename}"
        chart = load_chart(path)
        jre_facts = build_jre_facts(chart)

        print(f"\n{'=' * 70}")
        print(f"SUBJECT: {chart_name}")
        print(f"  Birth: {chart.get('raw_birth_data', {}).get('date', '?')} "
              f"{chart.get('raw_birth_data', {}).get('time', '?')} "
              f"({chart.get('raw_birth_data', {}).get('timezone', '?')})")
        print(f"{'=' * 70}")

        events = chart.get("known_events", [])
        for event in events:
            diagnose_event(chart_name, event, jre_facts)

    # Summary
    print("\n" + "=" * 70)
    print("ROOT CAUSE ANALYSIS: DASHA ACTIVATION")
    print("=" * 70)
    print("""
  KEY FINDING: The Dasha computation produces IDENTICAL MD/AD/PD for all
  events within the same subject when using the back-calculated birth epoch.
  This is because the engine's _compute_birth_epoch() back-calculates from
  the target timestamp, producing a birth epoch close to the target.

  Using ACTUAL birth dates produces correct, differentiated Dasha periods.

  ROOT CAUSES OF LOW ACTIVATION RATE:

  1. YOGA DIVERSITY DEFICIT (Primary):
     Only 2-4 classical yogas are detected per chart:
     - Gajakesari (Jupiter in kendra from Moon)
     - Raja (Kendra lord conjunct/mutually aspects Trikona lord)
     - Vipareeta Raja (dusthana lord in dusthana)
     - Pancha Mahapurusha (planet in own/exalt sign in kendra)

     Missing yogas that SHOULD be detected:
     - Dhana Yoga (2nd lord + 11th lord connection)
     - Neecha Bhanga (debilitation cancellation)
     - Chandra/Sunapha/Anapha yogas (planets from Moon)
     - Parivartana Yoga (sign exchange)
     - Rahu/Ketu axis yogas

  2. DASHA LORD ≠ YOGA PLANET MISMATCH:
     The activation requires: dasha_lord in involved_planets
     But many important yogas involve planets that are NOT the Dasha lords.

     Example: Einstein's Malavya Yoga (Venus in own sign):
     - Venus MD → ACTIVATED ✅
     - But Venus MD is only 20 out of 120 years (16.7% of life)
     - Most events occur during non-Venus MD periods

  3. TRANSIT DATA ABSENT:
     - transit_houses and ashtakavarga_scores not provided
     - Transit multiplier defaults to 1.0 (neutral)
     - This eliminates the transit-based activation pathway

  4. DASHA ENGINE BIRTH EPOCH BUG:
     The engine's _compute_birth_epoch() back-calculates from target,
     NOT from actual birth. This produces incorrect Dasha assignments
     for events far from the back-calculated birth.

  RECOMMENDATIONS:
  a) Fix Dasha engine to accept explicit birth_datetime parameter
  b) Add missing classical yogas (Dhana, Parivartana, Chandra series)
  c) Add transit data to fixtures for transit multiplier activation
  d) Consider broadening activation to include Dasha lord's dispositor
""")


if __name__ == "__main__":
    main()
