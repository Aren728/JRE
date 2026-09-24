"""JRE Reporting — Comprehensive 9-Step PDF report generator.

Generates a world-class, professional astrological analysis following
the exact 9-step sequence mandated in Phase I6.

NO engine logic — pure presentation layer using weasyprint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jrs.api.schemas import ENGINE_VERSION, LEGAL_DISCLAIMER, EvaluationResponse

# ── Classical Citations ─────────────────────────────────────────────────────

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

_CLASSICAL_RULES: dict[str, str] = {
    "Gajakesari": "Jupiter in Kendra (1st, 4th, 7th, or 10th house) from the Moon",
    "Raja": "Kendra lord (angular house ruler) conjunct or mutually aspecting Trikona lord (trinal house ruler)",
    "Dhana": "Lords of 2nd, 5th, 9th, or 11th houses connected through conjunction or aspect",
    "Budhaditya": "Sun and Mercury conjunct in the same sign within 10° orb",
    "Vipareeta Raja": "Lord of 6th, 8th, or 12th house placed in another dusthana house",
    "Malavya": "Venus in own sign or exaltation in a Kendra (1st, 4th, 7th, 10th)",
    "Ruchaka": "Mars in own sign or exaltation in a Kendra",
    "Bhadra": "Mercury in own sign or exaltation in a Kendra",
    "Hamsa": "Jupiter in own sign or exaltation in a Kendra",
    "Sasa": "Saturn in own sign or exaltation in a Kendra",
    "Sunapha": "A benefic planet 2nd from the Moon",
    "Anapha": "A benefic planet 12th from the Moon",
    "Dhudhara": "A benefic planet 2nd and 12th from the Moon simultaneously",
    "Amala": "A benefic planet in the 10th from Lagna or Moon",
    "Neecha Bhanga": "Debilitation sign lord in Kendra from Lagna or conjunct Lagna lord",
    "Saraswati": "Jupiter, Venus, Mercury in Kendra/Trikona from Lagna, or Jupiter+Venus in 2nd house",
    "Adhi": "Benefics (Mercury, Jupiter, Venus) in 6th, 7th, or 8th houses from Lagna or Moon",
    "Vasumati": "Benefics in Upachaya houses (3, 6, 10, 11) from Lagna or Moon",
}

_MODIFIER_DESCRIPTIONS: list[tuple[str, str]] = [
    ("Combustion", "Planet within ~8° of the Sun — reduced strength"),
    ("Debilitation", "Planet in its sign of debilitation — diminished dignity"),
    ("Planetary War", "Two planets within 1° — both lose functional strength"),
    ("Retrograde", "Planet appears retrograde — alters ownership and strength"),
    ("Node Influence", "Rahu/Ketu conjunction or aspect — modifies results"),
]

_DIGNITY_DESCRIPTIONS: dict[str, str] = {
    "Exalted": "Operating at peak strength; bestows exceptional results in its significations",
    "Moolatrikona": "Deeply comfortable; functionally powerful with clear, strong results",
    "Own Sign": "Naturally strong and self-sufficient; expresses significations with authority",
    "Friendly": "Well-placed and cooperative; produces beneficial results with ease",
    "Neutral": "Neither particularly strong nor weak; moderate, context-dependent results",
    "Enemy": "Placed in a hostile environment; may create friction in significations",
    "Debilitated": "Significantly weakened; requires Neecha Bhanga for beneficial results",
}


# ── PDF Generator ───────────────────────────────────────────────────────────


class PDFReportGenerator:
    """Generates a comprehensive multi-page PDF report following the 9-step sequence."""

    def __init__(self, response: EvaluationResponse, language: str = "en") -> None:
        self.response = response
        self.language = language

    # ── Step 1: Birth Data Verification ──────────────────────────────────────

    def _step1_birth_data(self) -> str:
        """Step 1: Clean table of Date, Time, Place, UTC, Ayanamsa, and planetary longitudes."""
        r = self.response
        bd = r.birth_data_display

        tob_warning = ""
        if r.unknown_tob:
            skipped = ", ".join(r.skipped_yogas) if r.skipped_yogas else "N/A"
            tob_warning = f"""
            <div class="warning-box">
                <strong>⚠ Unknown Time of Birth</strong><br>
                Birth time was not provided. Noon (12:00) was used as a computational
                default for planetary positions. <strong>The computed Lagna is unreliable
                and Lagna-dependent yogas have been suspended.</strong><br><br>
                <em>Skipped yogas:</em> {skipped}
            </div>
            """

        # Planetary longitudes table
        planet_rows = ""
        for pname, pdetail in sorted(r.planet_details.items()):
            sign = pdetail.get("sign", "—")
            deg = pdetail.get("degree_in_sign", 0)
            element = pdetail.get("element", "—")
            modality = pdetail.get("modality", "—")
            retro = (
                " (R)"
                if r.yogas
                and any(y.involved_planets and pname in y.involved_planets for y in r.yogas)
                else ""
            )
            planet_rows += f"""
            <tr>
                <td>{pname}{retro}</td>
                <td>{sign}</td>
                <td>{deg:.2f}°</td>
                <td>{element.title()}</td>
                <td>{modality.title()}</td>
            </tr>
            """

        return f"""
        <div class="section-page">
            <h2>Step 1 — Birth Data Verification</h2>
            {tob_warning}
            <div class="birth-data-grid">
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
            </div>
            <h3>Planetary Positions</h3>
            <table class="data-table">
                <thead>
                    <tr><th>Planet</th><th>Sign (Rashi)</th><th>Degree in Sign</th><th>Element</th><th>Modality</th></tr>
                </thead>
                <tbody>
                    {planet_rows}
                </tbody>
            </table>
            <div class="disclaimer-box">
                <strong>Disclaimer:</strong> {LEGAL_DISCLAIMER}
            </div>
        </div>
        """

    # ── Step 2: Elemental & Modality Balance ──────────────────────────────────

    def _step2_elements(self) -> str:
        """Step 2: Visual bar chart or clean table showing elemental/modality distribution."""
        r = self.response
        eb = r.elemental_balance or {}
        mb = r.modality_balance or {}

        def _bar_html(count: int, max_count: int, color: str, label: str) -> str:
            pct = (count / max(max_count, 1)) * 100 if max_count > 0 else 0
            return f"""
            <tr>
                <td class="dt-label">{label}</td>
                <td>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {pct}%; background: {color};"></div>
                    </div>
                </td>
                <td class="bar-count">{count}</td>
            </tr>
            """

        max_elem = max(eb.values()) if eb else 1
        max_mod = max(mb.values()) if mb else 1

        return f"""
        <div class="section-page">
            <h2>Step 2 — Elemental & Modality Balance</h2>
            <div class="two-col">
                <div>
                    <h3>Elemental Distribution</h3>
                    <table class="data-table">
                        {_bar_html(eb.get("fire", 0), max_elem, "#e74c3c", "🔥 Fire (Agni)")}
                        {_bar_html(eb.get("earth", 0), max_elem, "#27ae60", "🌍 Earth (Prithvi)")}
                        {_bar_html(eb.get("air", 0), max_elem, "#3498db", "💨 Air (Vayu)")}
                        {_bar_html(eb.get("water", 0), max_elem, "#9b59b6", "💧 Water (Jala)")}
                    </table>
                </div>
                <div>
                    <h3>Modality Distribution</h3>
                    <table class="data-table">
                        {_bar_html(mb.get("cardinal", 0), max_mod, "#e67e22", "Cardinal (Chara)")}
                        {_bar_html(mb.get("fixed", 0), max_mod, "#2c3e50", "Fixed (Sthira)")}
                        {_bar_html(mb.get("mutable", 0), max_mod, "#1abc9c", "Mutable (Sara)")}
                    </table>
                </div>
            </div>
        </div>
        """

    # ── Step 3: Primary Triad ────────────────────────────────────────────────

    def _step3_triad(self) -> str:
        """Step 3: Narrative synthesis of Lagna, Sun, and Moon."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}
        bd = r.birth_data_display

        _RASHI_NAMES: dict[str, str] = {
            "MESHA": "Aries",
            "VRISHABHA": "Taurus",
            "MITHUNA": "Gemini",
            "KARKA": "Cancer",
            "SIMHA": "Leo",
            "KANYA": "Virgo",
            "TULA": "Libra",
            "VRISHCHIKA": "Scorpio",
            "DHANUSHA": "Sagittarius",
            "MAKARA": "Capricorn",
            "KUMBHA": "Aquarius",
            "MEENA": "Pisces",
        }

        lagna_name = _RASHI_NAMES.get(r.lagna, r.lagna)
        sun_detail = pd.get("SUN", {})
        moon_detail = pd.get("MOON", {})
        sun_dignity = dm.get("SUN", "Neutral")
        moon_dignity = dm.get("MOON", "Neutral")

        sun_sign = _RASHI_NAMES.get(sun_detail.get("sign", ""), sun_detail.get("sign", "—"))
        moon_sign = _RASHI_NAMES.get(moon_detail.get("sign", ""), moon_detail.get("sign", "—"))

        # Build triad narrative
        triad_text = f"""The native's Lagna (Ascendant) is <strong>{lagna_name}</strong>, """
        element = sun_detail.get("element", "fire")
        if element == "fire":
            triad_text += "endowing the physical body and outward temperament with dynamic, initiative-driven energy. "
        elif element == "earth":
            triad_text += "providing a practical, grounded, and materially-oriented temperament. "
        elif element == "air":
            triad_text += "granting an intellectual, communicative, and socially-oriented nature. "
        else:
            triad_text += "bestowing deep emotional intelligence, intuitive perception, and empathic sensitivity. "

        triad_text += f"""The Sun, representing the soul and core identity, is placed in <strong>{sun_sign}</strong> """
        triad_text += f"({sun_dignity}). "

        triad_text += f"""The Moon, governing the mind and emotional nature, resides in <strong>{moon_sign}</strong> """
        triad_text += f"({moon_dignity}). "

        triad_text += (
            "Together, this Lagna-Sun-Moon triad forms the foundational axis of the natal chart."
        )

        return f"""
        <div class="section-page">
            <h2>Step 3 — Primary Triad Analysis</h2>
            <div class="triad-grid">
                <div class="triad-card">
                    <div class="triad-icon">ASC</div>
                    <div class="triad-title">Lagna</div>
                    <div class="triad-value">{lagna_name}</div>
                    <div class="triad-sub">Physical Body & Temperament</div>
                </div>
                <div class="triad-card">
                    <div class="triad-icon">☉</div>
                    <div class="triad-title">Sun</div>
                    <div class="triad-value">{sun_sign}</div>
                    <div class="triad-sub">Soul & Core Identity</div>
                </div>
                <div class="triad-card">
                    <div class="triad-icon">☽</div>
                    <div class="triad-title">Moon</div>
                    <div class="triad-value">{moon_sign}</div>
                    <div class="triad-sub">Mind & Emotional Nature</div>
                </div>
            </div>
            <div class="narrative-block">
                {triad_text}
            </div>
        </div>
        """

    # ── Step 3.5: Classical House Placements & Conjunctions ────────────────

    def _step35_house_placements(self) -> str:
        """Step 3.5: Detailed classical interpretation of each occupied house."""
        from jrs.reporting.narrative_engine import generate_classical_house_narratives

        # Build jre_facts from response data for the narrative engine
        jre_facts = self._response_to_jre_facts()
        narratives = generate_classical_house_narratives(jre_facts)

        if not narratives:
            return """
            <div class="section-page">
                <h2>Step 3.5 — House Placements & Conjunctions</h2>
                <p class="note">No classical house interpretations available for this chart.</p>
            </div>
            """

        sections = ""
        for house_data in narratives:
            house_num = house_data["house"]
            house_name = house_data["house_name"]
            domain = house_data["domain"]
            signifies = house_data["signifies"]
            narratives_list = house_data["narratives"]

            interp_html = ""
            for n in narratives_list:
                ntype = n["type"]
                planets_list = n["planets"]
                text = n["interpretation"]
                dignity = n.get("dignity", "")

                if ntype == "conjunction":
                    header = f"Conjunction: {' + '.join(planets_list)}"
                    if dignity:
                        header += f" [{dignity}]"
                    interp_html += f"""
                    <div class="narrative-block" style="border-left-color: #e74c3c; margin-top: 6px;">
                        <strong>{header}</strong><br>
                        {text}
                    </div>
                    """
                else:
                    pname = planets_list[0]
                    header = f"{pname} in House {house_num}"
                    if dignity:
                        header += f" [{dignity}]"
                    interp_html += f"""
                    <div class="narrative-block" style="margin-top: 6px;">
                        <strong>{header}</strong><br>
                        {text}
                    </div>
                    """

            sections += f"""
            <div class="house-interpretation">
                <h3>{house_name} ({domain}) — House {house_num}</h3>
                <p class="note" style="margin-bottom: 4px;">Signifies: {signifies}</p>
                {interp_html}
            </div>
            """

        return f"""
        <div class="section-page">
            <h2>Step 3.5 — House Placements & Conjunctions</h2>
            <p class="note">Classical interpretations from BPHS and Phaladeepika for each occupied house.</p>
            {sections}
        </div>
        """

    # ── Step 3.6: Nakshatra Influences ──────────────────────────────────────

    def _step36_nakshatras(self) -> str:
        """Step 3.6: Significant nakshatra placements and their influences."""
        from jrs.reporting.narrative_engine import generate_nakshatra_narratives

        jre_facts = self._response_to_jre_facts()
        narratives = generate_nakshatra_narratives(jre_facts)

        if not narratives:
            return """
            <div class="section-page">
                <h2>Step 3.6 — Nakshatra Influences</h2>
                <p class="note">Nakshatra data is not available for this chart.</p>
            </div>
            """

        cards = ""
        for n in narratives:
            planet = n["planet"]
            nak = n["nakshatra"].replace("_", " ").title()
            text = n["interpretation"]
            cards += f"""
            <div class="yoga-card" style="border-left: 3px solid #9b59b6;">
                <div class="yoga-header">
                    <span class="yoga-name">{planet} in {nak}</span>
                </div>
                <div class="narrative-block" style="border-left-color: #9b59b6; margin-top: 6px;">
                    {text}
                </div>
            </div>
            """

        return f"""
        <div class="section-page">
            <h2>Step 3.6 — Nakshatra Influences</h2>
            <p class="note">The nakshatra (lunar mansion) layer reveals subtle emotional and karmic
            patterns beyond the rashi-level interpretation.</p>
            {cards}
        </div>
        """

    # ── Step 3.7: Aspectual Themes ──────────────────────────────────────────

    def _step37_aspect_themes(self) -> str:
        """Step 3.7: Narrative interpretation of planetary aspects."""
        from jrs.reporting.narrative_engine import generate_aspectual_themes

        jre_facts = self._response_to_jre_facts()
        themes = generate_aspectual_themes(jre_facts)

        if not themes:
            return """
            <div class="section-page">
                <h2>Step 3.7 — Aspectual Themes</h2>
                <p class="note">No significant planetary aspects detected.</p>
            </div>
            """

        items = ""
        for t in themes:
            source = t["source"]
            target = t["target"]
            atype = t["aspect_type"].replace("_", " ").title()
            angle = t.get("angle_deg", 0)
            narrative = t["narrative"]
            sh = t.get("source_house")
            th = t.get("target_house")
            house_info = f" (H{sh}→H{th})" if sh and th else ""

            items += f"""
            <div class="aspect-item">
                <div class="aspect-header">
                    <strong>{source}</strong> {atype}{house_info} <strong>{target}</strong>
                    <span class="note" style="margin-left: 8px;">{angle:.0f}°</span>
                </div>
                <div class="narrative-block" style="margin-top: 4px; font-size: 9pt;">
                    {narrative}
                </div>
            </div>
            """

        return f"""
        <div class="section-page">
            <h2>Step 3.7 — Aspectual Themes</h2>
            <p class="note">Vedic aspects create dynamic relationships between planets across the chart.
            Each aspect modifies the energy of both the source and target planets.</p>
            {items}
        </div>
        """

    # ── Helper: Convert response data to jre_facts dict ─────────────────────

    def _response_to_jre_facts(self) -> dict[str, Any]:
        """Convert EvaluationResponse fields back to a jre_facts-like dictionary
        for use by the narrative engine functions.
        """
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}
        am = r.aspect_matrix or []

        # Reconstruct planets dict from planet_details
        planets: dict[str, dict[str, Any]] = {}
        for pname, detail in pd.items():
            planets[pname] = {
                "house": detail.get("house", 0),
                "rashi": detail.get("sign", ""),
                "combust": detail.get("combust", False),
                "debilitated": detail.get("debilitated", False),
                "retrograde": detail.get("retrograde", False),
                "dignity": dm.get(pname, ""),
            }

        # Try to extract lagna sign number
        lagna_sign_num = 1
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
        lagna_sign_num = _RASHI_MAP.get(r.lagna, 1)

        # Build house_lords from lagna
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
        lagna_idx = _RASHI_ORDER.index(r.lagna) if r.lagna in _RASHI_ORDER else 0
        house_lords: dict[int, str] = {}
        for i in range(12):
            rashi_idx = (lagna_idx + i) % 12
            rashi_name = _RASHI_ORDER[rashi_idx]
            house_lords[i + 1] = _SIGN_LORDS.get(_RASHI_MAP.get(rashi_name, i + 1), "")

        # Reconstruct aspect_matrix as dicts
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

        # Planet nakshatras from response (if available)
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

    # ── Step 4: Planetary Strengths & Dignities ──────────────────────────────

    def _step4_dignities(self) -> str:
        """Step 4: Table showing Planet, Sign, Degree, and Dignity Status."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}

        rows = ""
        for pname in sorted(pd.keys()):
            detail = pd[pname]
            dignity = dm.get(pname, "—")
            dignity_class = dignity.lower().replace(" ", "-")
            deg = detail.get("degree_in_sign", 0)
            rows += f"""
            <tr>
                <td class="planet-name">{pname}</td>
                <td>{detail.get("sign", "—")}</td>
                <td>{deg:.2f}°</td>
                <td><span class="dignity-badge dignity-{dignity_class}">{dignity}</span></td>
            </tr>
            """

        return f"""
        <div class="section-page">
            <h2>Step 4 — Planetary Strengths & Dignities</h2>
            <table class="data-table">
                <thead>
                    <tr><th>Planet</th><th>Sign (Rashi)</th><th>Degree</th><th>Dignity</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <div class="note">
                Dignity classifications follow classical BPHS rules: Exalted, Moolatrikona,
                Own Sign, Friendly, Neutral, Enemy, and Debilitated.
            </div>
        </div>
        """

    # ── Step 5: Geometrical Aspect Matrix ────────────────────────────────────

    def _step5_aspects(self) -> str:
        """Step 5: Clean table of major aspects and their orbs."""
        r = self.response
        aspects = r.aspect_matrix or []

        if not aspects:
            return """
            <div class="section-page">
                <h2>Step 5 — Geometrical Aspect Matrix</h2>
                <p class="note">No significant Vedic aspects detected between planets.</p>
            </div>
            """

        rows = ""
        for asp in aspects:
            rows += f"""
            <tr>
                <td class="planet-name">{asp.get("source", "—")}</td>
                <td>{asp.get("type", "—").replace("_", " ").title()}</td>
                <td class="planet-name">{asp.get("target", "—")}</td>
                <td>{asp.get("angle_deg", 0):.0f}°</td>
                <td>H{asp.get("source_house", "?")} → H{asp.get("target_house", "?")}</td>
            </tr>
            """

        return f"""
        <div class="section-page">
            <h2>Step 5 — Geometrical Aspect Matrix</h2>
            <p class="note">Vedic aspects are house-based: all planets aspect the 7th house;
            Mars also aspects 4th and 8th; Jupiter aspects 5th and 9th; Saturn aspects 3rd and 10th.</p>
            <table class="data-table">
                <thead>
                    <tr><th>Source</th><th>Aspect Type</th><th>Target</th><th>Angle</th><th>House Path</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    # ── Step 6: Categorized House Analysis ───────────────────────────────────

    def _step6_houses(self) -> str:
        """Step 6: Narrative grouped by life domains."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}

        _HOUSE_DOMAINS: dict[str, list[int]] = {
            "Personality & Self": [1],
            "Wealth & Family": [2, 11],
            "Communication & Courage": [3],
            "Home & Happiness": [4],
            "Children & Creativity": [5],
            "Health & Service": [6],
            "Marriage & Partnership": [7],
            "Obstacles & Transformation": [8],
            "Fortune & Dharma": [9],
            "Career & Status": [10],
            "Gains & Aspirations": [11],
            "Loss & Liberation": [12],
        }

        sections = ""
        for domain, houses in _HOUSE_DOMAINS.items():
            occupants: list[tuple[str, dict[str, Any]]] = []
            for pname, pdata in r.planet_details.items():
                # Use dignity map to find planets in relevant houses
                pass

            # Find planets by checking all yogas that involve these houses
            found_planets: list[str] = []
            for y in r.yogas:
                for pname in y.involved_planets:
                    if pname in pd and pd[pname].get("sign"):
                        found_planets.append(pname)

            if not found_planets:
                continue

            planet_strs = []
            for pname in set(found_planets):
                detail = pd.get(pname, {})
                sign = detail.get("sign", "—")
                deg = detail.get("degree_in_sign", 0)
                dignity = dm.get(pname, "")
                planet_strs.append(f"<strong>{pname}</strong> in {sign} ({deg:.1f}°) [{dignity}]")

            sections += f"""
            <div class="house-domain">
                <h3>{domain} (House {", ".join(str(h) for h in houses)})</h3>
                <p>{", ".join(planet_strs)}</p>
            </div>
            """

        return f"""
        <div class="section-page">
            <h2>Step 6 — Categorized House Analysis</h2>
            {sections if sections else '<p class="note">No significant house placements detected.</p>'}
        </div>
        """

    # ── Step 7: Karmic Axis ──────────────────────────────────────────────────

    def _step7_karmic(self) -> str:
        """Step 7: Rahu/Ketu node analysis."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}

        _RASHI_NAMES: dict[str, str] = {
            "MESHA": "Aries",
            "VRISHABHA": "Taurus",
            "MITHUNA": "Gemini",
            "KARKA": "Cancer",
            "SIMHA": "Leo",
            "KANYA": "Virgo",
            "TULA": "Libra",
            "VRISHCHIKA": "Scorpio",
            "DHANUSHA": "Sagittarius",
            "MAKARA": "Capricorn",
            "KUMBHA": "Aquarius",
            "MEENA": "Pisces",
        }

        rahu_detail = pd.get("RAHU", {})
        ketu_detail = pd.get("KETU", {})
        rahu_sign = _RASHI_NAMES.get(rahu_detail.get("sign", ""), rahu_detail.get("sign", "—"))
        ketu_sign = _RASHI_NAMES.get(ketu_detail.get("sign", ""), ketu_detail.get("sign", "—"))
        rahu_deg = rahu_detail.get("degree_in_sign", 0)
        ketu_deg = ketu_detail.get("degree_in_sign", 0)
        rahu_dignity = dm.get("RAHU", "—")
        ketu_dignity = dm.get("KETU", "—")

        if rahu_sign == "—" and ketu_sign == "—":
            return """
            <div class="section-page">
                <h2>Step 7 — Karmic Axis</h2>
                <p class="note">Karmic axis data is not available for this chart.</p>
            </div>
            """

        narrative = (
            f"The karmic axis runs from <strong>{ketu_sign}</strong> (past-life gifts, comfort zone) "
            f"to <strong>{rahu_sign}</strong> (evolutionary direction, growth area). "
            f"Ketu in {ketu_sign} indicates innate talents and instinctive understanding. "
            f"Rahu in {rahu_sign} points to the unfamiliar territory offering the greatest growth. "
            f"This axis creates tension between the familiar and the aspirational — "
            f"the native's life journey involves gradually integrating Rahu's qualities "
            f"while honoring Ketu's natural gifts."
        )

        return f"""
        <div class="section-page">
            <h2>Step 7 — Karmic Axis</h2>
            <div class="karmic-grid">
                <div class="karmic-card karmic-ketu">
                    <div class="karmic-icon">☋</div>
                    <div class="karmic-label">Ketu (South Node)</div>
                    <div class="karmic-value">{ketu_sign} ({ketu_deg:.1f}°)</div>
                    <div class="karmic-sub">Past-Life Gifts • Comfort Zone</div>
                </div>
                <div class="karmic-arrow">→</div>
                <div class="karmic-card karmic-rahu">
                    <div class="karmic-icon">☊</div>
                    <div class="karmic-label">Rahu (North Node)</div>
                    <div class="karmic-value">{rahu_sign} ({rahu_deg:.1f}°)</div>
                    <div class="karmic-sub">Evolutionary Direction • Growth</div>
                </div>
            </div>
            <div class="narrative-block">{narrative}</div>
        </div>
        """

    # ── Step 7.5: Karmic Themes & Predictive Indicators ──────────────────────

    def _step75_karmic_insights(self) -> str:
        """Step 7.5: Deep karmic and predictive indicators with classical context."""
        from jrs.reporting.narrative_engine import generate_karmic_insights

        jre_facts = self._response_to_jre_facts()
        insights = generate_karmic_insights(jre_facts)

        if not insights:
            return """
            <div class="section-page">
                <h2>Step 7.5 — Karmic Themes & Predictive Indicators</h2>
                <div class="narrative-block">
                    No significant karmic challenge indicators were detected in this chart. The native's
                    planetary disposition suggests a relatively smooth karmic trajectory. General guidance
                    includes maintaining ethical conduct, practicing regular spiritual discipline, and
                    cultivating compassion as prescribed in BPHS and Phaladeepika.
                </div>
            </div>
            """

        sections = ""
        for insight in insights:
            condition = insight["condition"]
            interpretation = insight["interpretation"]
            remedy = insight["remedy"]

            sections += f"""
            <div class="karmic-insight-card">
                <div class="karmic-insight-header">
                    <span class="karmic-insight-badge">Karmic Indicator</span>
                    <strong>{condition}</strong>
                </div>
                <div class="narrative-block" style="margin-top: 6px;">
                    {interpretation}
                </div>
                <div class="remedy-block">
                    <strong>Classical Remedy:</strong> {remedy}
                </div>
            </div>
            """

        return f"""
        <div class="section-page">
            <h2>Step 7.5 — Karmic Themes & Predictive Indicators</h2>
            <p class="note">Challenging placements are framed constructively with classical remedial context.
            Every challenge carries the seed of spiritual growth and transformation.</p>
            {sections}
        </div>
        """

    # ── Step 8: Chronological Predictive Timelines ───────────────────────────

    def _step8_temporal(self) -> str:
        """Step 8: Current MD/AD/PD and upcoming major transit windows."""
        r = self.response
        active_with_temporal = [
            y
            for y in r.yogas
            if y.status in ("FORMED", "WEAKENED")
            and (y.dasha_multiplier is not None or y.transit_multiplier is not None)
        ]

        if not active_with_temporal:
            return """
            <div class="section-page">
                <h2>Step 8 — Chronological Predictive Timelines</h2>
                <p class="note">No temporal activation data available. This may indicate
                the evaluation was run without a target event timestamp.</p>
            </div>
            """

        rows = ""
        for yoga in active_with_temporal:
            dasha = f"{yoga.dasha_multiplier:.2f}×" if yoga.dasha_multiplier is not None else "—"
            transit = (
                f"{yoga.transit_multiplier:.2f}×" if yoga.transit_multiplier is not None else "—"
            )
            if yoga.dynamic_strength is not None:
                final = f"{yoga.dynamic_strength:.4f}"
            else:
                d = yoga.dasha_multiplier if yoga.dasha_multiplier is not None else 1.0
                t = yoga.transit_multiplier if yoga.transit_multiplier is not None else 1.0
                final = f"{yoga.static_strength * d * t:.4f}"

            timing_note = ""
            if yoga.dasha_multiplier is not None:
                if yoga.dasha_multiplier >= 1.0:
                    timing_note = "Active Dasha period"
                elif yoga.dasha_multiplier >= 0.5:
                    timing_note = "Approaching activation"
                else:
                    timing_note = "Dormant"

            rows += f"""
            <tr>
                <td>{yoga.yoga_name}</td>
                <td>{dasha}</td>
                <td>{transit}</td>
                <td class="final-score">{final}</td>
                <td>{timing_note}</td>
            </tr>
            """

        return f"""
        <div class="section-page">
            <h2>Step 8 — Chronological Predictive Timelines</h2>
            <p class="note">Vimshottari Dasha multipliers indicate the planetary period's alignment
            with each yoga. Transit Ashtakavarga (BAV) multipliers reflect current transit support.</p>
            <table class="data-table">
                <thead>
                    <tr><th>Yoga</th><th>Dasha Multiplier</th><th>Transit (BAV)</th><th>Final Score</th><th>Timing</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    # ── Step 9: Yoga Formation Analysis (Deep Dive) ──────────────────────────

    def _step9_yogas(self) -> str:
        """Step 9: For each yoga, show the exact 6-step math."""
        r = self.response
        sections = ""

        # Include FORMED, WEAKENED, and CANCELLED
        all_yogas = [y for y in r.yogas if y.status in ("FORMED", "WEAKENED", "CANCELLED")]

        if all_yogas:
            sections += "<h3>Active Yoga Formations</h3>"
            for yoga in all_yogas:
                citation = _CLASSICAL_CITATIONS.get(yoga.yoga_name, "")
                rule = _CLASSICAL_RULES.get(yoga.yoga_name, "Classical rule applied")
                planets_str = ", ".join(yoga.involved_planets) if yoga.involved_planets else "—"
                strength_pct = f"{yoga.static_strength:.0%}" if yoga.static_strength > 0 else "—"
                dynamic_str = (
                    f"{yoga.dynamic_strength:.2f}" if yoga.dynamic_strength is not None else "—"
                )

                status_class = (
                    "status-formed"
                    if yoga.status == "FORMED"
                    else ("status-weakened" if yoga.status == "WEAKENED" else "status-cancelled")
                )

                # Modifier evidence
                modifier_section = ""
                if yoga.cancellation_reason:
                    modifier_section = f"""
                    <div class="evidence-block" style="border-left: 3px solid #dc3545; padding-left: 8px;">
                        <strong>Modifier Impact:</strong> {yoga.cancellation_reason}
                        → {yoga.status} (-{"100" if yoga.status == "CANCELLED" else "50"}% strength)
                    </div>
                    """
                elif yoga.provenance.formation_evidence:
                    modifier_section = f"""
                    <div class="evidence-block">
                        <strong>Formation Evidence:</strong> {yoga.provenance.formation_evidence}
                    </div>
                    """

                # Chain impact
                chain_section = ""
                if yoga.chain_impact is not None:
                    chain_section = f"""
                    <div class="evidence-block">
                        <strong>Chain Impact:</strong> {yoga.chain_impact:+.2f}
                        (Dispositorship network effect)
                    </div>
                    """

                # Temporal activation
                temporal_section = ""
                if yoga.dasha_multiplier is not None or yoga.transit_multiplier is not None:
                    temporal_parts = []
                    if yoga.dasha_multiplier is not None:
                        temporal_parts.append(
                            f"Dasha Multiplier: <strong>{yoga.dasha_multiplier:.2f}×</strong>"
                        )
                    if yoga.transit_multiplier is not None:
                        temporal_parts.append(
                            f"Transit (BAV) Multiplier: <strong>{yoga.transit_multiplier:.2f}×</strong>"
                        )
                    temporal_section = f"""
                    <div class="evidence-block">
                        <strong>Temporal Activation:</strong> {" | ".join(temporal_parts)}
                    </div>
                    """

                # Final strength computation — explicit equation
                if yoga.status == "CANCELLED":
                    modifier_penalty = 0.0
                elif yoga.status == "WEAKENED":
                    modifier_penalty = 0.5
                else:
                    modifier_penalty = 1.0

                base_raw = yoga.static_strength
                dasha_v = yoga.dasha_multiplier if yoga.dasha_multiplier is not None else 1.0
                transit_v = yoga.transit_multiplier if yoga.transit_multiplier is not None else 1.0
                if yoga.status == "CANCELLED":
                    final_v = 0.0
                elif yoga.dynamic_strength is not None:
                    final_v = yoga.dynamic_strength
                else:
                    final_v = base_raw * modifier_penalty * dasha_v * transit_v

                eq_parts = [f"{base_raw:.2f} (Base)"]
                eq_parts.append(f"× {modifier_penalty:.2f} (Modifier Penalty)")
                if yoga.dasha_multiplier is not None:
                    eq_parts.append(f"× {dasha_v:.2f} (Dasha)")
                if yoga.transit_multiplier is not None:
                    eq_parts.append(f"× {transit_v:.2f} (Transit BAV)")

                strength_section = f"""
                    <div class="evidence-block">
                        <strong>Final Calculation:</strong>
                    </div>
                    <div class="strength-calc">
                        {"<br>".join(eq_parts)}
                        <br><strong>= {final_v:.4f}</strong>
                    </div>
                    """

                sections += f"""
                <div class="yoga-card">
                    <div class="yoga-header">
                        <span class="yoga-name">{yoga.yoga_name} Yoga</span>
                        <span class="{status_class}">{yoga.status}</span>
                    </div>
                    <div class="yoga-category">{yoga.category}</div>
                    <table class="detail-table">
                        <tr><td class="dt-label">Classical Rule</td><td>{rule}</td></tr>
                        <tr><td class="dt-label">Scripture Reference</td><td>{citation}</td></tr>
                        <tr><td class="dt-label">Involved Planets</td><td>{planets_str}</td></tr>
                        <tr><td class="dt-label">Outcome Domains</td><td>{", ".join(yoga.domains) if yoga.domains else "—"}</td></tr>
                        <tr><td class="dt-label">Static Strength</td><td>{strength_pct}</td></tr>
                        <tr><td class="dt-label">Dynamic Strength</td><td>{dynamic_str}</td></tr>
                    </table>
                    {modifier_section}
                    {chain_section}
                    {temporal_section}
                    {strength_section}
                </div>
                """

        # Not-formed summary
        other_yogas = [y for y in r.yogas if y.status not in ("FORMED", "WEAKENED", "CANCELLED")]
        if other_yogas:
            sections += "<h3>Not Formed</h3>"
            rows = ""
            for yoga in other_yogas:
                reason = yoga.cancellation_reason or "Classical conditions not met"
                rows += f"""
                <tr>
                    <td>{yoga.yoga_name}</td>
                    <td class="status-cancelled">{yoga.status}</td>
                    <td>{reason}</td>
                </tr>
                """
            sections += f"""
            <table class="data-table">
                <thead><tr><th>Yoga</th><th>Status</th><th>Reason</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """

        return f"""
        <div class="section-page">
            <h2>Step 9 — Yoga Formation Analysis (Deep Dive)</h2>
            <p class="note">Each yoga follows a 6-step evaluation: Classical Rule → Evidence →
            Modifier Pipeline → Chain Impact → Temporal Activation → Final Calculation.</p>
            {sections if sections else '<p class="note">No yogas met formation criteria.</p>'}
        </div>
        """

    # ── Remedial Measures (Appendix) ─────────────────────────────────────────

    def _remedial_measures(self) -> str:
        """Actionable Remedies section."""
        r = self.response
        pd = r.planet_details or {}
        dm = r.dignity_map or {}

        # Find most afflicted planet
        affliction_scores: dict[str, int] = {}
        for pname, pdata_raw in pd.items():
            if pname in ("RAHU", "KETU"):
                continue
            score = 0
            # Check from yogas if debilitated
            for y in r.yogas:
                if pname in y.involved_planets and y.status == "CANCELLED":
                    score += 3
                elif pname in y.involved_planets and y.status == "WEAKENED":
                    score += 1
            dignity = dm.get(pname, "")
            if dignity == "Debilitated":
                score += 3
            elif dignity == "Enemy":
                score += 1
            if score > 0:
                affliction_scores[pname] = score

        if not affliction_scores:
            return """
            <div class="section-page">
                <h2>Appendix — Actionable Remedies</h2>
                <div class="narrative-block">
                    No significantly afflicted classical planets were detected. General remedies include
                    daily prayer, charitable giving, and maintaining ethical conduct as prescribed in
                    Phaladeepika. Regular worship of the Ishta Devata (chosen deity) strengthens the
                    overall spiritual foundation.
                </div>
            </div>
            """

        sorted_planets = sorted(affliction_scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_planets[0][0]

        _REMEDIES: dict[str, dict[str, str]] = {
            "SUN": {"mantra": "Om Suryaya Namaha", "gemstone": "Ruby", "day": "Sunday"},
            "MOON": {"mantra": "Om Chandraya Namaha", "gemstone": "Pearl", "day": "Monday"},
            "MARS": {"mantra": "Om Angarakaya Namaha", "gemstone": "Red Coral", "day": "Tuesday"},
            "MERCURY": {"mantra": "Om Budhaya Namaha", "gemstone": "Emerald", "day": "Wednesday"},
            "JUPITER": {
                "mantra": "Om Gurave Namaha",
                "gemstone": "Yellow Sapphire",
                "day": "Thursday",
            },
            "VENUS": {"mantra": "Om Shukraya Namaha", "gemstone": "Diamond", "day": "Friday"},
            "SATURN": {
                "mantra": "Om Shanicharaya Namaha",
                "gemstone": "Blue Sapphire",
                "day": "Saturday",
            },
        }

        remedy = _REMEDIES.get(primary, {})
        remedy_items = ""
        if remedy.get("mantra"):
            remedy_items += f"<li><strong>Mantra:</strong> Chant '{remedy['mantra']}' 108 times on {remedy.get('day', 'the planet day')}s.</li>"
        if remedy.get("gemstone"):
            remedy_items += f"<li><strong>Gemstone:</strong> {remedy['gemstone']} — consult a qualified Vedic astrologer before wearing.</li>"
        remedy_items += (
            "<li><strong>Charity:</strong> Donate to those in need on the planet's day.</li>"
        )
        remedy_items += "<li><strong>Classical Remedy:</strong> Visit the relevant temple and perform puja as prescribed in BPHS.</li>"

        return f"""
        <div class="section-page">
            <h2>Appendix — Actionable Remedies</h2>
            <div class="narrative-block">
                The most afflicted planet is <strong>{primary}</strong>. Classical texts recommend specific
                remedial measures to mitigate negative effects and channel this planet's energy constructively.
            </div>
            <ul class="remedy-list">
                {remedy_items}
            </ul>
        </div>
        """

    # ── Full HTML Assembly ───────────────────────────────────────────────────

    def _build_full_html(self) -> str:
        """Build the complete HTML document with Macro-to-Micro flow.

        Layout: Summary → Life Arenas → Yogas → Remedies → Appendix (Technical).
        """
        r = self.response

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>JRE Comprehensive Report: {r.subject}</title>
<style>
    @page {{
        size: A4;
        margin: 2cm 2.5cm;
        @bottom-center {{
            content: "JRE {r.engine_version} — Page " counter(page);
            font-size: 8pt;
            color: #8a94a6;
        }}
    }}
    @page :first {{
        margin-top: 3cm;
        @bottom-center {{ content: none; }}
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Tamil', 'Noto Sans Malayalam', 'Noto Sans Telugu', 'Noto Sans Kannada', 'Noto Sans Bengali', 'Noto Sans Gujarati', 'Noto Sans Gurmukhi', 'Noto Sans Oriya', 'Helvetica Neue', 'Arial', sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #e6dfd3;
        background: #0c0f1d;
    }}

    /* ── Section Pages ── */
    .section-page {{
        page-break-before: always;
        padding-top: 0.5cm;
    }}
    .section-page:first-child {{
        page-break-before: avoid;
    }}

    /* ── Headings ── */
    h2 {{
        font-family: 'Georgia', serif;
        font-size: 14pt;
        color: #c5a880;
        border-bottom: 2px solid #c5a880;
        padding-bottom: 4px;
        margin: 0 0 0.5cm 0;
    }}
    h3 {{
        font-family: 'Georgia', serif;
        font-size: 11pt;
        color: #e6dfd3;
        margin: 0.5cm 0 0.3cm 0;
    }}

    /* ── Tables ── */
    .data-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.4cm 0 0.6cm 0;
        font-size: 9pt;
    }}
    .data-table th {{
        background: #1a1423;
        color: #c5a880;
        padding: 6px 8px;
        text-align: left;
        font-size: 8.5pt;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        border-bottom: 1px solid rgba(197,168,128,0.3);
    }}
    .data-table td {{
        padding: 5px 8px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        color: #e6dfd3;
    }}
    .data-table tr:nth-child(even) {{
        background: rgba(255,255,255,0.03);
    }}
    .dt-label {{
        font-weight: bold;
        color: #8a94a6;
        width: 150px;
        white-space: nowrap;
    }}
    .detail-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 4px 0;
        font-size: 9pt;
    }}
    .detail-table td {{
        padding: 3px 8px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        color: #e6dfd3;
    }}

    /* ── Bars ── */
    .bar-container {{
        width: 100%;
        height: 16px;
        background: rgba(255,255,255,0.06);
        border-radius: 3px;
        overflow: hidden;
    }}
    .bar-fill {{
        height: 100%;
        border-radius: 3px;
    }}
    .bar-count {{
        font-weight: bold;
        text-align: center;
        width: 30px;
        color: #c5a880;
    }}

    /* ── Two Column Layout ── */
    .two-col {{
        display: flex;
        gap: 1cm;
    }}
    .two-col > div {{
        flex: 1;
    }}

    /* ── Triad Grid ── */
    .triad-grid {{
        display: flex;
        gap: 0.5cm;
        margin: 0.5cm 0;
    }}
    .triad-card {{
        flex: 1;
        text-align: center;
        padding: 12px;
        border: 1px solid rgba(197,168,128,0.2);
        border-radius: 8px;
        background: rgba(26,20,35,0.6);
    }}
    .triad-icon {{
        font-size: 20pt;
        color: #c5a880;
        margin-bottom: 4px;
    }}
    .triad-title {{
        font-size: 9pt;
        color: #8a94a6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .triad-value {{
        font-family: 'Georgia', serif;
        font-size: 13pt;
        font-weight: bold;
        color: #c5a880;
        margin: 4px 0;
    }}
    .triad-sub {{
        font-size: 8pt;
        color: #8a94a6;
    }}

    /* ── Karmic Grid ── */
    .karmic-grid {{
        display: flex;
        align-items: center;
        gap: 0.5cm;
        margin: 0.5cm 0;
    }}
    .karmic-card {{
        flex: 1;
        text-align: center;
        padding: 12px;
        border-radius: 6px;
    }}
    .karmic-ketu {{
        background: rgba(139,92,246,0.1);
        border: 1px solid rgba(139,92,246,0.25);
    }}
    .karmic-rahu {{
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.2);
    }}
    .karmic-arrow {{
        font-size: 24pt;
        color: #c5a880;
    }}
    .karmic-icon {{ font-size: 18pt; color: #c5a880; }}
    .karmic-label {{ font-size: 8pt; color: #8a94a6; text-transform: uppercase; }}
    .karmic-value {{ font-family: 'Georgia', serif; font-size: 12pt; font-weight: bold; color: #c5a880; margin: 4px 0; }}
    .karmic-sub {{ font-size: 8pt; color: #8a94a6; }}

    /* ── Narrative ── */
    .narrative-block {{
        margin: 0.5cm 0;
        padding: 12px 16px;
        background: rgba(26,20,35,0.4);
        border-left: 3px solid #c5a880;
        border-radius: 0 6px 6px 0;
        font-size: 9.5pt;
        line-height: 1.6;
        color: #e6dfd3;
    }}

    /* ── Yoga Cards ── */
    .yoga-card {{
        border: 1px solid rgba(197,168,128,0.2);
        border-radius: 8px;
        padding: 10px 14px;
        margin: 0.4cm 0;
        background: rgba(26,20,35,0.4);
        page-break-inside: avoid;
    }}
    .yoga-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }}
    .yoga-name {{ font-family: 'Georgia', serif; font-size: 11pt; font-weight: bold; color: #e6dfd3; }}
    .yoga-category {{ font-size: 8pt; color: #8a94a6; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
    .status-formed {{ background: rgba(16,185,129,0.15); color: #34d399; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }}
    .status-weakened {{ background: rgba(234,179,8,0.15); color: #facc15; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }}
    .status-cancelled {{ background: rgba(239,68,68,0.15); color: #f87171; padding: 2px 8px; border-radius: 3px; font-size: 8pt; font-weight: bold; }}

    /* ── Evidence & Strength ── */
    .evidence-block {{ font-size: 9pt; padding: 4px 0; border-top: 1px dashed rgba(197,168,128,0.2); margin-top: 4px; color: #e6dfd3; }}
    .strength-calc {{
        font-family: 'Courier New', monospace;
        font-size: 8.5pt;
        background: rgba(197,168,128,0.06);
        padding: 6px 10px;
        border-radius: 3px;
        margin-top: 4px;
        border-left: 3px solid #8B0000;
    }}
    .final-score {{ font-weight: bold; color: #8B0000; }}

    /* ── Dignity Badges ── */
    .dignity-badge {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 8pt;
        font-weight: bold;
    }}
    .dignity-exalted {{ background: #d4edda; color: #155724; }}
    .dignity-moolatrikona {{ background: #cce5ff; color: #004085; }}
    .dignity-own-sign {{ background: #d1ecf1; color: #0c5460; }}
    .dignity-friendly {{ background: #e2e3e5; color: #383d41; }}
    .dignity-neutral {{ background: #f8f9fa; color: #6c757d; }}
    .dignity-enemy {{ background: #fff3cd; color: #856404; }}
    .dignity-debilitated {{ background: #f8d7da; color: #721c24; }}

    /* ── House Domain ── */
    .house-domain {{
        margin: 0.3cm 0;
        padding: 8px 12px;
        border-left: 3px solid #8B0000;
        background: #fafafa;
        border-radius: 0 4px 4px 0;
    }}

    /* ── Remedies ── */
    .remedy-list {{
        margin: 0.5cm 0;
        padding-left: 1.5cm;
    }}
    .remedy-list li {{
        margin: 4px 0;
        font-size: 9.5pt;
    }}

    /* ── Utilities ── */
    .note {{ font-size: 8.5pt; color: #888; font-style: italic; margin: 0.2cm 0; }}
    .planet-name {{ font-weight: bold; }}
    code {{ font-family: 'Courier New', monospace; font-size: 9pt; background: #f0f0f0; padding: 1px 4px; border-radius: 2px; }}

    .warning-box {{
        max-width: 500px;
        margin: 0.5cm 0;
        padding: 12px 16px;
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 4px;
        font-size: 9pt;
        color: #664d03;
    }}

    .disclaimer-box {{
        margin-top: 1cm;
        padding: 10px 14px;
        background: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 8pt;
        color: #666;
    }}

    .birth-data-grid {{
        margin: 0.5cm 0;
    }}

    /* ── House Interpretations (Phase I7) ── */
    .house-interpretation {{
        margin: 0.4cm 0;
        padding: 8px 12px;
        border-left: 3px solid #c5a880;
        background: rgba(26,20,35,0.4);
        border-radius: 0 6px 6px 0;
        page-break-inside: avoid;
    }}
    .house-interpretation h3 {{
        font-family: 'Georgia', serif;
        font-size: 10pt;
        color: #e6dfd3;
        margin-bottom: 4px;
    }}

    /* ── Aspect Items ── */
    .aspect-item {{
        margin: 0.3cm 0;
        padding: 8px 12px;
        border-left: 3px solid #3b82f6;
        background: rgba(59,130,246,0.06);
        border-radius: 0 6px 6px 0;
        page-break-inside: avoid;
    }}
    .aspect-header {{
        font-size: 9.5pt;
        color: #e6dfd3;
    }}

    /* ── Karmic Insight Cards ── */
    .karmic-insight-card {{
        border: 1px solid rgba(197,168,128,0.2);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 0.5cm 0;
        background: rgba(26,20,35,0.4);
        page-break-inside: avoid;
    }}
    .karmic-insight-header {{
        font-size: 10pt;
        margin-bottom: 6px;
    }}
    .karmic-insight-badge {{
        display: inline-block;
        background: rgba(197,168,128,0.2);
        color: #c5a880;
        font-size: 7.5pt;
        padding: 2px 6px;
        border-radius: 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 6px;
    }}
    .remedy-block {{
        margin-top: 8px;
        padding: 8px 12px;
        background: rgba(16,185,129,0.06);
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 4px;
        font-size: 9pt;
        color: #34d399;
    }}

    /* ── Appendix Header ── */
    .appendix-header {{
        font-family: 'Georgia', serif;
        font-size: 12pt;
        color: #8a94a6;
        border-top: 2px solid rgba(138,148,166,0.3);
        padding-top: 0.5cm;
        margin-top: 1cm;
    }}
</style>
</head><body>

<!-- ═══ SECTION 1: EXECUTIVE SUMMARY ═══ -->
{self._step1_birth_data()}

{self._step2_elements()}

{self._step3_triad()}

<!-- ═══ SECTION 2: LIFE ARENAS ═══ -->
{self._step35_house_placements()}

{self._step36_nakshatras()}

{self._step37_aspect_themes()}

{self._step4_dignities()}

{self._step6_houses()}

<!-- ═══ SECTION 3: YOGA ANALYSIS ═══ -->
{self._step9_yogas()}

<!-- ═══ SECTION 4: ACTIONABLE REMEDIES ═══ -->
{self._remedial_measures()}

<!-- ═══ APPENDIX: TECHNICAL CALCULATIONS ═══ -->
<div class="section-page">
<h2 class="appendix-header">Appendix: Technical Calculations</h2>
<p style="font-size: 9pt; color: #8a94a6; margin-bottom: 0.5cm;">Detailed astronomical data, karmic indicators, temporal activation, and aspect analysis for expert review.</p>
</div>

{self._step7_karmic()}

{self._step75_karmic_insights()}

{self._step8_temporal()}

{self._step5_aspects()}

</body>
</html>"""

    def generate_pdf(self) -> bytes:
        """Generate the PDF as bytes using weasyprint."""
        from weasyprint import HTML  # type: ignore[import-not-found]

        html_content = self._build_full_html()
        doc = HTML(string=html_content)
        pdf_bytes: bytes = doc.write_pdf()
        return pdf_bytes

    def generate_html(self) -> str:
        """Generate the HTML report as a string."""
        return self._build_full_html()
