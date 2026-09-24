"""Nakshatra Exchange (Nakshatra Parivartana) Engine — Detection and readings.

Detects Nakshatra-level exchanges where:
  - Planet A occupies Planet B's Nakshatra
  - Planet B occupies Planet A's Nakshatra

Also provides Nakshatra Lord assignments for all planets in both
natal and transit charts.

All outputs are deterministic — no LLM, no randomness.
Reference: BPHS Ch 29-30 (Nakshatra effects), Phaladeepika Ch 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Nakshatra constants ─────────────────────────────────────────────────────

NAKSHATRA_ORDER: tuple[str, ...] = (
    "ASHWINI",
    "BHARANI",
    "KRITTIKA",
    "ROHINI",
    "MRIGASHIRA",
    "ARDRA",
    "PUNARVASU",
    "PUSHA",
    "ASHLESHA",
    "MAGHA",
    "PURVA_PHALGUNI",
    "UTTARA_PHALGUNI",
    "HASTA",
    "CHITRA",
    "SWATI",
    "VISHAKHA",
    "ANURADHA",
    "JYESHTHA",
    "MULA",
    "PURVA_ASHADHA",
    "UTTARA_ASHADHA",
    "SHRAVANA",
    "DHANISHTA",
    "SHATABHISHA",
    "PURVA_BHADRAPADA",
    "UTTARA_BHADRAPADA",
    "REVATI",
)

NAKSHATRA_NAMES: dict[str, str] = {
    "ASHWINI": "Ashwini",
    "BHARANI": "Bharani",
    "KRITTIKA": "Krittika",
    "ROHINI": "Rohini",
    "MRIGASHIRA": "Mrigashira",
    "ARDRA": "Ardra",
    "PUNARVASU": "Punarvasu",
    "PUSHA": "Pushya",
    "ASHLESHA": "Ashlesha",
    "MAGHA": "Magha",
    "PURVA_PHALGUNI": "Purva Phalguni",
    "UTTARA_PHALGUNI": "Uttara Phalguni",
    "HASTA": "Hasta",
    "CHITRA": "Chitra",
    "SWATI": "Swati",
    "VISHAKHA": "Vishakha",
    "ANURADHA": "Anuradha",
    "JYESHTHA": "Jyeshtha",
    "MULA": "Mula",
    "PURVA_ASHADHA": "Purva Ashadha",
    "UTTARA_ASHADHA": "Uttara Ashadha",
    "SHRAVANA": "Shravana",
    "DHANISHTA": "Dhanishta",
    "SHATABHISHA": "Shatabhisha",
    "PURVA_BHADRAPADA": "Purva Bhadrapada",
    "UTTARA_BHADRAPADA": "Uttara Bhadrapada",
    "REVATI": "Revati",
}

# ── Nakshatra Lords (classical assignment) ──────────────────────────────────

NAKSHATRA_LORDS: dict[str, str] = {
    "ASHWINI": "Ketu",
    "BHARANI": "Venus",
    "KRITTIKA": "Sun",
    "ROHINI": "Moon",
    "MRIGASHIRA": "Mars",
    "ARDRA": "Rahu",
    "PUNARVASU": "Jupiter",
    "PUSHA": "Saturn",
    "ASHLESHA": "Mercury",
    "MAGHA": "Ketu",
    "PURVA_PHALGUNI": "Venus",
    "UTTARA_PHALGUNI": "Sun",
    "HASTA": "Moon",
    "CHITRA": "Mars",
    "SWATI": "Rahu",
    "VISHAKHA": "Jupiter",
    "ANURADHA": "Saturn",
    "JYESHTHA": "Mercury",
    "MULA": "Ketu",
    "PURVA_ASHADHA": "Venus",
    "UTTARA_ASHADHA": "Sun",
    "SHRAVANA": "Moon",
    "DHANISHTA": "Mars",
    "SHATABHISHA": "Rahu",
    "PURVA_BHADRAPADA": "Jupiter",
    "UTTARA_BHADRAPADA": "Saturn",
    "REVATI": "Mercury",
}

# ── Sign order ───────────────────────────────────────────────────────────────

SIGN_ORDER: tuple[str, ...] = (
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
)


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class NakshatraInfo:
    """Nakshatra information for a single planet."""

    planet: str
    longitude: float
    sign: str
    degree_in_sign: float
    nakshatra: str
    nakshatra_name: str
    nakshatra_lord: str
    pada: int  # 1-4


@dataclass
class NakshatraExchange:
    """A detected Nakshatra exchange between two planets."""

    planet_a: str
    planet_a_nakshatra: str
    planet_a_nakshatra_lord: str
    planet_b: str
    planet_b_nakshatra: str
    planet_b_nakshatra_lord: str
    reading: str
    significance: str  # "lifelong" or "transit"
    strength: str  # "strong", "moderate"


@dataclass
class NakshatraExchangeResult:
    """Complete Nakshatra analysis result."""

    natal_nakshatras: dict[str, NakshatraInfo]
    transit_nakshatras: dict[str, NakshatraInfo] | None
    natal_exchanges: list[NakshatraExchange]
    transit_exchanges: list[NakshatraExchange]
    nakshatra_readings: dict[str, str]


# ── Classical readings for Nakshatra exchanges ──────────────────────────────

NAKSHATRA_EXCHANGE_READINGS: dict[tuple[str, str], str] = {
    ("Ketu", "Mars"): (
        "Mars in Ketu's Nakshatra & Ketu in Mars' Nakshatra: Intense, unconventional drive; "
        "sudden actions, foreign connections, and spiritual warrior energy. Past-life martial karma manifests as "
        "combative instincts and fearless pursuit of liberation."
    ),
    ("Venus", "Jupiter"): (
        "Venus in Jupiter's Nakshatra & Jupiter in Venus' Nakshatra: Wisdom in love; "
        "artistic and philosophical brilliance. Relationships blend luxury with dharma. "
        "Strong indicators for teaching art, music, or spiritual counseling."
    ),
    ("Sun", "Moon"): (
        "Sun in Moon's Nakshatra & Moon in Sun's Nakshatra: Royal emotional intelligence; "
        "leadership through empathy. Strong parental influence. Public life and private "
        "emotions are deeply intertwined."
    ),
    ("Moon", "Mercury"): (
        "Moon in Mercury's Nakshatra & Mercury in Moon's Nakshatra: Communicative emotions; "
        "witty mind, artistic expression. Strong in writing, counseling, and media. "
        "Emotional intelligence drives intellectual pursuits."
    ),
    ("Mars", "Rahu"): (
        "Mars in Rahu's Nakshatra & Rahu in Mars' Nakshatra: Intense, unconventional drive; "
        "sudden actions, foreign connections, and magnetic physical energy. "
        "Risk of impulsive decisions but great potential for breakthrough."
    ),
    ("Jupiter", "Saturn"): (
        "Jupiter in Saturn's Nakshatra & Saturn in Jupiter's Nakshatra: Disciplined wisdom; "
        "philosophical patience, structured spirituality. Long-term teaching or counseling career. "
        "Delayed but profound spiritual growth."
    ),
    ("Mercury", "Venus"): (
        "Mercury in Venus' Nakshatra & Venus in Mercury' Nakshatra: Artistic intellect; "
        "beautiful communication, musical talent, and business acumen. "
        "Strong in creative writing, design, or luxury goods trade."
    ),
    ("Saturn", "Rahu"): (
        "Saturn in Rahu's Nakshatra & Rahu in Saturn' Nakshatra: Unconventional discipline; "
        "systemic innovation, revolutionary structure. Foreign or technological career paths. "
        "Karmic lessons through breaking established norms."
    ),
    ("Jupiter", "Rahu"): (
        "Jupiter in Rahu's Nakshatra & Rahu in Jupiter' Nakshatra: Unorthodox wisdom; "
        "foreign spiritual traditions, innovative philosophy. Attraction to unconventional "
        "teachers or belief systems. Strong foreign connection through education."
    ),
    ("Venus", "Rahu"): (
        "Venus in Rahu's Nakshatra & Rahu in Venus' Nakshatra: Unconventional romance; "
        "foreign partners, taboo attractions, obsessive love. Artistic innovation through "
        "breaking aesthetic norms. Secret or hidden romantic connections."
    ),
    ("Sun", "Rahu"): (
        "Sun in Rahu's Nakshatra & Rahu in Sun' Nakshatra: Unconventional authority; "
        "foreign leadership, innovative governance. Ego transformation through breaking "
        "established patterns. Foreign or technological career prominence."
    ),
    ("Moon", "Rahu"): (
        "Moon in Rahu's Nakshatra & Rahu in Moon' Nakshatra: Unconventional emotions; "
        "foreign connections through family, innovative nurturing. Emotional intensity "
        "with foreign or technological themes."
    ),
    ("Mercury", "Rahu"): (
        "Mercury in Rahu's Nakshatra & Rahu in Mercury' Nakshatra: Unconventional communication; "
        "foreign language skills, technological writing, innovative business. "
        "Strong in data science, AI, or international communications."
    ),
    ("Mars", "Saturn"): (
        "Mars in Saturn's Nakshatra & Saturn in Mars' Nakshatra: Disciplined courage; "
        "patient action, strategic military or engineering career. "
        "Slow but unstoppable force. Long-term physical endurance."
    ),
    ("Venus", "Saturn"): (
        "Venus in Saturn's Nakshatra & Saturn in Venus' Nakshatra: Disciplined love; "
        "enduring relationships, patient artistry. Long-term partnerships built on "
        "commitment rather than passion. Mature romantic appreciation."
    ),
    ("Mercury", "Saturn"): (
        "Mercury in Saturn's Nakshatra & Saturn in Mercury' Nakshatra: Disciplined intellect; "
        "structured thinking, analytical mastery. Strong in engineering, law, or systematic research. "
        "Patient communication style."
    ),
    ("Sun", "Saturn"): (
        "Sun in Saturn's Nakshatra & Saturn in Sun' Nakshatra: Disciplined authority; "
        "responsible leadership, structured governance. Authority earned through perseverance. "
        "Karmic lessons in ego management."
    ),
    ("Moon", "Saturn"): (
        "Moon in Saturn's Nakshatra & Saturn in Moon' Nakshatra: Disciplined emotions; "
        "patient nurturing, structured home life. Emotional maturity through hardship. "
        "Deep, lasting emotional bonds."
    ),
    ("Jupiter", "Mercury"): (
        "Jupiter in Mercury's Nakshatra & Mercury in Jupiter' Nakshatra: Intellectual wisdom; "
        "teaching through communication, philosophical business. Strong in education, "
        "publishing, or advisory roles."
    ),
    ("Venus", "Moon"): (
        "Venus in Moon's Nakshatra & Moon in Venus' Nakshatra: Romantic emotions; "
        "beautiful nurturing, artistic sensitivity. Strong in beauty, fashion, or hospitality. "
        "Emotional fulfillment through aesthetic expression."
    ),
    ("Sun", "Mercury"): (
        "Sun in Mercury's Nakshatra & Mercury in Sun' Nakshatra: Intellectual authority; "
        "communicative leadership, philosophical writing. Strong in politics, teaching, or media. "
        "Ego expressed through communication."
    ),
    ("Mars", "Jupiter"): (
        "Mars in Jupiter's Nakshatra & Jupiter in Mars' Nakshatra: Spiritual courage; "
        "philosophical warrior, righteous action. Strong in spiritual teaching, martial arts, "
        "or humanitarian work."
    ),
    ("Venus", "Mars"): (
        "Venus in Mars' Nakshatra & Mars in Venus' Nakshatra: Passionate creativity; "
        "intense romantic drive, artistic courage. Strong in performing arts, fashion, "
        "or physical beauty industries."
    ),
    ("Jupiter", "Moon"): (
        "Jupiter in Moon's Nakshatra & Moon in Jupiter' Nakshatra: Emotional wisdom; "
        "nurturing philosophy, compassionate teaching. Strong in counseling, spiritual "
        "guidance, or family traditions."
    ),
    ("Saturn", "Ketu"): (
        "Saturn in Ketu's Nakshatra & Ketu in Saturn' Nakshatra: Detached discipline; "
        "spiritual isolation, ascetic tendencies. Long periods of solitude for spiritual "
        "growth. Karmic release through renunciation."
    ),
    ("Jupiter", "Ketu"): (
        "Jupiter in Ketu's Nakshatra & Ketu in Jupiter' Nakshatra: Detached wisdom; "
        "spiritual knowledge without ego attachment. Past-life spiritual merit manifests "
        "as intuitive understanding."
    ),
    ("Venus", "Ketu"): (
        "Venus in Ketu's Nakshatra & Ketu in Venus' Nakshatra: Detached love; "
        "spiritual approach to romance, past-life romantic connections. "
        "Unconventional beauty appreciation."
    ),
    ("Sun", "Ketu"): (
        "Sun in Ketu's Nakshatra & Ketu in Sun' Nakshatra: Detached authority; "
        "spiritual leadership, ego dissolution. Past-life royal karma manifests as "
        "natural leadership without ego attachment."
    ),
    ("Moon", "Ketu"): (
        "Moon in Ketu's Nakshatra & Ketu in Moon' Nakshatra: Detached emotions; "
        "past-life emotional connections, intuitive depth. Strong psychic abilities. "
        "Emotional release through spiritual practice."
    ),
    ("Mercury", "Ketu"): (
        "Mercury in Ketu's Nakshatra & Ketu in Mercury' Nakshatra: Detached intellect; "
        "spiritual communication, past-life analytical skills. Strong in meditation "
        "instruction or spiritual writing."
    ),
    ("Mars", "Ketu"): (
        "Mars in Ketu's Nakshatra & Ketu in Mars' Nakshatra: Detached courage; "
        "spiritual warrior energy, past-life martial skills. Strong in martial arts "
        "teaching or spiritual combat."
    ),
    ("Saturn", "Mars"): (
        "Saturn in Mars' Nakshatra & Mars in Saturn' Nakshatra: Disciplined courage; "
        "patient action, strategic military or engineering career. "
        "Slow but unstoppable force. Long-term physical endurance."
    ),
    ("Sun", "Moon"): (
        "Sun in Moon's Nakshatra & Moon in Sun' Nakshatra: Royal emotional intelligence; "
        "leadership through empathy. Strong parental influence. Public life and private "
        "emotions are deeply intertwined."
    ),
    ("Sun", "Mars"): (
        "Sun in Mars' Nakshatra & Mars in Sun' Nakshatra: Courageous authority; "
        "fiery leadership, martial governance. Strong in military, politics, or sports. "
        "Ego expressed through bold action."
    ),
    ("Sun", "Jupiter"): (
        "Sun in Jupiter's Nakshatra & Jupiter in Sun' Nakshatra: Philosophical authority; "
        "spiritual leadership, dharmic governance. Strong in teaching, religion, or law. "
        "Ego expressed through wisdom."
    ),
    ("Sun", "Venus"): (
        "Sun in Venus' Nakshatra & Venus in Sun' Nakshatra: Artistic authority; "
        "beautiful leadership, creative governance. Strong in arts, entertainment, or diplomacy. "
        "Ego expressed through aesthetic excellence."
    ),
    ("Sun", "Saturn"): (
        "Sun in Saturn's Nakshatra & Saturn in Sun' Nakshatra: Disciplined authority; "
        "responsible leadership, structured governance. Authority earned through perseverance. "
        "Karmic lessons in ego management."
    ),
    ("Moon", "Mars"): (
        "Moon in Mars' Nakshatra & Mars in Moon' Nakshatra: Emotional courage; "
        "passionate nurturing, protective instincts. Strong in healthcare, defense, or activism. "
        "Emotional intensity drives physical action."
    ),
    ("Moon", "Jupiter"): (
        "Moon in Jupiter's Nakshatra & Jupiter in Moon' Nakshatra: Emotional wisdom; "
        "nurturing philosophy, compassionate teaching. Strong in counseling, spiritual "
        "guidance, or family traditions."
    ),
    ("Moon", "Venus"): (
        "Moon in Venus' Nakshatra & Venus in Moon' Nakshatra: Romantic emotions; "
        "beautiful nurturing, artistic sensitivity. Strong in beauty, fashion, or hospitality. "
        "Emotional fulfillment through aesthetic expression."
    ),
    ("Moon", "Saturn"): (
        "Moon in Saturn's Nakshatra & Saturn in Moon' Nakshatra: Disciplined emotions; "
        "patient nurturing, structured home life. Emotional maturity through hardship. "
        "Deep, lasting emotional bonds."
    ),
    ("Mars", "Mercury"): (
        "Mars in Mercury's Nakshatra & Mercury in Mars' Nakshatra: Communicative courage; "
        "sharp speech, competitive intellect. Strong in technology, sports commentary, or debate. "
        "Physical energy expressed through words."
    ),
    ("Mars", "Venus"): (
        "Mars in Venus' Nakshatra & Venus in Mars' Nakshatra: Passionate creativity; "
        "intense romantic drive, artistic courage. Strong in performing arts, fashion, "
        "or physical beauty industries."
    ),
    ("Mars", "Saturn"): (
        "Mars in Saturn's Nakshatra & Saturn in Mars' Nakshatra: Disciplined courage; "
        "patient action, strategic military or engineering career. "
        "Slow but unstoppable force. Long-term physical endurance."
    ),
    ("Jupiter", "Mercury"): (
        "Jupiter in Mercury's Nakshatra & Mercury in Jupiter' Nakshatra: Intellectual wisdom; "
        "teaching through communication, philosophical business. Strong in education, "
        "publishing, or advisory roles."
    ),
    ("Jupiter", "Venus"): (
        "Jupiter in Venus' Nakshatra & Venus in Jupiter' Nakshatra: Wisdom in love; "
        "artistic and philosophical brilliance. Relationships blend luxury with dharma. "
        "Strong indicators for teaching art, music, or spiritual counseling."
    ),
    ("Jupiter", "Saturn"): (
        "Jupiter in Saturn's Nakshatra & Saturn in Jupiter' Nakshatra: Disciplined wisdom; "
        "philosophical patience, structured spirituality. Long-term teaching or counseling career. "
        "Delayed but profound spiritual growth."
    ),
    ("Mercury", "Venus"): (
        "Mercury in Venus' Nakshatra & Venus in Mercury' Nakshatra: Artistic intellect; "
        "beautiful communication, musical talent, and business acumen. "
        "Strong in creative writing, design, or luxury goods trade."
    ),
    ("Mercury", "Saturn"): (
        "Mercury in Saturn's Nakshatra & Saturn in Mercury' Nakshatra: Disciplined intellect; "
        "structured thinking, analytical mastery. Strong in engineering, law, or systematic research. "
        "Patient communication style."
    ),
    ("Venus", "Saturn"): (
        "Venus in Saturn's Nakshatra & Saturn in Venus' Nakshatra: Disciplined love; "
        "enduring relationships, patient artistry. Long-term partnerships built on "
        "commitment rather than passion. Mature romantic appreciation."
    ),
}


# ── Engine ───────────────────────────────────────────────────────────────────


def _longitude_to_nakshatra(longitude: float) -> tuple[str, int, int]:
    """Convert ecliptic longitude to Nakshatra, index, and pada."""
    normalized = longitude % 360.0
    nak_span = 360.0 / 27.0  # ~13.333 degrees per nakshatra
    nak_index = int(normalized / nak_span)
    nakshatra = NAKSHATRA_ORDER[min(nak_index, 26)]
    pada_span = nak_span / 4
    within_nak = normalized - (nak_index * nak_span)
    pada = int(within_nak / pada_span) + 1
    pada = min(pada, 4)
    return nakshatra, nak_index, pada


def compute_nakshatra_info(
    planet_details: dict[str, dict[str, Any]],
) -> dict[str, NakshatraInfo]:
    """Compute Nakshatra information for all planets from their positions.

    Args:
        planet_details: {planet: {sign, degree_in_sign, longitude (optional), ...}}

    Returns:
        Dictionary of planet name -> NakshatraInfo.
    """
    result: dict[str, NakshatraInfo] = {}

    for planet, data in planet_details.items():
        sign = data.get("sign", "")
        degree_in_sign = data.get("degree_in_sign", 0)

        # Compute longitude from sign + degree
        if sign in SIGN_ORDER:
            sign_idx = SIGN_ORDER.index(sign)
            longitude = (sign_idx * 30.0) + degree_in_sign
        else:
            longitude = data.get("longitude", 0.0)

        nakshatra, nak_idx, pada = _longitude_to_nakshatra(longitude)
        nak_lord = NAKSHATRA_LORDS.get(nakshatra, "")

        result[planet] = NakshatraInfo(
            planet=planet,
            longitude=longitude,
            sign=sign,
            degree_in_sign=degree_in_sign,
            nakshatra=nakshatra,
            nakshatra_name=NAKSHATRA_NAMES.get(nakshatra, nakshatra),
            nakshatra_lord=nak_lord,
            pada=pada,
        )

    return result


def detect_nakshatra_exchanges(
    nakshatra_infos: dict[str, NakshatraInfo],
    significance: str = "lifelong",
) -> list[NakshatraExchange]:
    """Detect Nakshatra exchanges between planet pairs.

    A Nakshatra exchange occurs when:
      - Planet A is in Planet B's Nakshatra Lord's Nakshatra
      - Planet B is in Planet A's Nakshatra Lord's Nakshatra

    Args:
        nakshatra_infos: Nakshatra information for all planets.
        significance: "lifelong" for natal, "transit" for current.

    Returns:
        List of detected NakshatraExchange objects.
    """
    exchanges: list[NakshatraExchange] = []
    seen_pairs: set[tuple[str, str]] = set()

    planets = list(nakshatra_infos.keys())
    for i, planet_a in enumerate(planets):
        for planet_b in planets[i + 1 :]:
            info_a = nakshatra_infos[planet_a]
            info_b = nakshatra_infos[planet_b]

            # Check: A is in B's Nakshatra Lord's Nakshatra
            # and B is in A's Nakshatra Lord's Nakshatra
            # Case-insensitive comparison: A's nakshatra lord == B's planet name
            #                               AND B's nakshatra lord == A's planet name
            a_lord = info_a.nakshatra_lord.upper()
            b_lord = info_b.nakshatra_lord.upper()

            if a_lord == planet_b.upper() and b_lord == planet_a.upper():
                pair = tuple(sorted([planet_a, planet_b]))
                pair_typed: tuple[str, str] = (pair[0], pair[1])
                if pair_typed in seen_pairs:
                    continue
                seen_pairs.add(pair_typed)

                # Look up reading
                reading_key = (planet_a, planet_b)
                reading_key_rev = (planet_b, planet_a)
                reading = NAKSHATRA_EXCHANGE_READINGS.get(
                    reading_key,
                    NAKSHATRA_EXCHANGE_READINGS.get(
                        reading_key_rev,
                        f"Nakshatra exchange between {planet_a} and {planet_b}: "
                        f"Mutual influence creating blended energies.",
                    ),
                )

                exchanges.append(
                    NakshatraExchange(
                        planet_a=planet_a,
                        planet_a_nakshatra=info_a.nakshatra,
                        planet_a_nakshatra_lord=a_lord,
                        planet_b=planet_b,
                        planet_b_nakshatra=info_b.nakshatra,
                        planet_b_nakshatra_lord=b_lord,
                        reading=reading,
                        significance=significance,
                        strength="strong",
                    )
                )

    return exchanges


def compute_nakshatra_exchanges(
    natal_planet_details: dict[str, dict[str, Any]],
    transit_planet_details: dict[str, dict[str, Any]] | None = None,
) -> NakshatraExchangeResult:
    """Compute complete Nakshatra analysis with exchanges.

    Args:
        natal_planet_details: Natal planet positions.
        transit_planet_details: Current transit positions (optional).

    Returns:
        NakshatraExchangeResult with all analysis.
    """
    natal_nakshatras = compute_nakshatra_info(natal_planet_details)
    natal_exchanges = detect_nakshatra_exchanges(natal_nakshatras, "lifelong")

    transit_nakshatras = None
    transit_exchanges: list[NakshatraExchange] = []
    if transit_planet_details:
        transit_nakshatras = compute_nakshatra_info(transit_planet_details)
        transit_exchanges = detect_nakshatra_exchanges(transit_nakshatras, "transit")

    # Build readings dict
    readings: dict[str, str] = {}
    for ex in natal_exchanges:
        key = f"{ex.planet_a}-{ex.planet_b}"
        readings[key] = ex.reading
    for ex in transit_exchanges:
        key = f"{ex.planet_a}-{ex.planet_b}-transit"
        readings[key] = ex.reading

    return NakshatraExchangeResult(
        natal_nakshatras=natal_nakshatras,
        transit_nakshatras=transit_nakshatras,
        natal_exchanges=natal_exchanges,
        transit_exchanges=transit_exchanges,
        nakshatra_readings=readings,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Transit Nakshatra Exchange Detection (14-day forecast)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class TransitNakshatraExchange:
    """A transit-to-natal Nakshatra exchange detected on a specific date."""

    date: str
    transit_planet: str
    transit_nakshatra: str
    transit_nakshatra_lord: str
    natal_planet: str
    natal_nakshatra: str
    natal_nakshatra_lord: str
    reading: str
    strength: str  # "strong", "moderate"


def compute_transit_nakshatra_exchanges(
    natal_planet_details: dict[str, dict[str, Any]],
    days: int = 14,
) -> list[TransitNakshatraExchange]:
    """Detect Transit-to-Natal Nakshatra exchanges for the next N days.

    For each day, uses pyswisseph to calculate transit planet positions,
    converts them to Nakshatras, and compares with natal Nakshatras.

    A transit-natal exchange occurs when:
      - Transit Planet A is in a Nakshatra whose Lord is Natal Planet B
      - AND Natal Planet B is in a Nakshatra whose Lord is Transit Planet A

    Or more commonly:
      - Transit Planet A's Nakshatra Lord == Natal Planet B's name
      - AND Natal Planet B's Nakshatra Lord == Transit Planet A's name

    Args:
        natal_planet_details: Natal planet positions.
        days: Number of days to forecast.

    Returns:
        List of TransitNakshatraExchange objects.
    """
    from datetime import datetime, timedelta, timezone

    exchanges: list[TransitNakshatraExchange] = []
    now = datetime.now(timezone.utc)

    # Compute natal Nakshatras once
    natal_naks = compute_nakshatra_info(natal_planet_details)

    # Classical planets for transit check
    transit_planets = [
        "SUN",
        "MOON",
        "MARS",
        "MERCURY",
        "JUPITER",
        "VENUS",
        "SATURN",
        "RAHU",
        "KETU",
    ]

    for day_offset in range(days):
        target_date = now + timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")

        # Compute FUTURE transit positions using Swiss Ephemeris
        try:
            from jrs.prediction_engine.gochar_transit import compute_planetary_states_for_date

            daily_states = compute_planetary_states_for_date(
                target_date.year,
                target_date.month,
                target_date.day,
            )
        except Exception:
            continue

        # Convert transit longitudes to Nakshatras
        transit_naks: dict[str, NakshatraInfo] = {}
        for planet in transit_planets:
            state = daily_states.get(planet)
            if not state:
                continue
            lng = state.longitude
            nakshatra, nak_idx, pada = _longitude_to_nakshatra(lng)
            nak_lord = NAKSHATRA_LORDS.get(nakshatra, "")

            # Convert longitude to sign for display
            sign_idx = int(lng / 30.0)
            signs = [
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
            sign = signs[sign_idx % 12] if sign_idx < 12 else "MESHA"
            deg_in_sign = lng - (sign_idx * 30.0)

            transit_naks[planet] = NakshatraInfo(
                planet=planet,
                longitude=lng,
                sign=sign,
                degree_in_sign=deg_in_sign,
                nakshatra=nakshatra,
                nakshatra_name=NAKSHATRA_NAMES.get(nakshatra, nakshatra),
                nakshatra_lord=nak_lord,
                pada=pada,
            )

        # Check for transit-natal exchanges
        seen_pairs: set[tuple[str, str, str]] = set()  # (transit_planet, natal_planet, date)

        for t_planet, t_info in transit_naks.items():
            for n_planet, n_info in natal_naks.items():
                # Check: Transit planet's Nakshatra Lord == Natal planet's name
                #        AND Natal planet's Nakshatra Lord == Transit planet's name
                # Normalize case: Nakshatra lords are title-case, planet names are uppercase
                t_lord_upper = t_info.nakshatra_lord.upper()
                n_lord_upper = n_info.nakshatra_lord.upper()
                if t_lord_upper == n_planet and n_lord_upper == t_planet:
                    pair_key = (t_planet, n_planet, date_str)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Generate detailed reading
                    reading = _generate_transit_nak_exchange_reading(
                        t_planet,
                        t_info,
                        n_planet,
                        n_info,
                        date_str,
                    )

                    exchanges.append(
                        TransitNakshatraExchange(
                            date=date_str,
                            transit_planet=t_planet,
                            transit_nakshatra=t_info.nakshatra_name,
                            transit_nakshatra_lord=t_info.nakshatra_lord,
                            natal_planet=n_planet,
                            natal_nakshatra=n_info.nakshatra_name,
                            natal_nakshatra_lord=n_info.nakshatra_lord,
                            reading=reading,
                            strength="strong",
                        )
                    )

    print(
        f"TRANSIT NAKSHATRA DEBUG: Found {len(exchanges)} transit exchanges in the next {days} days."
    )
    return exchanges


def _generate_transit_nak_exchange_reading(
    t_planet: str,
    t_info: "NakshatraInfo",
    n_planet: str,
    n_info: "NakshatraInfo",
    date_str: str,
) -> str:
    """Generate a detailed reading for a transit-natal Nakshatra exchange."""
    # Base reading from classical lookup
    reading_key = (t_planet, n_planet)
    reading_key_rev = (n_planet, t_planet)
    base_reading = NAKSHATRA_EXCHANGE_READINGS.get(
        reading_key,
        NAKSHATRA_EXCHANGE_READINGS.get(
            reading_key_rev, f"Mutual Nakshatra exchange between {t_planet} and {n_planet}."
        ),
    )

    # Build transit-specific reading
    reading = (
        f"On {date_str}, Transit {t_planet} in {t_info.nakshatra_name} (Lord: {t_info.nakshatra_lord}) "
        f"exchanges Nakshatras with Natal {n_planet} in {n_info.nakshatra_name} (Lord: {n_info.nakshatra_lord}). "
        f"{base_reading} "
        f"This is a temporary activation of karmic patterns — the transit planet "
        f"awakens dormant potentials in the natal planet's domain. "
        f"Conscious awareness of this exchange during {date_str} can help channel "
        f"these energies constructively."
    )

    return reading


def transit_nakshatra_exchanges_to_dict(
    exchanges: list[TransitNakshatraExchange],
) -> list[dict[str, Any]]:
    """Convert TransitNakshatraExchange list to JSON-serializable list."""
    return [
        {
            "date": e.date,
            "transit_planet": e.transit_planet,
            "transit_nakshatra": e.transit_nakshatra,
            "transit_nakshatra_lord": e.transit_nakshatra_lord,
            "natal_planet": e.natal_planet,
            "natal_nakshatra": e.natal_nakshatra,
            "natal_nakshatra_lord": e.natal_nakshatra_lord,
            "reading": e.reading,
            "strength": e.strength,
        }
        for e in exchanges
    ]


def nakshatra_exchange_to_dict(result: NakshatraExchangeResult) -> dict[str, Any]:
    """Convert NakshatraExchangeResult to JSON-serializable dict."""

    def _info(n: NakshatraInfo) -> dict[str, Any]:
        return {
            "planet": n.planet,
            "longitude": round(n.longitude, 4),
            "sign": n.sign,
            "degree_in_sign": round(n.degree_in_sign, 2),
            "nakshatra": n.nakshatra,
            "nakshatra_name": n.nakshatra_name,
            "nakshatra_lord": n.nakshatra_lord,
            "pada": n.pada,
        }

    def _exch(e: NakshatraExchange) -> dict[str, Any]:
        return {
            "planet_a": e.planet_a,
            "planet_a_nakshatra": e.planet_a_nakshatra,
            "planet_a_nakshatra_lord": e.planet_a_nakshatra_lord,
            "planet_b": e.planet_b,
            "planet_b_nakshatra": e.planet_b_nakshatra,
            "planet_b_nakshatra_lord": e.planet_b_nakshatra_lord,
            "reading": e.reading,
            "significance": e.significance,
            "strength": e.strength,
        }

    return {
        "natal_nakshatras": {k: _info(v) for k, v in result.natal_nakshatras.items()},
        "transit_nakshatras": {k: _info(v) for k, v in (result.transit_nakshatras or {}).items()},
        "natal_exchanges": [_exch(e) for e in result.natal_exchanges],
        "transit_exchanges": [_exch(e) for e in result.transit_exchanges],
        "nakshatra_readings": result.nakshatra_readings,
        "transit_natal_exchanges": [],
    }
