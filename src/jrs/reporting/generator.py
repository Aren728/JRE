"""JRE Reporting — Human-readable report generator.

Transforms EvaluationResponse JSON into structured, domain-grouped
astrological reports in Markdown and HTML formats.

NO engine logic — pure presentation layer.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from jrs.api.schemas import EvaluationResponse, YogaResult


# ── Domain Display Names ────────────────────────────────────────────────────

_DOMAIN_DISPLAY: dict[str, str] = {
    "CAREER_PROMINENCE": "Career & Professional Life",
    "POLITICAL_POWER": "Leadership & Political Influence",
    "WEALTH_ACCUMULATION": "Wealth & Financial Prosperity",
    "BUSINESS_ACUMEN": "Business & Entrepreneurship",
    "RELATIONSHIP_HARMONY": "Relationships & Partnerships",
    "DOMESTIC_HARMONY": "Home & Family Life",
    "INTELLECTUAL_EXCELLENCE": "Intellect & Learning",
    "WISDOM_ACCUMULATION": "Wisdom & Spiritual Growth",
    "TEACHING_ABILITY": "Teaching & Mentoring",
    "COMMUNICATION_SKILLS": "Communication & Expression",
    "ARTISTIC_EXCELLENCE": "Arts & Creative Expression",
    "PUBLIC_RECOGNITION": "Fame & Public Recognition",
    "SOCIAL_STATUS": "Social standing & Influence",
    "MENTAL_STRENGTH": "Mental Fortitude & Resilience",
    "LEADERSHIP": "Leadership & Initiative",
    "GENERAL_IMPROVEMENT": "General Well-being",
    "RECOVERY_FROM_ADVERSITY": "Recovery & Resilience",
    "CRISIS_MANAGEMENT": "Crisis Navigation",
    "EMOTIONAL_STABILITY": "Emotional Balance",
}

# Domain grouping order for the report
_DOMAIN_SECTIONS: list[str] = [
    "CAREER_PROMINENCE",
    "POLITICAL_POWER",
    "LEADERSHIP",
    "WEALTH_ACCUMULATION",
    "BUSINESS_ACUMEN",
    "INTELLECTUAL_EXCELLENCE",
    "WISDOM_ACCUMULATION",
    "TEACHING_ABILITY",
    "COMMUNICATION_SKILLS",
    "ARTISTIC_EXCELLENCE",
    "PUBLIC_RECOGNITION",
    "SOCIAL_STATUS",
    "RELATIONSHIP_HARMONY",
    "DOMESTIC_HARMONY",
    "MENTAL_STRENGTH",
    "EMOTIONAL_STABILITY",
    "GENERAL_IMPROVEMENT",
    "RECOVERY_FROM_ADVERSITY",
    "CRISIS_MANAGEMENT",
]


# ── Yoga Descriptions ───────────────────────────────────────────────────────

_YOGA_DESCRIPTIONS: dict[str, str] = {
    "Gajakesari": (
        "Jupiter in a Kendra (angular house) from the Moon. This classical yoga "
        "indicates wisdom, prosperity, and lasting influence. The native tends to "
        "be respected, generous, and intellectually gifted."
    ),
    "Raja": (
        "A Kendra lord (angular house ruler) connected with a Trikona lord "
        "(trinal house ruler) through conjunction or mutual aspect. This is one "
        "of the most powerful yogas for success, authority, and achievement."
    ),
    "Dhana": (
        "A wealth yoga formed when the lords of the 2nd, 5th, 9th, or 11th "
        "houses are connected. Indicates strong potential for financial prosperity "
        "and material accumulation."
    ),
    "Budhaditya": (
        "Sun and Mercury conjunct in the same sign. Named after Budha (Mercury), "
        "this yoga sharpens intellect, communication, and analytical ability. "
        "Common in scholars, writers, and professionals."
    ),
    "Vipareeta Raja": (
        "A dusthana lord (6th, 8th, or 12th house ruler) placed in another "
        "dusthana. Paradoxically, this 'reverse Raja yoga' brings success through "
        "overcoming adversity, crisis management, and unexpected windfalls."
    ),
    "Malavya": (
        "Venus in own sign or exaltation in a Kendra house. One of the Pancha "
        "Mahapurusha yogas. Indicates artistic talent, beauty, luxury, and strong "
        "relationships. The native often excels in creative fields."
    ),
    "Ruchaka": (
        "Mars in own sign or exaltation in a Kendra house. One of the Pancha "
        "Mahapurusha yogas. Indicates courage, military prowess, leadership, and "
        "physical vitality. The native is decisive and energetic."
    ),
    "Bhadra": (
        "Mercury in own sign or exaltation in a Kendra house. One of the Pancha "
        "Mahapurusha yogas. Indicates intelligence, eloquence, and business acumen. "
        "The native is skilled in communication and trade."
    ),
    "Hamsa": (
        "Jupiter in own sign or exaltation in a Kendra house. One of the Pancha "
        "Mahapurusha yogas. Indicates spiritual wisdom, teaching ability, and moral "
        "authority. The native is often drawn to philosophy or religion."
    ),
    "Sasa": (
        "Saturn in own sign or exaltation in a Kendra house. One of the Pancha "
        "Mahapurusha yogas. Indicates discipline, organizational ability, and "
        "enduring influence. The native builds lasting structures and institutions."
    ),
    "Sunapha": (
        "A benefic planet (Venus, Jupiter, Mercury, or Moon) positioned 2nd from "
        "the Moon. One of the Upapurusha yogas. Indicates good character, wealth, "
        "and social respect."
    ),
    "Anapha": (
        "A benefic planet positioned 12th from the Moon. One of the Upapurusha "
        "yogas. Indicates artistic inclination, luxury, and foreign connections."
    ),
    "Dhudhara": (
        "A benefic planet positioned 2nd and 12th from the Moon simultaneously. "
        "One of the Upapurusha yogas. Indicates prosperity, good health, and "
        "strong social standing."
    ),
    "Amala": (
        "A benefic planet in the 10th house from the Lagna or Moon. One of the "
        "Upapurusha yogas. Indicates virtuous career, good reputation, and "
        "meritorious deeds."
    ),
    "Neecha Bhanga": (
        "Cancellation of debilitation. When a debilitated planet's debilitation "
        "sign lord is in a Kendra from the Lagna, or conjunct the Lagna lord, "
        "the debilitation is cancelled. This restores strength and brings "
        "unexpected success."
    ),
    "Saraswati": (
        "Jupiter, Venus, and Mercury all in Kendra or Trikona from the Lagna, "
        "or Jupiter and Venus in the 2nd house. Indicates exceptional learning, "
        "artistic talent, and scholarly achievement. Named after Saraswati, "
        "goddess of knowledge."
    ),
}

# Status display labels
_STATUS_LABELS: dict[str, str] = {
    "FORMED": "Active",
    "WEAKENED": "Present (weakened)",
    "CANCELLED": "Cancelled",
}


# ── Report Generator ────────────────────────────────────────────────────────


class ReportGenerator:
    """Generates human-readable astrological reports from EvaluationResponse."""

    def __init__(self, response: EvaluationResponse) -> None:
        """Initialize with an evaluation response.

        Args:
            response: The EvaluationResponse from the API pipeline.
        """
        self.response = response
        self._grouped = self._group_yogas_by_domain()

    def _group_yogas_by_domain(self) -> dict[str, list[YogaResult]]:
        """Group yogas by their outcome domains.

        Returns:
            Dictionary mapping domain names to lists of YogaResult.
        """
        grouped: dict[str, list[YogaResult]] = defaultdict(list)
        for yoga in self.response.yogas:
            if yoga.status == "CANCELLED":
                continue  # Skip cancelled yogas in domain grouping
            for domain in yoga.domains:
                grouped[domain].append(yoga)
        return dict(grouped)

    def _get_yoga_description(self, yoga_name: str) -> str:
        """Get plain-english description for a yoga."""
        return _YOGA_DESCRIPTIONS.get(
            yoga_name,
            f"{yoga_name} yoga detected in the chart."
        )

    def _format_planets(self, planets: list[str]) -> str:
        """Format planet names for display."""
        return ", ".join(planets) if planets else "—"

    def _format_strength(self, yoga: YogaResult) -> str:
        """Format strength information for a yoga."""
        parts = []
        if yoga.static_strength > 0:
            if yoga.static_strength >= 0.8:
                label = "Strong"
            elif yoga.static_strength >= 0.5:
                label = "Moderate"
            else:
                label = "Mild"
            parts.append(f"{label} ({yoga.static_strength:.0%})")

        if yoga.dynamic_strength is not None:
            parts.append(f"Dynamic: {yoga.dynamic_strength:.2f}")

        return " | ".join(parts) if parts else ""

    # ── Markdown Renderer ───────────────────────────────────────────────────

    def generate_markdown(self) -> str:
        """Generate a well-formatted Markdown report.

        Returns:
            Markdown string with headers, bullet points, and structured content.
        """
        lines: list[str] = []
        r = self.response

        # ── Title ──
        lines.append(f"# Jyotish Yoga Report: {r.subject}")
        lines.append("")
        if r.evaluation_id:
            lines.append(f"**Evaluation ID:** `{r.evaluation_id}`")
        lines.append(f"**Lagna (Ascendant):** {r.lagna}")
        if r.moon_nakshatra:
            lines.append(f"**Moon Nakshatra:** {r.moon_nakshatra}")
        lines.append(f"**Yogas Detected:** {r.yoga_count} "
                     f"({r.formed_count} active)")
        if r.engine_version:
            lines.append(f"**Engine Version:** {r.engine_version}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ── Executive Summary ──
        lines.append("## Executive Summary")
        lines.append("")
        active_yogas = [y for y in r.yogas if y.status == "FORMED"]
        weakened_yogas = [y for y in r.yogas if y.status == "WEAKENED"]
        cancelled_yogas = [y for y in r.yogas if y.status == "CANCELLED"]

        if active_yogas:
            names = ", ".join(y.yoga_name for y in active_yogas)
            lines.append(f"**Active yogas:** {names}")
        if weakened_yogas:
            names = ", ".join(y.yoga_name for y in weakened_yogas)
            lines.append(f"**Weakened yogas:** {names}")
        if cancelled_yogas:
            names = ", ".join(y.yoga_name for y in cancelled_yogas)
            lines.append(f"**Cancelled yogas:** {names}")
        lines.append("")

        # ── Domain Sections ──
        for domain_key in _DOMAIN_SECTIONS:
            if domain_key not in self._grouped:
                continue

            yogas = self._grouped[domain_key]
            section_title = _DOMAIN_DISPLAY.get(domain_key, domain_key)
            lines.append(f"## {section_title}")
            lines.append("")

            for yoga in yogas:
                status_label = _STATUS_LABELS.get(yoga.status, yoga.status)
                planets_str = self._format_planets(yoga.involved_planets)
                strength_str = self._format_strength(yoga)

                lines.append(f"### {yoga.yoga_name} — {status_label}")
                lines.append("")
                lines.append(f"**Planets:** {planets_str}")
                if yoga.category:
                    lines.append(f"**Category:** {yoga.category}")
                if strength_str:
                    lines.append(f"**Strength:** {strength_str}")
                lines.append("")

                # Description
                desc = self._get_yoga_description(yoga.yoga_name)
                lines.append(f"> {desc}")
                lines.append("")

                # Temporal context
                if yoga.dasha_multiplier is not None:
                    if yoga.dasha_multiplier >= 1.0:
                        timing = "Currently active (Dasha alignment)"
                    else:
                        timing = "Currently dormant (no Dasha alignment)"
                    lines.append(f"**Timing:** {timing}")
                    lines.append("")

            lines.append("---")
            lines.append("")

        # ── All Yogas Summary Table ──
        lines.append("## Complete Yoga Summary")
        lines.append("")
        lines.append("| Yoga | Status | Planets | Strength |")
        lines.append("|------|--------|---------|----------|")
        for yoga in r.yogas:
            status = _STATUS_LABELS.get(yoga.status, yoga.status)
            planets = self._format_planets(yoga.involved_planets)
            strength = f"{yoga.static_strength:.0%}" if yoga.static_strength > 0 else "—"
            lines.append(f"| {yoga.yoga_name} | {status} | {planets} | {strength} |")
        lines.append("")

        # ── Methodology Note ──
        lines.append("---")
        lines.append("")
        lines.append("## Methodology Note")
        lines.append("")
        lines.append("This report is generated by the Jyotish Reasoning Engine (JRE), "
                     "a deterministic astronomical pipeline based on classical BPHS "
                     "(Brihat Parashara Hora Shastra) and Phaladeepika principles. "
                     "All calculations use sidereal (Lahiri ayanamsa) coordinates "
                     "and Whole-Sign house system.")
        lines.append("")
        lines.append("Yoga detection follows classical conditions exactly as described "
                     "in the source texts. Modifier evaluation applies a 5-tier priority "
                     "hierarchy (combustion, debilitation, planetary war, retrograde, "
                     "node influence). D9 (Navamsha) confirmation provides additional "
                     "validation.")
        lines.append("")

        # ── Legal Disclaimer ──
        lines.append("---")
        lines.append("")
        disclaimer = getattr(r, 'disclaimer', '') or (
            "DISCLAIMER: This output is a computational interpretation based on "
            "classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided "
            "for informational and research purposes only. It does not constitute "
            "medical, financial, legal, or guaranteed predictive advice."
        )
        lines.append(f"*{disclaimer}*")
        lines.append("")

        return "\n".join(lines)

    # ── HTML Renderer ───────────────────────────────────────────────────────

    def generate_html(self) -> str:
        """Generate a styled HTML report.

        Returns:
            HTML string with inline CSS, suitable for browser viewing or PDF conversion.
        """
        r = self.response
        md = self.generate_markdown()

        # Simple markdown-to-HTML conversion for the report
        html_body = self._markdown_to_html(md)

        disclaimer = getattr(r, 'disclaimer', '') or (
            "DISCLAIMER: This output is a computational interpretation based on "
            "classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided "
            "for informational and research purposes only. It does not constitute "
            "medical, financial, legal, or guaranteed predictive advice."
        )
        eval_id = getattr(r, 'evaluation_id', '')
        eval_line = f'<p class="meta">Evaluation ID: <code>{eval_id}</code></p>' if eval_id else ''

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jyotish Yoga Report: {r.subject}</title>
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
            background: #fafafa;
        }}
        h1 {{
            color: #8B0000;
            border-bottom: 2px solid #8B0000;
            padding-bottom: 0.5rem;
        }}
        h2 {{
            color: #4A0E0E;
            margin-top: 2rem;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.3rem;
        }}
        h3 {{
            color: #6B3A3A;
            margin-top: 1.5rem;
        }}
        strong {{
            color: #222;
        }}
        blockquote {{
            border-left: 3px solid #8B0000;
            margin: 1rem 0;
            padding: 0.5rem 1rem;
            background: #f5f0f0;
            font-style: italic;
            color: #555;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.5rem 0.75rem;
            text-align: left;
        }}
        th {{
            background: #8B0000;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 2rem 0;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
{eval_line}
{html_body}
    <div style="margin-top: 2rem; padding: 1rem; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; font-size: 0.85em; color: #664d03;">
        <strong>Disclaimer:</strong> {disclaimer}
    </div>
</body>
</html>"""

    def _markdown_to_html(self, md: str) -> str:
        """Convert markdown to simple HTML (headers, bold, blockquotes, tables)."""
        lines = md.split("\n")
        html_lines: list[str] = []
        in_table = False
        in_blockquote = False

        for line in lines:
            stripped = line.strip()

            # Table handling
            if stripped.startswith("|") and stripped.endswith("|"):
                if not in_table:
                    in_table = True
                    html_lines.append("<table>")
                    # Check if this is a header row (next line should be separator)
                    cells = [c.strip() for c in stripped.split("|")[1:-1]]
                    html_lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
                    continue
                elif "---" in stripped:
                    continue  # Skip separator row
                else:
                    cells = [c.strip() for c in stripped.split("|")[1:-1]]
                    html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
                    continue
            elif in_table:
                html_lines.append("</table>")
                in_table = False

            # Blockquote
            if stripped.startswith("> "):
                if not in_blockquote:
                    html_lines.append("<blockquote>")
                    in_blockquote = True
                html_lines.append(f"<p>{stripped[2:]}</p>")
                continue
            elif in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False

            # Headers
            if stripped.startswith("# "):
                html_lines.append(f"<h1>{stripped[2:]}</h1>")
            elif stripped.startswith("## "):
                html_lines.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith("### "):
                html_lines.append(f"<h3>{stripped[4:]}</h3>")
            elif stripped == "---":
                html_lines.append("<hr>")
            elif stripped == "":
                html_lines.append("")
            else:
                # Bold text
                import re
                text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
                html_lines.append(f"<p>{text}</p>")

        if in_table:
            html_lines.append("</table>")
        if in_blockquote:
            html_lines.append("</blockquote>")

        return "\n".join(html_lines)
