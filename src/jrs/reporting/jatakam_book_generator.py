"""JRE Reporting — Master Jatakam Book Generator.

Compiles enriched facts, extended metrics, and generated narratives into
a single, beautifully formatted, multi-page document following the exact
5-part Jatakam structure.

NO engine logic — pure document generation layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jrs.api.schemas import ENGINE_VERSION, LEGAL_DISCLAIMER, EvaluationResponse
from jrs.deterministic_engine.esoteric_evaluator import (
    evaluate_esoteric_profile,
    render_esoteric_profile_html,
)
from jrs.fact_engine.extended_metrics import ExtendedMetrics
from jrs.reporting.narrative_engines.bhava_engine import BhavaNarrativeEngine
from jrs.reporting.narrative_engines.timeline_engine import ChronologicalTimelineEngine

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════

_RASHI_NAMES: dict[str, str] = {
    "MESHA": "Aries (Mesha)",
    "VRISHABHA": "Taurus (Vrishabha)",
    "MITHUNA": "Gemini (Mithuna)",
    "KARKA": "Cancer (Karka)",
    "SIMHA": "Leo (Simha)",
    "KANYA": "Virgo (Kanya)",
    "TULA": "Libra (Tula)",
    "VRISHCHIKA": "Scorpio (Vrishchika)",
    "DHANUSHA": "Sagittarius (Dhanusha)",
    "MAKARA": "Capricorn (Makara)",
    "KUMBHA": "Aquarius (Kumbha)",
    "MEENA": "Pisces (Meena)",
}

_RASHI_ORDER = [
    "MESHA",
    "VRISHABHA",
    "MITHUNA",
    "KARKA",
    "SIMHA",
    "KANYA",
    "TULA",
    "VRISHCHIKA",
    "DHANUSHA",
    "MAKARA",
    "KUMBHA",
    "MEENA",
]

_CLASSICAL_CITATIONS: dict[str, str] = {
    "Gajakesari": "BPHS Ch. 28, Phaladeepika Ch. 9",
    "Raja": "BPHS Ch. 34, Uttara Kalamrita Ch. 5",
    "Dhana": "BPHS Ch. 35, Phaladeepika Ch. 11",
    "Budhaditya": "BPHS Ch. 22, Phaladeepika Ch. 8",
    "Vipareeta Raja": "BPHS Ch. 37, Uttara Kalamrita Ch. 7",
    "Malavya": "BPHS Ch. 39 (Pancha Mahapurusha)",
    "Ruchaka": "BPHS Ch. 39 (Pancha Mahapurusha)",
    "Bhadra": "BPHS Ch. 39 (Pancha Mahapurusha)",
    "Hamsa": "BPHS Ch. 39 (Pancha Mahapurusha)",
    "Sasa": "BPHS Ch. 39 (Pancha Mahapurusha)",
    "Sunapha": "BPHS Ch. 40 (Upapurusha)",
    "Anapha": "BPHS Ch. 40 (Upapurusha)",
    "Dhudhara": "BPHS Ch. 40 (Upapurusha)",
    "Amala": "BPHS Ch. 40 (Upapurusha)",
    "Neecha Bhanga": "BPHS Ch. 38, Phaladeepika Ch. 12",
    "Saraswati": "BPHS Ch. 41",
    "Adhi": "BPHS Ch. 40",
    "Vasumati": "BPHS Ch. 41",
}


# ══════════════════════════════════════════════════════════════════════════════
# Jatakam Book Generator
# ══════════════════════════════════════════════════════════════════════════════


class JatakamBookGenerator:
    """Generates the complete 5-part Jatakam Book as HTML/PDF."""

    def __init__(self, response: EvaluationResponse) -> None:
        self.response = response
        self.jre_facts = self._response_to_jre_facts()
        self.extended = ExtendedMetrics.enrich(self.jre_facts)

    # ── Response → JRE Facts Conversion ──────────────────────────────────────

    def _response_to_jre_facts(self) -> dict[str, Any]:
        """Convert EvaluationResponse back to jre_facts for narrative engines."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}
        am = r.aspect_matrix or []

        _RASHI_MAP = {
            "MESHA": 1,
            "VRISHABHA": 2,
            "MITHUNA": 3,
            "KARKA": 4,
            "SIMHA": 5,
            "KANYA": 6,
            "TULA": 7,
            "VRISHCHIKA": 8,
            "DHANUSHA": 9,
            "MAKARA": 10,
            "KUMBHA": 11,
            "MEENA": 12,
        }
        _SIGN_LORDS = {
            1: "MARS",
            2: "VENUS",
            3: "MERCURY",
            4: "MOON",
            5: "SUN",
            6: "MERCURY",
            7: "VENUS",
            8: "MARS",
            9: "JUPITER",
            10: "SATURN",
            11: "SATURN",
            12: "JUPITER",
        }

        planets: dict[str, dict[str, Any]] = {}
        for pname, detail in pd.items():
            planets[pname] = {
                "house": detail.get("house", 0),
                "rashi": detail.get("sign", ""),
                "rashi_num": _RASHI_MAP.get(detail.get("sign", ""), 0),
                "combust": detail.get("combust", False),
                "debilitated": detail.get("debilitated", False),
                "retrograde": detail.get("retrograde", False),
                "longitude": detail.get("degree_in_sign", 0)
                + ((_RASHI_MAP.get(detail.get("sign", ""), 1) - 1) * 30),
                "sign_lord": _SIGN_LORDS.get(_RASHI_MAP.get(detail.get("sign", ""), 1), ""),
                "dignity": dm.get(pname, ""),
            }

        lagna_sign_num = _RASHI_MAP.get(r.lagna, 1)
        lagna_idx = _RASHI_ORDER.index(r.lagna) if r.lagna in _RASHI_ORDER else 0
        house_lords: dict[int, str] = {}
        for i in range(12):
            rashi_idx = (lagna_idx + i) % 12
            rashi_name = _RASHI_ORDER[rashi_idx]
            house_lords[i + 1] = _SIGN_LORDS.get(_RASHI_MAP.get(rashi_name, i + 1), "")

        aspect_matrix: list[dict[str, Any]] = []
        for asp in am:
            aspect_matrix.append(
                {
                    "source": asp.get("source", ""),
                    "target": asp.get("target", ""),
                    "type": asp.get("type", "opposition"),
                    "angle_deg": asp.get("angle_deg", 0),
                    "source_house": asp.get("source_house"),
                    "target_house": asp.get("target_house"),
                }
            )

        planet_nakshatras: dict[str, str] = {}
        if r.moon_nakshatra:
            planet_nakshatras["MOON"] = r.moon_nakshatra

        return {
            "planets": planets,
            "house_lords": house_lords,
            "lagna_sign": lagna_sign_num,
            "dignity_map": dm,
            "planet_details": pd,
            "aspect_matrix": aspect_matrix,
            "planet_nakshatras": planet_nakshatras,
            "moon_nakshatra": r.moon_nakshatra or "",
        }

    # ════════════════════════════════════════════════════════════════════════
    # PART 1: Technical & Astronomical Foundation
    # ════════════════════════════════════════════════════════════════════════

    def _part1_technical(self) -> str:
        """Part 1: Astronomical Ephemeris, Divisional Charts, Strength Matrices."""
        r = self.response
        bd = r.birth_data_display
        ext = self.extended
        planets = self.jre_facts.get("planets", {})

        # 1.1 Birth Data & Panchanga
        birth_table = f"""
        <table class="data-table">
            <tr><td class="dt-label">Subject</td><td>{r.subject}</td></tr>
            <tr><td class="dt-label">Date of Birth</td><td>{bd.get("date", "—")}</td></tr>
            <tr><td class="dt-label">Time of Birth</td><td>{bd.get("time", "—")} ({bd.get("timezone", "—")})</td></tr>
            <tr><td class="dt-label">Latitude</td><td>{bd.get("latitude", "—")}</td></tr>
            <tr><td class="dt-label">Longitude</td><td>{bd.get("longitude", "—")}</td></tr>
            <tr><td class="dt-label">Lagna (Ascendant)</td><td><strong>{r.lagna}</strong> ({r.lagna_confidence})</td></tr>
            <tr><td class="dt-label">Moon Nakshatra</td><td>{r.moon_nakshatra or "—"}</td></tr>
            <tr><td class="dt-label">Ayanamsa</td><td>Lahiri (Chitrapaksha)</td></tr>
            <tr><td class="dt-label">House System</td><td>Whole-Sign</td></tr>
            <tr><td class="dt-label">Engine Version</td><td>{r.engine_version}</td></tr>
            <tr><td class="dt-label">Evaluation ID</td><td><code>{r.evaluation_id}</code></td></tr>
            <tr><td class="dt-label">Generated</td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
        </table>
        """

        # Planetary positions table
        planet_rows = ""
        for pname, pdata in sorted(planets.items()):
            rashi = _RASHI_NAMES.get(pdata.get("rashi", ""), pdata.get("rashi", "—"))
            deg = 0.0
            for pd_name, pd_detail in (r.planet_details or {}).items():
                if pd_name == pname:
                    deg = pd_detail.get("degree_in_sign", 0)
            retro = " (R)" if pdata.get("retrograde") else ""
            combust = " ☉" if pdata.get("combust") else ""
            dignity = r.dignity_map.get(pname, "—")
            planet_rows += f"""
            <tr>
                <td class="planet-name">{pname}{retro}{combust}</td>
                <td>{rashi}</td>
                <td>{deg:.2f}°</td>
                <td><span class="dignity-badge dignity-{dignity.lower().replace(" ", "-")}">{dignity}</span></td>
            </tr>
            """

        # 1.2 Divisional Charts
        div_charts = ext.get("divisional_charts", {})
        div_html = ""
        for div_name, chart in div_charts.items():
            div_rows = ""
            for pname in [
                "SUN",
                "MOON",
                "MARS",
                "MERCURY",
                "JUPITER",
                "VENUS",
                "SATURN",
                "RAHU",
                "KETU",
            ]:
                if pname in chart:
                    sign = _RASHI_NAMES.get(chart[pname], chart[pname])
                    div_rows += f"<tr><td>{pname}</td><td>{sign}</td></tr>"
            div_html += f"""
            <div class="div-chart-block">
                <h4>{div_name.replace("_", " ").title()}</h4>
                <table class="data-table compact">
                    <thead><tr><th>Planet</th><th>Sign</th></tr></thead>
                    <tbody>{div_rows}</tbody>
                </table>
            </div>
            """

        # 1.3 Strength Matrices
        shadbala = ext.get("shadbala", {})
        shad_rows = ""
        for pname in [
            "SUN",
            "MOON",
            "MARS",
            "MERCURY",
            "JUPITER",
            "VENUS",
            "SATURN",
            "RAHU",
            "KETU",
        ]:
            if pname in shadbala:
                s = shadbala[pname]
                shad_rows += f"""
                <tr>
                    <td class="planet-name">{pname}</td>
                    <td>{s.get("placement_rupas", 0):.1f}</td>
                    <td>{s.get("dignity_modifier", 1.0):.2f}</td>
                    <td><strong>{s.get("total_rupas", 0):.1f}</strong></td>
                    <td><span class="grade-{s.get("grade", "").lower().split()[0]}">{s.get("grade", "—")}</span></td>
                </tr>
                """

        # Ashtakavarga
        av = ext.get("ashtakavarga", {})
        sav = av.get("sav", {})
        av_rows = ""
        for h in range(1, 13):
            score = sav.get(h, 0)
            av_rows += f"""
            <tr>
                <td>House {h}</td>
                <td><strong>{score}</strong></td>
                <td>{"█" * score}{"░" * max(0, 40 - score)}</td>
            </tr>
            """

        return f"""
        <div class="part">
            <h1 class="part-title">Part 1: Technical & Astronomical Foundation</h1>

            <h2>1.1 Astronomical Ephemeris & Birth Data</h2>
            {birth_table}

            <h3>Planetary Positions (D1 Rashi Chart)</h3>
            <table class="data-table">
                <thead>
                    <tr><th>Planet</th><th>Sign (Rashi)</th><th>Degree</th><th>Dignity</th></tr>
                </thead>
                <tbody>{planet_rows}</tbody>
            </table>

            <h2>1.2 The Divisional Chart Matrix</h2>
            <div class="div-charts-grid">
                {div_html}
            </div>

            <h2>1.3 Mathematical Strength Matrices</h2>

            <h3>Shadbala (Six-Fold Strength)</h3>
            <table class="data-table">
                <thead>
                    <tr><th>Planet</th><th>Placement (Rupas)</th><th>Dignity Mod</th><th>Total</th><th>Grade</th></tr>
                </thead>
                <tbody>{shad_rows}</tbody>
            </table>

            <h3>Sarva-Ashtakavarga (Total Bindu Scores)</h3>
            <table class="data-table">
                <thead><tr><th>House</th><th>Score</th><th>Visual</th></tr></thead>
                <tbody>{av_rows}</tbody>
            </table>
            <p class="total-bindus">Total SAV Bindus: <strong>{av.get("total_bindus", 0)}</strong> (Average: {(av.get("total_bindus", 0) or 0) / 12:.1f} per house)</p>
        </div>
        """

    # ════════════════════════════════════════════════════════════════════════
    # PART 2: Static Lifetime Potential (12 Bhavas In-Depth)
    # ════════════════════════════════════════════════════════════════════════

    def _part2_bhavas(self) -> str:
        """Part 2: Detailed text-dense analysis of Houses 1-12."""
        engine = BhavaNarrativeEngine(self.extended)
        bhavas = engine.generate_all_bhavas()

        sections = ""
        for bhava in bhavas:
            house_num = bhava["house"]
            name = bhava["name"]
            domain = bhava["domain"]
            narrative = bhava["narrative"]
            lord = bhava.get("lord", "—")
            lord_dignity = bhava.get("lord_dignity", "—")
            sav_score = bhava.get("sav_score", 0)

            # Occupant details
            occ_details = ""
            for occ in bhava.get("occupants", []):
                retro_note = " (R)" if occ.get("retrograde") else ""
                occ_details += f"• <strong>{occ['name']}{retro_note}</strong> [{occ['dignity']}] — Shadbala: {occ.get('shadbala', 0):.1f} Rupas<br>"

            sections += f"""
            <div class="bhava-section">
                <h3>House {house_num}: {name} — {domain}</h3>
                <div class="bhava-meta">
                    <span class="meta-badge">Lord: {lord} [{lord_dignity}]</span>
                    <span class="meta-badge">SAV: {sav_score} bindus</span>
                    <span class="meta-badge">Nature: {bhava.get("nature", "—")}</span>
                </div>
                <div class="narrative-block">
                    {narrative}
                </div>
                {'<div class="occupant-detail"><h4>Occupying Planets:</h4>' + occ_details + "</div>" if occ_details else ""}
            </div>
            """

        return f"""
        <div class="part">
            <h1 class="part-title">Part 2: Static Lifetime Potential — The 12 Bhavas In-Depth</h1>
            <p class="part-intro">This section provides a comprehensive, text-dense analysis of each of the
            twelve houses (Bhavas) in the natal chart. For each house, we evaluate the house lord's
            dignity and placement, occupying planets, aspects, karakas (significators), and Ashtakavarga
            scores to produce a classical interpretation following BPHS and Phaladeepika conventions.</p>
            {sections}
        </div>
        """

    # ════════════════════════════════════════════════════════════════════════
    # PART 3: Major Conjunctions & Planetary Yogas
    # ════════════════════════════════════════════════════════════════════════

    def _part3_yogas(self) -> str:
        """Part 3: Raja/Dhana Yogas, Arishta Yogas, Pravrajya Yogas."""
        r = self.response
        yogas = r.yogas or []

        # Categorize yogas
        raja_yogas = [
            y for y in yogas if y.category in ("RAJA", "PANCHAMAHAPURUSHA") and y.status == "FORMED"
        ]
        dhana_yogas = [y for y in yogas if y.category == "DHANA" and y.status == "FORMED"]
        arishta_yogas = [y for y in yogas if y.status in ("WEAKENED", "CANCELLED")]
        spiritual_yogas = [
            y
            for y in yogas
            if y.status == "FORMED"
            and any(d in ("WISDOM_ACCUMULATION", "GENERAL_IMPROVEMENT") for d in y.domains)
        ]

        def _yoga_card(yoga, show_math: bool = False) -> str:
            citation = _CLASSICAL_CITATIONS.get(yoga.yoga_name, "")
            planets_str = ", ".join(yoga.involved_planets) if yoga.involved_planets else "—"
            strength = f"{yoga.static_strength:.0%}" if yoga.static_strength > 0 else "—"
            dynamic = f"{yoga.dynamic_strength:.2f}" if yoga.dynamic_strength is not None else "—"

            math_html = ""
            if show_math and (
                yoga.dasha_multiplier is not None or yoga.transit_multiplier is not None
            ):
                base = yoga.static_strength
                d_mult = yoga.dasha_multiplier if yoga.dasha_multiplier is not None else 1.0
                t_mult = yoga.transit_multiplier if yoga.transit_multiplier is not None else 1.0
                final = (
                    yoga.dynamic_strength
                    if yoga.dynamic_strength is not None
                    else (base * d_mult * t_mult)
                )
                math_html = f"""
                <div class="strength-calc">
                    {base:.2f} (Base) × {d_mult:.2f} (Dasha) × {t_mult:.2f} (Transit) = <strong>{final:.4f}</strong>
                </div>
                """

            return f"""
            <div class="yoga-card">
                <div class="yoga-header">
                    <span class="yoga-name">{yoga.yoga_name} Yoga</span>
                    <span class="status-formed">{yoga.status}</span>
                </div>
                <table class="detail-table">
                    <tr><td class="dt-label">Scripture</td><td>{citation}</td></tr>
                    <tr><td class="dt-label">Planets</td><td>{planets_str}</td></tr>
                    <tr><td class="dt-label">Strength</td><td>{strength} (Dynamic: {dynamic})</td></tr>
                    <tr><td class="dt-label">Domains</td><td>{", ".join(yoga.domains) if yoga.domains else "—"}</td></tr>
                </table>
                {math_html}
            </div>
            """

        # Raja & Dhana section
        raja_html = ""
        for y in raja_yogas:
            raja_html += _yoga_card(y, show_math=True)
        if not raja_yogas:
            raja_html = '<p class="note">No Raja or Pancha Mahapurusha yogas detected as FORMED in this chart.</p>'

        dhana_html = ""
        for y in dhana_yogas:
            dhana_html += _yoga_card(y, show_math=True)
        if not dhana_yogas:
            dhana_html = '<p class="note">No Dhana yogas detected as FORMED in this chart.</p>'

        # Arishta section
        arishta_html = ""
        for y in arishta_yogas:
            reason = y.cancellation_reason or "Classical conditions not met"
            arishta_html += f"""
            <div class="yoga-card arishta-card">
                <div class="yoga-header">
                    <span class="yoga-name">{y.yoga_name}</span>
                    <span class="status-{y.status.lower()}">{y.status}</span>
                </div>
                <p class="arishta-reason"><strong>Reason:</strong> {reason}</p>
                <p class="note">Classical texts prescribe specific remedial measures for this affliction.
                See Part 5 for mitigation protocols.</p>
            </div>
            """
        if not arishta_yogas:
            arishta_html = '<p class="note">No significant Arishta (affliction) yogas detected.</p>'

        # Spiritual section
        spiritual_html = ""
        for y in spiritual_yogas:
            spiritual_html += _yoga_card(y)
        if not spiritual_yogas:
            spiritual_html = '<p class="note">Spiritual yoga formations are assessed through house analysis in Part 2.</p>'

        return f"""
        <div class="part">
            <h1 class="part-title">Part 3: Major Conjunctions & Planetary Yogas</h1>

            <h2>3.1 Raja Yogas & Dhana Yogas</h2>
            <p class="part-intro">Raja Yogas indicate wealth and power blueprints. Dhana Yogas indicate
            financial prosperity potential. Pancha Mahapurusha yogas indicate exceptional personal qualities.</p>
            {raja_html}
            {dhana_html}

            <h2>3.2 Arishta & Daridra Yogas</h2>
            <p class="part-intro">Arishta yogas indicate affliction metrics that require conscious
            remedial attention. Every challenge carries the seed of transformation.</p>
            {arishta_html}

            <h2>3.3 Pravrajya Yogas — Spiritual Focus</h2>
            <p class="part-intro">Pravrajya yogas indicate renunciation or spiritual focus blueprints.
            These yogas suggest the native's spiritual inclinations and potential for inner development.</p>
            {spiritual_html}
        </div>
        """

    # ════════════════════════════════════════════════════════════════════════
    # PART 4: 90-Year Chronological Predictive Timeline
    # ════════════════════════════════════════════════════════════════════════

    def _part4_timeline(self) -> str:
        """Part 4: Decade-by-decade sequential breakdown."""
        engine = ChronologicalTimelineEngine(self.extended)
        decades = engine.generate_timeline()

        decade_sections = ""
        for decade in decades:
            age_start = decade["age_start"]
            age_end = decade["age_end"]
            phase = decade["phase"]
            title = decade["title"]
            narrative = decade["narrative"]

            decade_sections += f"""
            <div class="decade-section">
                <h3>{phase}: Ages {age_start}–{age_end} — {title}</h3>
                <div class="narrative-block decade-narrative">
                    {narrative}
                </div>
            </div>
            """

        return f"""
        <div class="part">
            <h1 class="part-title">Part 4: The 90-Year Chronological Predictive Timeline</h1>
            <p class="part-intro">This section maps the Vimshottari Dasha sequence and major transits
            across the native's 90-year lifespan. Each decade is analyzed for career, relationships,
            health, and spiritual evolution.</p>
            {decade_sections}
        </div>
        """

    # ════════════════════════════════════════════════════════════════════════
    # PART 5: Karmic Directives & Remedial Engineering
    # ════════════════════════════════════════════════════════════════════════

    def _part5_karmic_remedial(self) -> str:
        """Part 5: Karmic Node Axis + Practical Mitigation Protocols."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}

        # 5.1 Karmic Node Axis
        rahu_detail = pd.get("RAHU", {})
        ketu_detail = pd.get("KETU", {})
        rahu_sign = _RASHI_NAMES.get(rahu_detail.get("sign", ""), rahu_detail.get("sign", "—"))
        ketu_sign = _RASHI_NAMES.get(ketu_detail.get("sign", ""), ketu_detail.get("sign", "—"))

        karmic_narrative = (
            f"The karmic axis runs from <strong>Ketu in {ketu_sign}</strong> "
            f"(past-life gifts, comfort zone, innate talents) to "
            f"<strong>Rahu in {rahu_sign}</strong> (evolutionary direction, "
            f"growth area, unfamiliar territory). This axis defines the "
            f"native's primary karmic lesson: integrating Rahu's qualities "
            f"while honoring Ketu's natural gifts."
        )

        # 5.2 Remedial Protocols
        # Find most afflicted planets
        afflictions: list[dict[str, Any]] = []
        for pname in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            score = 0
            reasons: list[str] = []
            if dm.get(pname) == "Debilitated":
                score += 3
                reasons.append(f"{pname} is debilitated")
            # Check if any yoga involving this planet is weakened/cancelled
            for y in r.yogas or []:
                if pname in y.involved_planets:
                    if y.status == "CANCELLED":
                        score += 2
                        reasons.append(f"{pname} involved in cancelled {y.yoga_name} yoga")
                    elif y.status == "WEAKENED":
                        score += 1
                        reasons.append(f"{pname} involved in weakened {y.yoga_name} yoga")
            if score > 0:
                afflictions.append({"planet": pname, "score": score, "reasons": reasons})

        afflictions.sort(key=lambda x: x["score"], reverse=True)

        remedy_text = ""
        for aff in afflictions[:3]:
            pname = aff["planet"]
            reasons = " / ".join(aff["reasons"])
            remedy_text += f"""
            <div class="remedy-card">
                <h4>{pname} — {", ".join(aff["reasons"][:2])}</h4>
                <p><strong>Issue:</strong> {reasons}</p>
                <div class="remedy-protocols">
                    <p><strong>Mantra:</strong> Chant the {pname} mantra 108 times daily.</p>
                    <p><strong>Charity:</strong> Donate {pname.lower()}-related items on {pname.lower()}'s day.</p>
                    <p><strong>Vastu:</strong> Strengthen the {pname.lower()}-ruled direction in your living space.</p>
                    <p><strong>Meditation:</strong> Practice {pname.lower()}-balancing meditation techniques.</p>
                </div>
            </div>
            """

        if not remedy_text:
            remedy_text = """
            <div class="remedy-card">
                <p>No significantly afflicted planets detected. General remedial practices:</p>
                <ul>
                    <li>Daily prayer and meditation for spiritual grounding</li>
                    <li>Regular charitable giving on planetary days</li>
                    <li>Maintaining ethical conduct as prescribed in Phaladeepika</li>
                    <li>Worship of the Ishta Devata (chosen deity) for overall strength</li>
                </ul>
            </div>
            """

        # 5.3 Esoteric & Mystical Profile (DDE Compliant)
        esoteric_html = ""
        try:
            esoteric_profile = evaluate_esoteric_profile(
                self.jre_facts, strengths={}, language=getattr(self, "language", "en")
            )
            esoteric_html = render_esoteric_profile_html(esoteric_profile)
        except Exception:
            esoteric_html = """
            <div class="esoteric-section">
                <h3>5.3 Esoteric & Mystical Profile</h3>
                <p class="note">Esoteric profile evaluation unavailable for this chart configuration.</p>
            </div>
            """

        return f"""
        <div class="part">
            <h1 class="part-title">Part 5: Karmic Directives & Remedial Engineering</h1>

            <h2>5.1 The Evolutionary Karmic Node Axis</h2>
            <div class="karmic-grid">
                <div class="karmic-card karmic-ketu">
                    <div class="karmic-icon">☋</div>
                    <div class="karmic-label">Ketu (South Node)</div>
                    <div class="karmic-value">{ketu_sign}</div>
                    <div class="karmic-sub">Past-Life Gifts • Comfort Zone</div>
                </div>
                <div class="karmic-arrow">→</div>
                <div class="karmic-card karmic-rahu">
                    <div class="karmic-icon">☊</div>
                    <div class="karmic-label">Rahu (North Node)</div>
                    <div class="karmic-value">{rahu_sign}</div>
                    <div class="karmic-sub">Evolutionary Direction • Growth</div>
                </div>
            </div>
            <div class="narrative-block">{karmic_narrative}</div>

            <h2>5.2 Practical Mitigation Protocols</h2>
            <p class="part-intro">Classical remedial measures to balance problematic planetary frequencies.
            These protocols combine mantra, charity, Vastu, and meditative practices.</p>
            {remedy_text}

            {esoteric_html}
        </div>
        """

    # ════════════════════════════════════════════════════════════════════════
    # Full Document Assembly
    # ════════════════════════════════════════════════════════════════════════

    def _build_full_html(self) -> str:
        """Build the complete 5-part Jatakam Book HTML document."""
        r = self.response

        part1 = self._part1_technical()
        part2 = self._part2_bhavas()
        part3 = self._part3_yogas()
        part4 = self._part4_timeline()
        part5 = self._part5_karmic_remedial()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Jatakam Book — {r.subject}</title>
{_JATAKAM_CSS}
</head>
<body>

<!-- Cover Page -->
<div class="cover-page">
    <div class="cover-symbol">✦</div>
    <h1 class="cover-title">Jatakam</h1>
    <h2 class="cover-subtitle">Comprehensive Vedic Astrological Analysis</h2>
    <p class="cover-subject">{r.subject}</p>
    <div class="cover-meta">
        <p>Date of Birth: {r.birth_data_display.get("date", "—")}</p>
        <p>Time: {r.birth_data_display.get("time", "—")} | Place: {r.birth_data_display.get("latitude", "—")}, {r.birth_data_display.get("longitude", "—")}</p>
        <p>Lagna: {r.lagna} | Moon Nakshatra: {r.moon_nakshatra or "—"}</p>
    </div>
    <div class="cover-disclaimer">
        <p>{LEGAL_DISCLAIMER}</p>
    </div>
    <p class="cover-footer">Generated by Jyotish Reasoning Engine {r.engine_version} | {datetime.now().strftime("%Y-%m-%d")}</p>
</div>

<!-- Table of Contents -->
<div class="toc-page">
    <h1>Table of Contents</h1>
    <div class="toc-list">
        <div class="toc-item"><span class="toc-part">Part 1</span> Technical & Astronomical Foundation</div>
        <div class="toc-item"><span class="toc-part">Part 2</span> Static Lifetime Potential — The 12 Bhavas In-Depth</div>
        <div class="toc-item"><span class="toc-part">Part 3</span> Major Conjunctions & Planetary Yogas</div>
        <div class="toc-item"><span class="toc-part">Part 4</span> The 90-Year Chronological Predictive Timeline</div>
        <div class="toc-item"><span class="toc-part">Part 5</span> Karmic Directives & Remedial Engineering</div>
    </div>
</div>

{part1}

{part2}

{part3}

{part4}

{part5}

</body>
</html>"""

    def generate_pdf(self) -> bytes:
        """Generate the Jatakam Book as PDF bytes."""
        from weasyprint import HTML

        html_content = self._build_full_html()
        doc = HTML(string=html_content)
        return doc.write_pdf()

    def generate_html(self) -> str:
        """Generate the Jatakam Book as HTML string."""
        return self._build_full_html()


