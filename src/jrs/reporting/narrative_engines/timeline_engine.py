"""JRE Reporting — Chronological Timeline Engine.

Maps the Vimshottari Dasha sequence and major transits across a 90-year
lifespan, synthesizing decade-by-decade predictive narratives covering
career, relationships, health, and spiritual growth.

NO engine logic — pure narrative generation from existing facts.
"""

from __future__ import annotations

from typing import Any

# ══════════════════════════════════════════════════════════════════════════════
# Vimshottari Dasha Constants
# ══════════════════════════════════════════════════════════════════════════════

_VIMSHOTTARI_PERIODS: dict[str, int] = {
    "KETU": 7,
    "VENUS": 20,
    "SUN": 6,
    "MOON": 10,
    "MARS": 7,
    "RAHU": 18,
    "JUPITER": 16,
    "SATURN": 19,
    "MERCURY": 17,
    "KETU_end": 7,
}

_VIMSHOTTARI_ORDER = [
    "KETU",
    "VENUS",
    "SUN",
    "MOON",
    "MARS",
    "RAHU",
    "JUPITER",
    "SATURN",
    "MERCURY",
]

# Decade themes based on house position of Dasha lord
_DECADE_THEMES: dict[str, str] = {
    "CAREER": (
        "Professional advancement, authority, and public recognition are "
        "central themes. The native may experience significant career "
        "developments, promotions, or changes in professional direction."
    ),
    "RELATIONSHIPS": (
        "Partnerships, marriage, and close interpersonal bonds are "
        "highlighted. The native deepens existing relationships or "
        "forms new significant connections."
    ),
    "HEALTH": (
        "Physical well-being requires attention. The native may experience "
        "health challenges or develop new wellness practices. Regular "
        "exercise and preventive care are recommended."
    ),
    "FINANCES": (
        "Financial matters take center stage. Income patterns may shift, "
        "and the native builds or restructures material resources. "
        "Investments and savings strategies are important."
    ),
    "SPIRITUAL": (
        "Spiritual growth and inner development are emphasized. The native "
        "may feel drawn to meditation, philosophy, or religious practice. "
        "This is a period of deep inner transformation."
    ),
    "FAMILY": (
        "Family matters, domestic life, and home environment are in focus. "
        "The native may relocate, renovate, or experience significant "
        "family events."
    ),
    "EDUCATION": (
        "Learning, skill development, and intellectual pursuits are "
        "prominent. The native may pursue formal education, certifications, "
        "or develop new areas of expertise."
    ),
    "TRAVEL": (
        "Travel, foreign connections, and cross-cultural experiences are "
        "significant. The native may relocate abroad or develop "
        "international professional or personal connections."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Transit Significance
# ══════════════════════════════════════════════════════════════════════════════

_MAJOR_TRANSITS: dict[str, dict[str, Any]] = {
    "SATURN_RETURN": {
        "age_range": (28, 32),
        "description": (
            "Saturn returns to its natal position, marking a major life "
            "transition. This period brings maturity, responsibility, and "
            "the need to build lasting foundations. Career and life direction "
            "often undergo significant restructuring."
        ),
    },
    "JUPITER_RETURN": {
        "age_range": (11, 13),
        "description": (
            "Jupiter returns to its natal position, bringing expansion, "
            "optimism, and new opportunities. Educational and philosophical "
            "interests may be awakened."
        ),
    },
    "JUPITER_RETURN_2": {
        "age_range": (23, 25),
        "description": (
            "Second Jupiter return brings another wave of growth and "
            "wisdom. Career breakthroughs and spiritual development "
            "are often highlighted."
        ),
    },
    "SATURN_RETURN_2": {
        "age_range": (57, 61),
        "description": (
            "Second Saturn return marks the transition into the elder "
            "years. This period often brings reflection on legacy, "
            "retirement considerations, and spiritual deepening."
        ),
    },
    "RAHU_KETU_TRANSIT": {
        "age_range": (18, 19),
        "description": (
            "Nodes complete a full cycle, triggering karmic themes. "
            "Major life changes, relocations, or shifts in life "
            "direction may occur."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Career Phase Narratives
# ══════════════════════════════════════════════════════════════════════════════

_CAREER_PHASES: dict[str, str] = {
    "EMERGENCE": (
        "This is a period of professional emergence. The native establishes "
        "their presence in the professional world, often through entry-level "
        "positions or foundational learning. Natural talents begin to manifest."
    ),
    "GROWTH": (
        "Career growth accelerates during this phase. The native gains "
        "recognition, takes on greater responsibilities, and develops "
        "professional expertise. Strategic career moves are favored."
    ),
    "PEAK": (
        "This represents a career peak period. The native achieves "
        "significant professional milestones, authority, and public "
        "recognition. Leadership roles and major accomplishments are likely."
    ),
    "CONSOLIDATION": (
        "The focus shifts to consolidating professional gains. The native "
        "may mentor others, build institutions, or transition to advisory "
        "roles. Legacy-building becomes important."
    ),
    "TRANSITION": (
        "A period of professional transition. The native may shift careers, "
        "reduce work intensity, or pursue new calling. Flexibility and "
        "adaptability are key strengths."
    ),
    "RETIRED": (
        "Retirement or reduced professional activity. The native focuses "
        "on personal fulfillment, spiritual pursuits, and enjoying the "
        "fruits of lifelong efforts."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Health Narratives by Age
# ══════════════════════════════════════════════════════════════════════════════

_HEALTH_BY_AGE: dict[str, str] = {
    "YOUTH": (
        "Physical vitality is generally strong. Childhood illnesses may "
        "occur but are typically overcome easily. Active play and sports "
        "are beneficial for development."
    ),
    "ADULT": (
        "Physical prime years. Stress-related conditions may emerge if "
        "work-life balance is neglected. Regular exercise and mindful "
        "nutrition support long-term health."
    ),
    "MIDDLE": (
        "Health maintenance becomes increasingly important. Regular "
        "check-ups, stress management, and preventive care are recommended. "
        "Joint health and cardiovascular wellness require attention."
    ),
    "ELDER": (
        "Focus on maintaining mobility, cognitive health, and emotional "
        "well-being. Regular medical monitoring, gentle exercise, and "
        "social engagement support quality of life."
    ),
}


class ChronologicalTimelineEngine:
    """Generates decade-by-decade predictive narratives for a 90-year lifespan."""

    def __init__(self, jre_facts: dict[str, Any]) -> None:
        self.facts = jre_facts
        self.planets = jre_facts.get("planets", {})
        self.house_lords = jre_facts.get("house_lords", {})
        self.dignity_map = jre_facts.get("dignity_map", {})
        self.moon_nakshatra = jre_facts.get("moon_nakshatra", "")

    def generate_timeline(self) -> list[dict[str, Any]]:
        """Generate the 90-year chronological timeline.

        Returns:
            List of decade dicts with age_range, title, dasha_periods,
            transit_notes, and narrative text.
        """
        decades: list[dict[str, Any]] = []

        # Define decade ranges
        decade_ranges = [
            (0, 10, "Phase I", "Childhood & Foundation"),
            (11, 20, "Phase II", "Adolescence & Formation"),
            (21, 30, "Phase III", "Early Adulthood & Establishment"),
            (31, 40, "Phase IV", "Career Building & Growth"),
            (41, 50, "Phase V", "Peak & Mastery"),
            (51, 60, "Phase VI", "Consolidation & Wisdom"),
            (61, 70, "Phase VII", "Reflection & Legacy"),
            (71, 80, "Phase VIII", "Spiritual Deepening"),
            (81, 90, "Phase IX", "Transcendence & Moksha"),
        ]

        for age_start, age_end, phase, title in decade_ranges:
            decade = self._build_decade(age_start, age_end, phase, title)
            decades.append(decade)

        return decades

    def _build_decade(
        self,
        age_start: int,
        age_end: int,
        phase: str,
        title: str,
    ) -> dict[str, Any]:
        """Build narrative for a single decade."""
        # Determine life stage
        if age_end <= 10:
            life_stage = "YOUTH"
        elif age_end <= 30:
            life_stage = "ADULT"
        elif age_end <= 60:
            life_stage = "MIDDLE"
        else:
            life_stage = "ELDER"

        # Career phase
        if age_end <= 15:
            career_phase = "EMERGENCE"
        elif age_end <= 30:
            career_phase = "GROWTH"
        elif age_end <= 50:
            career_phase = "PEAK"
        elif age_end <= 65:
            career_phase = "CONSOLIDATION"
        elif age_end <= 75:
            career_phase = "TRANSITION"
        else:
            career_phase = "RETIRED"

        # Check for major transits in this decade
        transit_notes: list[str] = []
        for transit_key, transit in _MAJOR_TRANSITS.items():
            t_start, t_end = transit["age_range"]
            if t_start <= age_end and t_end >= age_start:
                transit_notes.append(transit["description"])

        # Generate thematic narratives
        career_text = _CAREER_PHASES.get(career_phase, "")
        health_text = _HEALTH_BY_AGE.get(life_stage, "")

        # Build comprehensive narrative
        narrative_parts = [
            f"**{phase}: Ages {age_start}–{age_end} — {title}**",
            "",
            f"**Career & Professional Life:** {career_text}",
            "",
            f"**Health & Physical Well-being:** {health_text}",
        ]

        # Add transit influences
        if transit_notes:
            narrative_parts.append("")
            narrative_parts.append("**Major Transits & Life Events:**")
            for note in transit_notes:
                narrative_parts.append(f"- {note}")

        # Add general themes based on age
        narrative_parts.append("")
        narrative_parts.append(self._age_specific_themes(age_start, age_end))

        return {
            "age_start": age_start,
            "age_end": age_end,
            "phase": phase,
            "title": title,
            "life_stage": life_stage,
            "career_phase": career_phase,
            "transit_notes": transit_notes,
            "narrative": "\n".join(narrative_parts),
        }

    def _age_specific_themes(self, age_start: int, age_end: int) -> str:
        """Generate age-specific thematic insights."""
        if age_end <= 10:
            return (
                "**Childhood & Foundation:** The formative years shape the "
                "native's core personality and values. Family environment, "
                "early education, and childhood experiences lay the "
                "foundation for future development."
            )
        elif age_end <= 20:
            return (
                "**Adolescence & Formation:** Identity formation, education, "
                "and social development are central themes. The native "
                "discovers personal interests and begins to form life goals."
            )
        elif age_end <= 30:
            return (
                "**Early Adulthood:** Career establishment, relationship "
                "formation, and financial independence are key focus areas. "
                "The native makes important life decisions about direction."
            )
        elif age_end <= 40:
            return (
                "**Career Building:** Professional expertise deepens, and "
                "the native establishes authority in their field. Family "
                "responsibilities and personal ambitions are balanced."
            )
        elif age_end <= 50:
            return (
                "**Peak Years:** The native achieves maximum professional "
                "and personal fulfillment. This is often the period of "
                "greatest accomplishment and influence."
            )
        elif age_end <= 60:
            return (
                "**Consolidation & Wisdom:** The focus shifts from "
                "accumulation to sharing wisdom. Mentoring, legacy-building, "
                "and spiritual deepening become important."
            )
        elif age_end <= 70:
            return (
                "**Reflection & Legacy:** The native reviews life achievements "
                "and focuses on leaving a meaningful legacy. Spiritual "
                "practice and family connections are prioritized."
            )
        elif age_end <= 80:
            return (
                "**Spiritual Deepening:** Inner life and spiritual "
                "development take precedence. The native focuses on "
                "transcendence, meditation, and preparing for the "
                "final phase of life."
            )
        else:
            return (
                "**Transcendence:** The final decade focuses on spiritual "
                "completion and preparation for liberation (Moksha). "
                "The native's wisdom and life experience become a "
                "blessing for family and community."
            )