# ══════════════════════════════════════════════════════════════════════════════
# CSS Stylesheet
# ══════════════════════════════════════════════════════════════════════════════

_JATAKAM_CSS = """
<style>
    @page {
        size: A4;
        margin: 2cm 2.5cm;
        @bottom-center {
            content: "Jatakam Book — Page " counter(page);
            font-size: 8pt;
            color: #999;
        }
    }
    @page :first {
        margin-top: 3cm;
        @bottom-center { content: none; }
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #222;
    }

    /* Cover Page */
    .cover-page {
        text-align: center;
        padding-top: 3cm;
        page-break-after: always;
    }
    .cover-symbol { font-size: 48pt; color: #8B0000; margin-bottom: 0.5cm; }
    .cover-title { font-size: 28pt; color: #8B0000; margin-bottom: 0.3cm; }
    .cover-subtitle { font-size: 14pt; color: #4A0E0E; font-weight: normal; margin-bottom: 1cm; }
    .cover-subject { font-size: 18pt; font-weight: bold; color: #333; margin-bottom: 1.5cm; }
    .cover-meta { font-size: 10pt; color: #555; margin-bottom: 2cm; line-height: 1.8; }
    .cover-disclaimer { max-width: 400px; margin: 0 auto 1cm auto; font-size: 8pt; color: #888; text-align: left; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
    .cover-footer { font-size: 9pt; color: #999; margin-top: 3cm; }

    /* Table of Contents */
    .toc-page { page-break-after: always; padding-top: 2cm; }
    .toc-page h1 { font-size: 18pt; color: #8B0000; margin-bottom: 1cm; }
    .toc-list { max-width: 500px; }
    .toc-item { padding: 8px 0; border-bottom: 1px dotted #ccc; font-size: 11pt; }
    .toc-part { display: inline-block; width: 60px; font-weight: bold; color: #8B0000; }

    /* Parts */
    .part { page-break-before: always; }
    .part-title {
        font-size: 18pt;
        color: #8B0000;
        border-bottom: 2px solid #8B0000;
        padding-bottom: 6px;
        margin: 0 0 0.8cm 0;
    }
    .part-intro { font-style: italic; color: #555; margin-bottom: 0.6cm; font-size: 9.5pt; }

    /* Headings */
    h2 { font-size: 13pt; color: #4A0E0E; margin: 0.8cm 0 0.4cm 0; border-bottom: 1px solid #ddd; padding-bottom: 3px; }
    h3 { font-size: 11pt; color: #4A0E0E; margin: 0.5cm 0 0.3cm 0; }
    h4 { font-size: 10pt; color: #555; margin: 0.4cm 0 0.2cm 0; }

    /* Tables */
    .data-table { width: 100%; border-collapse: collapse; margin: 0.4cm 0 0.6cm 0; font-size: 9pt; }
    .data-table th { background: #8B0000; color: white; padding: 6px 8px; text-align: left; font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.3px; }
    .data-table td { padding: 5px 8px; border-bottom: 1px solid #eee; }
    .data-table tr:nth-child(even) { background: #fafafa; }
    .data-table.compact td { padding: 3px 6px; font-size: 8.5pt; }
    .dt-label { font-weight: bold; color: #555; width: 150px; white-space: nowrap; }
    .detail-table { width: 100%; border-collapse: collapse; margin: 4px 0; font-size: 9pt; }
    .detail-table td { padding: 3px 8px; border-bottom: 1px solid #f0f0f0; }

    /* Divisional Charts Grid */
    .div-charts-grid { display: flex; flex-wrap: wrap; gap: 0.4cm; }
    .div-chart-block { flex: 1 1 200px; border: 1px solid #eee; border-radius: 4px; padding: 6px; }
    .div-chart-block h4 { font-size: 9pt; color: #8B0000; margin-bottom: 4px; }

    /* Grades */
    .grade-uttama { color: #155724; font-weight: bold; }
    .grade-good { color: #0c5460; font-weight: bold; }
    .grade-average { color: #856404; }
    .grade-weak { color: #721c24; }
    .grade-very { color: #721c24; font-weight: bold; }

    /* Total Bindus */
    .total-bindus { font-size: 9pt; color: #555; margin: 0.3cm 0; }

    /* Bhava Sections */
    .bhava-section { margin: 0.6cm 0; padding: 0.5cm; border-left: 3px solid #8B0000; background: #fafafa; border-radius: 0 4px 4px 0; page-break-inside: avoid; }
    .bhava-meta { margin: 4px 0 8px 0; }
    .meta-badge { display: inline-block; font-size: 8pt; padding: 2px 6px; margin-right: 6px; background: #f0f0f0; border-radius: 3px; color: #555; }
    .narrative-block { margin: 0.4cm 0; padding: 10px 14px; background: #fff; border-left: 3px solid #8B0000; border-radius: 0 4px 4px 0; font-size: 9.5pt; line-height: 1.6; }
    .occupant-detail { margin-top: 6px; font-size: 9pt; }

    /* Yoga Cards */
    .yoga-card { border: 1px solid #e0d0d0; border-radius: 4px; padding: 10px 14px; margin: 0.4cm 0; page-break-inside: avoid; }
    .yoga-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .yoga-name { font-size: 11pt; font-weight: bold; color: #4A0E0E; }
    .status-formed { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }
    .status-weakened { background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }
    .status-cancelled { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }
    .arishta-card { border-left: 3px solid #e74c3c; }
    .arishta-reason { font-size: 9pt; margin: 4px 0; }
    .strength-calc { font-family: 'Courier New', monospace; font-size: 8.5pt; background: #f8f4f4; padding: 6px 10px; border-radius: 3px; margin-top: 4px; border-left: 3px solid #8B0000; }

    /* Karmic Grid */
    .karmic-grid { display: flex; align-items: center; gap: 0.5cm; margin: 0.5cm 0; }
    .karmic-card { flex: 1; text-align: center; padding: 12px; border-radius: 6px; }
    .karmic-ketu { background: #f5f0ff; border: 1px solid #d4c4f0; }
    .karmic-rahu { background: #fff5f0; border: 1px solid #f0d4c4; }
    .karmic-arrow { font-size: 24pt; color: #8B0000; }
    .karmic-icon { font-size: 18pt; color: #8B0000; }
    .karmic-label { font-size: 8pt; color: #888; text-transform: uppercase; }
    .karmic-value { font-size: 12pt; font-weight: bold; color: #4A0E0E; margin: 4px 0; }
    .karmic-sub { font-size: 8pt; color: #999; }

    /* Remedy Cards */
    .remedy-card { border: 1px solid #d4edda; border-radius: 6px; padding: 12px 16px; margin: 0.5cm 0; background: #f8fff8; }
    .remedy-protocols { margin-top: 6px; font-size: 9pt; }
    .remedy-protocols p { margin: 3px 0; }

    /* Decade Sections */
    .decade-section { margin: 0.5cm 0; page-break-inside: avoid; }
    .decade-narrative { font-size: 9.5pt; }

    /* Utilities */
    .note { font-size: 8.5pt; color: #888; font-style: italic; }
    .planet-name { font-weight: bold; }
    .dignity-badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 8pt; font-weight: bold; }
    .dignity-exalted { background: #d4edda; color: #155724; }
    .dignity-moolatrikona { background: #cce5ff; color: #004085; }
    .dignity-own-sign { background: #d1ecf1; color: #0c5460; }
    .dignity-friendly { background: #e2e3e5; color: #383d41; }
    .dignity-neutral { background: #f8f9fa; color: #6c757d; }
    .dignity-enemy { background: #fff3cd; color: #856404; }
    .dignity-debilitated { background: #f8d7da; color: #721c24; }
    code { font-family: 'Courier New', monospace; font-size: 9pt; background: #f0f0f0; padding: 1px 4px; border-radius: 2px; }
    .warning-box { max-width: 500px; margin: 0.5cm 0; padding: 12px 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; font-size: 9pt; color: #664d03; }

    /* Esoteric & Mystical Section */
    .esoteric-section { margin: 0.5cm 0; }
    .esoteric-card { border: 1px solid #e8d5f5; border-left: 4px solid #7b2d8e; border-radius: 6px; padding: 14px 18px; margin: 0.5cm 0; background: linear-gradient(135deg, #fdf8ff 0%, #f5f0fa 100%); page-break-inside: avoid; }
    .esoteric-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 4px; }
    .esoteric-planet { font-size: 10pt; font-weight: bold; color: #7b2d8e; }
    .esoteric-nakshatra { font-size: 11pt; font-weight: bold; color: #4A0E0E; }
    .esoteric-token { font-family: 'Courier New', monospace; font-size: 7.5pt; color: #8B5CF6; background: #f0e6ff; padding: 2px 6px; border-radius: 3px; }
    .esoteric-meta { margin: 6px 0; }
    .esoteric-shakti { font-size: 9pt; color: #555; margin: 4px 0 8px 0; font-style: italic; }
    .esoteric-narrative { border-left-color: #7b2d8e !important; }
    .narrative-section { margin-bottom: 8px; }
    .narrative-label { font-size: 8.5pt; color: #7b2d8e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; font-weight: bold; }
    .gandanta-warning { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; margin: 6px 0; font-size: 8.5pt; }
    .gandanta-badge { background: #dc3545; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold; font-size: 8pt; white-space: nowrap; }
    .gandanta-desc { color: #664d03; }
</style>
"""
