"""Relationship & Intimacy Analysis Engine — Classical Vedic deterministics.

Analyzes the natal chart for detailed relationship dynamics, intimacy patterns,
and specific classical indicators. All outputs are deterministic from planetary
positions — no LLM, no randomness.

Key analyses:
  1. Venus-Mars dynamic (passion, desire, physical compatibility)
  2. 7th house lord analysis (spouse nature, partnership style)
  3. 8th house / 12th house secrets (hidden relationships, intimacy depth)
  4. Rahu-Ketu axis effects on relationships
  5. Specific classical combination detection for relationship patterns

Reference: BPHS Ch 33-36 (Marriage), Phaladeepika Ch 12, Jataka Parijata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Sign / House Constants ───────────────────────────────────────────────────

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

SIGN_NAMES: dict[str, str] = {
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

SIGN_LORDS: dict[str, str] = {
    "MESHA": "MARS",
    "VRISHABHA": "VENUS",
    "MITHUNA": "MERCURY",
    "KARKA": "MOON",
    "SIMHA": "SUN",
    "KANYA": "MERCURY",
    "TULA": "VENUS",
    "VRISHCHIKA": "MARS",
    "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN",
    "KUMBHA": "SATURN",
    "MEENA": "JUPITER",
}

# ── Natural significators ────────────────────────────────────────────────────

VENUS_SIGNIFICATIONS = {
    "love": "romantic love, beauty, art, luxury, comfort",
    "sex": "physical pleasure, sensuality, desire nature",
    "marriage": "marital harmony, spouse attraction, romantic bond",
    "creativity": "artistic expression, aesthetic appreciation",
}

MARS_SIGNIFICATIONS = {
    "passion": "physical passion, sexual energy, drive",
    "courage": "boldness in relationships, initiative",
    "conflict": "anger, arguments, DOMINANCE in partnerships",
    "physical": "body, physical attraction, stamina",
}

# ── Venus-in-House Intimacy Analysis ────────────────────────────────────────

VENUS_HOUSE_INTIMACY: dict[int, dict[str, str]] = {
    1: {
        "style": "Direct and confident approach to intimacy. Physical beauty attracts partners naturally. Strong sensual desires.",
        "strength": "High — Venus in ascendant amplifies romantic magnetism",
        "challenge": "May be vain or overly focused on physical appearance",
        "partner_type": "Attracts physically attractive, charming partners",
    },
    2: {
        "style": "Wealth and comfort are intertwined with intimacy. Values luxurious romantic settings. Food and sensuality linked.",
        "strength": "Strong — financial security enhances romantic life",
        "challenge": "May equate love with material comfort",
        "partner_type": "Attracts wealthy, well-spoken partners from good families",
    },
    3: {
        "style": "Communication-driven intimacy. Expresses love through words, letters, and intellectual connection.",
        "strength": "Moderate — emotional expression through communication",
        "challenge": "May intellectualize emotions, reducing physical spontaneity",
        "partner_type": "Attracts communicative, intellectually stimulating partners",
    },
    4: {
        "style": "Domestic intimacy. Creates a beautiful, comfortable home environment for romantic life. Emotional security in love.",
        "strength": "Strong — domestic bliss supports romantic fulfillment",
        "challenge": "May become too comfortable, reducing passion over time",
        "partner_type": "Attracts nurturing, home-oriented partners",
    },
    5: {
        "style": "Passionate and creative romance. Approaches love as art. Strong romantic desire and creative sexual expression.",
        "strength": "Very High — Venus in triangle house amplifies love",
        "challenge": "May have idealized romantic expectations",
        "partner_type": "Attracts creative, passionate, youthful partners",
    },
    6: {
        "style": "Service-oriented intimacy. Shows love through acts of service. Health-conscious approach to physical relationships.",
        "strength": "Moderate — Venus in 6th weakens romantic expression",
        "challenge": "May attract health problems in relationships or attract critical partners",
        "partner_type": "Attracts partners through work/service environments",
    },
    7: {
        "style": "Natural partnership ability. Strong marital harmony. Balanced approach to give-and-take in relationships.",
        "strength": "Very Strong — Venus in own domain of partnership",
        "challenge": "May become dependent on partner for self-worth",
        "partner_type": "Attracts harmonious, beautiful, artistically inclined partners",
    },
    8: {
        "style": "Deep, intense, transformative intimacy. Secret romantic affairs possible. Strong sexual magnetism with hidden depths.",
        "strength": "Intense but hidden — powerful underground romantic energy",
        "challenge": "Attracts complicated, secretive, or taboo relationships",
        "partner_type": "Attracts intense, mysterious, sexually magnetic partners",
    },
    9: {
        "style": "Spiritual approach to love. Romance during travel. Love of philosophy, wisdom, and distant cultures in partner.",
        "strength": "Good — Venus in dharma house blesses love with meaning",
        "challenge": "May idealize partner or seek perfection",
        "partner_type": "Attracts wise, cultured, possibly foreign partners",
    },
    10: {
        "style": "Career-focused relationships. Public partnerships. Love through professional achievement and social status.",
        "strength": "Moderate — Venus in karma house delays but matures love",
        "challenge": "May prioritize career over romantic life",
        "partner_type": "Attracts ambitious, status-conscious partners",
    },
    11: {
        "style": "Social approach to love. Finds partners through networks and groups. Friendship-based romantic connections.",
        "strength": "Good — Venus in gains house brings romantic fulfillment through networks",
        "challenge": "May have many romantic connections but few deep ones",
        "partner_type": "Attracts socially connected, network-oriented partners",
    },
    12: {
        "style": "Private, spiritual intimacy. Secret romantic affairs. Foreign romantic connections. Surrender in love.",
        "strength": "Hidden but powerful — Venus in 12th intensifies private desires",
        "challenge": "Attracts secret affairs, extramarital connections, or relationships in isolation",
        "partner_type": "Attracts foreign, spiritual, or reclusive partners",
    },
}

# ── Mars-in-House Intimacy Analysis ─────────────────────────────────────────

MARS_HOUSE_INTIMACY: dict[int, dict[str, str]] = {
    1: {
        "style": "Assertive and dominant in intimacy. Strong physical desire. Natural sexual magnetism and confidence.",
        "strength": "High — Mars in ascendant amplifies physical passion",
        "challenge": "Aggressive or domineering in bed. Risk of sexual aggression.",
    },
    2: {
        "style": "Direct and assertive in expressing desires. Financial aspects of intimacy matter. Aggressive speech in romantic context.",
        "strength": "Moderate — Mars in wealth house channels desire into material pursuit",
        "challenge": "Harsh speech during intimate disagreements",
    },
    3: {
        "style": "Courageous initiator in love. Takes physical risks for romance. Athletic and adventurous approach to intimacy.",
        "strength": "Strong — Mars in 3rd is in own sign energy",
        "challenge": "May be too aggressive or impatient",
    },
    4: {
        "style": "Protective and territorial in relationships. Creates secure physical space. Deep emotional passion beneath surface.",
        "strength": "Moderate — Mars in 4th creates domestic tension but deep passion",
        "challenge": "Property/domestic conflicts affect intimate life",
    },
    5: {
        "style": "Passionate creativity in romance. Strong procreative desire. Enthusiastic and energetic approach to intimacy.",
        "strength": "High — Mars in 5th amplifies romantic and sexual energy",
        "challenge": "May have intense romantic attachments that end abruptly",
    },
    6: {
        "style": "Competitive approach to relationships. Overcomes intimacy obstacles. Service-oriented physical expression.",
        "strength": "Moderate — Mars in 6th channels energy into overcoming challenges",
        "challenge": "Health issues may affect intimate life",
    },
    7: {
        "style": "Passionate partnerships. Strong physical compatibility. Mars aspects 1st, 4th, 8th from 7th — creates intensity.",
        "strength": "High — Mars in partnership house amplifies physical chemistry",
        "challenge": "Arguments, dominance struggles, and sexual aggression possible",
    },
    8: {
        "style": "Intense, transformative intimacy. Deep sexual experiences. Occult approach to sexuality. Sudden passionate encounters.",
        "strength": "Very High — Mars in 8th creates underground sexual energy",
        "challenge": "Accidents during intimacy, sexual trauma, or obsessive desires",
    },
    9: {
        "style": "Adventurous and philosophical approach to intimacy. Seeks spiritual connection through physical expression.",
        "strength": "Moderate — Mars in dharma house channels passion into meaning",
        "challenge": "Religious/moral conflicts in intimate life",
    },
    10: {
        "style": "Career-driven relationship energy. Balances professional ambition with intimate needs. Public display of passion.",
        "strength": "Moderate — Mars in karma house delays physical fulfillment",
        "challenge": "Professional stress affects intimate life",
    },
    11: {
        "style": "Social energy in relationships. Group activities with partner. Network-based romantic connections.",
        "strength": "Good — Mars in gains house brings passionate social connections",
        "challenge": "May have multiple simultaneous romantic interests",
    },
    12: {
        "style": "Private intensity. Secret sexual desires. Foreign intimate connections. Spiritual approach to physical union.",
        "strength": "Hidden but powerful — Mars in 12th creates secret sexual energy",
        "challenge": "Secret affairs, sexual isolation, or destructive hidden desires",
    },
}

# ── 7th Lord Analysis ────────────────────────────────────────────────────────

SEVENTH_LORD_ANALYSIS: dict[str, dict[str, str]] = {
    "SUN": {
        "spouse_nature": "Confident, authoritative, possibly egoistic spouse. Strong personality that commands respect.",
        "relationship_dynamic": "Power dynamics are central. The spouse may dominate or be dominant in the relationship.",
        "intimacy": "Passionate but ego-driven. Both partners need to feel respected for intimacy to flourish.",
        "timing": "Marriage likely through professional connections or father's influence.",
    },
    "MOON": {
        "spouse_nature": "Emotionally sensitive, nurturing, caring spouse. Strong maternal/paternal instincts.",
        "relationship_dynamic": "Emotional connection is paramount. Moods fluctuate and affect the relationship.",
        "intimacy": "Emotionally driven intimacy. Needs feeling of safety and emotional bonding for physical connection.",
        "timing": "Marriage likely during a Jupiter or Moon period, possibly connected to family.",
    },
    "MARS": {
        "spouse_nature": "Energetic, passionate, possibly aggressive spouse. Strong physical constitution.",
        "relationship_dynamic": "Physical compatibility is strong but arguments may be frequent. Manglik tendencies.",
        "intimacy": "Very strong physical compatibility. High sexual energy. Risk of conflicts during intimacy.",
        "timing": "Marriage during Mars or Venus period, often sudden or through bold action.",
    },
    "MERCURY": {
        "spouse_nature": "Intelligent, communicative, youthful spouse. Good with words and business.",
        "relationship_dynamic": "Mental connection drives the relationship. Communication is key to harmony.",
        "intimacy": "Intellectual intimacy precedes physical. Verbal expression of desires important.",
        "timing": "Marriage during Mercury or Jupiter period, possibly through educational or business connections.",
    },
    "JUPITER": {
        "spouse_nature": "Wise, philosophical, spiritual spouse. Possibly from a religious or academic background.",
        "relationship_dynamic": "Growth-oriented relationship. Both partners learn from each other.",
        "intimacy": "Spiritual approach to physical union. Philosophy of love matters as much as practice.",
        "timing": "Marriage during Jupiter period, often after a period of spiritual growth.",
    },
    "VENUS": {
        "spouse_nature": "Beautiful, artistic, charming spouse. Strong aesthetic sense and romantic nature.",
        "relationship_dynamic": "Harmonious and romantic. Both partners value beauty and comfort.",
        "intimacy": "Highly romantic and sensual. Strong physical attraction and artistic approach to intimacy.",
        "timing": "Marriage during Venus period, often through artistic or social connections.",
    },
    "SATURN": {
        "spouse_nature": "Mature, disciplined, possibly older spouse. Practical and responsible nature.",
        "relationship_dynamic": "Stable but may lack passion. Delay in marriage. Duty-bound approach to partnership.",
        "intimacy": "Reserved physical expression. Intimacy develops slowly but is lasting and committed.",
        "timing": "Delayed marriage, likely during Saturn or Venus period after 28-30 years of age.",
    },
    "RAHU": {
        "spouse_nature": "Unconventional, possibly foreign or different-caste spouse. Obsessive nature.",
        "relationship_dynamic": "Obsessive attraction initially. Unconventional relationship dynamics.",
        "intimacy": "Intense and experimental. May involve unconventional practices or taboo elements.",
        "timing": "Marriage during Rahu period, often sudden or unconventional.",
    },
    "KETU": {
        "spouse_nature": "Spiritual, detached, possibly from past-life connection. Eccentric nature.",
        "relationship_dynamic": "Detachment in marriage. Spiritual purpose behind the partnership.",
        "intimacy": "Spiritual approach to physical union. May have periods of complete abstinence.",
        "timing": "Marriage during Ketu period, often after spiritual awakening.",
    },
}

# ── Rahu-Ketu Axis Effects ──────────────────────────────────────────────────

RAHU_KETU_RELATIONSHIP: dict[str, dict[str, str]] = {
    "RAHU_1_KETU_7": {
        "pattern": "Self vs. Partnership axis. Rahu in 1st obsesses over self-identity, Ketu in 7th detaches from partnerships.",
        "intimacy_effect": "May neglect partner's needs while focusing on self-development. Past-life mastery of partnership, now learning independence.",
        "affair_risk": "Moderate — Rahu's obsessive nature in self may lead to narcissistic relationship patterns",
    },
    "RAHU_2_KETU_8": {
        "pattern": "Wealth vs. Transformation axis. Rahu obsesses over accumulation, Ketu in 8th detaches from shared resources.",
        "intimacy_effect": "Financial matters create intimacy friction. Secret financial matters affect trust.",
        "affair_risk": "Low to Moderate — 8th house Ketu may create hidden relationship dynamics",
    },
    "RAHU_3_KETU_9": {
        "pattern": "Courage vs. Faith axis. Rahu in 3rd pursues unconventional communication, Ketu in 9th detaches from tradition.",
        "intimacy_effect": "Communication style in relationships is unconventional. May challenge traditional relationship norms.",
        "affair_risk": "Low — focus is on communication rather than physical affairs",
    },
    "RAHU_4_KETU_10": {
        "pattern": "Home vs. Career axis. Rahu in 4th obsesses over domestic life, Ketu in 10th detaches from career.",
        "intimacy_effect": "Domestic harmony is obsessive focus. Career detachment may create imbalance.",
        "affair_risk": "Low — domestic focus keeps energy within marriage",
    },
    "RAHU_5_KETU_11": {
        "pattern": "Romance vs. Networks axis. Rahu in 5th obsesses over romance/children, Ketu in 11th detaches from social networks.",
        "intimacy_effect": "Intense romantic focus. May become obsessive about love affairs or children.",
        "affair_risk": "Moderate to High — Rahu in 5th creates obsessive romantic tendencies",
    },
    "RAHU_6_KETU_12": {
        "pattern": "Service vs. Liberation axis. Rahu in 6th obsesses over daily routine, Ketu in 12th detaches from spiritual matters.",
        "intimacy_effect": "Practical approach to intimacy. Service-oriented physical expression.",
        "affair_risk": "Low — 6th house Rahu focuses on duty rather than passion",
    },
    "RAHU_7_KETU_1": {
        "pattern": "Partnership vs. Self axis. Rahu in 7th obsesses over partnerships, Ketu in 1st detaches from self-identity.",
        "intimacy_effect": "Obsessive need for partnership. May lose self-identity in relationships. Strong sexual attraction.",
        "affair_risk": "High — Rahu in 7th creates obsessive attraction to partners, possibly multiple",
    },
    "RAHU_8_KETU_2": {
        "pattern": "Transformation vs. Wealth axis. Rahu in 8th obsesses over hidden matters, Ketu in 2nd detaches from family values.",
        "intimacy_effect": "Deep, intense, secretive intimacy. Obsessive sexual patterns. Hidden relationship dynamics.",
        "affair_risk": "High — Rahu in 8th creates strong tendency toward secret affairs and hidden sexual lives",
    },
    "RAHU_9_KETU_3": {
        "pattern": "Fortune vs. Courage axis. Rahu in 9th obsesses over fortune/spirituality, Ketu in 3rd detaches from communication.",
        "intimacy_effect": "Spiritual approach to relationships. May attract foreign partners.",
        "affair_risk": "Low — spiritual focus reduces physical affair tendency",
    },
    "RAHU_10_KETU_4": {
        "pattern": "Career vs. Home axis. Rahu in 10th obsesses over career, Ketu in 4th detaches from domestic life.",
        "intimacy_effect": "Career-first approach affects intimate life. Partner may feel neglected.",
        "affair_risk": "Moderate — work environment affairs possible",
    },
    "RAHU_11_KETU_5": {
        "pattern": "Networks vs. Romance axis. Rahu in 11th obsesses over social networks, Ketu in 5th detaches from romance.",
        "intimacy_effect": "Social connections may overshadow romantic life. Friendship-based partnerships.",
        "affair_risk": "Moderate — social network affairs possible",
    },
    "RAHU_12_KETU_6": {
        "pattern": "Liberation vs. Service axis. Rahu in 12th obsesses over spiritual liberation, Ketu in 6th detaches from daily routine.",
        "intimacy_effect": "Spiritual and private intimacy. Foreign romantic connections. Secret affairs possible.",
        "affair_risk": "Moderate to High — Rahu in 12th creates secret romantic tendencies in foreign/isolated settings",
    },
}


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class RelationshipInsight:
    """A single relationship analysis insight."""

    category: str  # e.g., "Venus Placement", "7th Lord", "Rahu-Ketu Axis"
    planet: str
    house: int | None = None
    sign: str | None = None
    analysis_type: str = ""  # e.g., "intimacy_style", "spouse_nature", "affair_indicator"
    title: str = ""
    description: str = ""
    classical_reference: str = ""
    strength_indicator: str = ""  # "strong", "moderate", "challenging"
    specific_combinations: list[str] = field(default_factory=list)


@dataclass
class RelationshipAnalysisResult:
    """Complete relationship analysis result."""

    lagna: str
    venus_analysis: list[RelationshipInsight]
    mars_analysis: list[RelationshipInsight]
    seventh_lord_analysis: list[RelationshipInsight]
    rahu_ketu_analysis: list[RelationshipInsight]
    classical_combinations: list[RelationshipInsight]
    overall_assessment: str
    intimacy_profile: str
    relationship_strength: str  # "strong", "moderate", "challenging"


# ── Engine ───────────────────────────────────────────────────────────────────


def _get_house(planet_sign: str, lagna: str) -> int:
    try:
        p_idx = SIGN_ORDER.index(planet_sign)
        l_idx = SIGN_ORDER.index(lagna)
        return ((p_idx - l_idx) % 12) + 1
    except (ValueError, IndexError):
        return 0


def _get_aspect_type(source_deg: float, target_deg: float) -> tuple[bool, str]:
    diff = abs(source_deg - target_deg)
    if diff > 180:
        diff = 360 - diff
    if abs(diff - 180.0) <= 12.0:
        return True, "7th"
    if abs(diff - 120.0) <= 12.0:
        return True, "5th"
    if diff <= 6.0:
        return True, "Conjunction"
    return False, ""


def compute_relationship_analysis(
    planet_details: dict[str, dict[str, Any]],
    lagna: str,
    aspects: list[dict[str, Any]] | None = None,
    parivartana_yogas: list[dict[str, Any]] | None = None,
    yogas: list[dict[str, Any]] | None = None,
    dignity_map: dict[str, str] | None = None,
) -> RelationshipAnalysisResult:
    """Compute detailed relationship analysis from natal chart.

    Args:
        planet_details: Natal planet positions {planet: {sign, degree_in_sign, ...}}
        lagna: Natal Lagna sign
        aspects: Natal aspect matrix entries
        parivartana_yogas: Detected parivartana exchanges
        yogas: Detected classical yogas
        dignity_map: Planet dignity labels

    Returns:
        RelationshipAnalysisResult with all insights
    """
    aspects = aspects or []
    parivartana_yogas = parivartana_yogas or []
    yogas = yogas or []

    venus_insights: list[RelationshipInsight] = []
    mars_insights: list[RelationshipInsight] = []
    seventh_lord_insights: list[RelationshipInsight] = []
    rahu_ketu_insights: list[RelationshipInsight] = []
    classical_combinations: list[RelationshipInsight] = []

    # ── Venus Analysis ──
    venus_data = planet_details.get("VENUS", {})
    venus_sign = venus_data.get("sign", "")
    venus_house = _get_house(venus_sign, lagna) if venus_sign else 0
    venus_deg = venus_data.get("degree_in_sign", 0)

    if venus_house >= 1:
        venus_info = VENUS_HOUSE_INTIMACY.get(venus_house, {})
        venus_insights.append(
            RelationshipInsight(
                category="Venus Placement",
                planet="VENUS",
                house=venus_house,
                sign=venus_sign,
                analysis_type="intimacy_style",
                title=f"Venus in {SIGN_NAMES.get(venus_sign, venus_sign)} ({venus_house}{_get_suffix(venus_house)} House)",
                description=venus_info.get("style", ""),
                classical_reference="BPHS Ch 36 — Venus as natural karaka of marriage and love",
                strength_indicator=venus_info.get("strength", ""),
                specific_combinations=[
                    f"Venus in {SIGN_NAMES.get(venus_sign, venus_sign)} — {venus_info.get('partner_type', '')}",
                    f"Challenge: {venus_info.get('challenge', '')}",
                ],
            )
        )

    # ── Mars Analysis ──
    mars_data = planet_details.get("MARS", {})
    mars_sign = mars_data.get("sign", "")
    mars_house = _get_house(mars_sign, lagna) if mars_sign else 0

    if mars_house >= 1:
        mars_info = MARS_HOUSE_INTIMACY.get(mars_house, {})
        mars_insights.append(
            RelationshipInsight(
                category="Mars Placement",
                planet="MARS",
                house=mars_house,
                sign=mars_sign,
                analysis_type="physical_desire",
                title=f"Mars in {SIGN_NAMES.get(mars_sign, mars_sign)} ({mars_house}{_get_suffix(mars_house)} House)",
                description=mars_info.get("style", ""),
                classical_reference="BPHS Ch 34 — Mars as natural karaka of sexual desire and courage",
                strength_indicator=mars_info.get("strength", ""),
                specific_combinations=[
                    f"Challenge: {mars_info.get('challenge', '')}",
                ],
            )
        )

    # ── Moon Analysis (Emotional Needs) ──
    moon_data = planet_details.get("MOON", {})
    moon_sign = moon_data.get("sign", "")
    moon_house = _get_house(moon_sign, lagna) if moon_sign else 0

    MOON_HOUSE_EMOTIONAL = {
        1: "Emotionally sensitive, reactive personality. Needs constant emotional validation. Intense feelings in relationships.",
        2: "Emotional security tied to wealth and family. Expresses love through food, comfort, and material security.",
        3: "Communicative emotions. Expresses feelings through words, letters, and social interaction.",
        4: "Deeply nurturing and domestic. Home and mother are emotionally central. Needs peaceful domestic environment.",
        5: "Romantic and creative emotions. Falls in love with love itself. Strong emotional connection to children.",
        6: "Emotionally competitive. May attract enemies through emotional reactions. Service-oriented emotional expression.",
        7: "Emotionally dependent on partnerships. Marriage is emotionally central. Spouse fulfills deep emotional needs.",
        8: "Intense, transformative emotions. Prone to emotional upheaval, obsession, and psychological depth.",
        9: "Spiritually oriented emotions. Finds emotional peace through philosophy, travel, and higher learning.",
        10: "Emotions tied to career and public image. Career success brings emotional fulfillment.",
        11: "Socially oriented emotions. Gains emotional satisfaction through networks, friends, and group activities.",
        12: "Emotionally detached or spiritual. May withdraw emotionally. Foreign connections bring emotional peace.",
    }

    if moon_house >= 1:
        moon_emotional = MOON_HOUSE_EMOTIONAL.get(moon_house, "")
        venus_insights.append(
            RelationshipInsight(
                category="Moon Placement",
                planet="MOON",
                house=moon_house,
                sign=moon_sign,
                analysis_type="emotional_needs",
                title=f"Moon in {SIGN_NAMES.get(moon_sign, moon_sign)} ({moon_house}{_get_suffix(moon_house)} House)",
                description=moon_emotional,
                classical_reference="BPHS Ch 33 — Moon as natural karaka of mind and emotions",
                strength_indicator="strong" if moon_house in (1, 4, 7, 9) else "moderate",
                specific_combinations=[
                    f"Moon in {SIGN_NAMES.get(moon_sign, moon_sign)} — emotional nature colored by this sign",
                ],
            )
        )

    # ── Sun Analysis (Ego & Pride) ──
    sun_data = planet_details.get("SUN", {})
    sun_sign = sun_data.get("sign", "")
    sun_house = _get_house(sun_sign, lagna) if sun_sign else 0

    SUN_HOUSE_EGO = {
        1: "Strong ego and self-identity. Confident in relationships but may dominate. Pride is a key relationship theme.",
        2: "Ego tied to wealth and family status. Financial success feeds self-worth. Prideful about family background.",
        3: "Ego expressed through courage and communication. Competitive in relationships. Pride in sibling bonds.",
        4: "Ego connected to domestic life and property. Home environment affects self-image deeply.",
        5: "Creative ego. Pride in intelligence, children, and romantic conquests. Ego-driven romantic pursuits.",
        6: "Ego challenged through enemies and obstacles. Pride humbled through service and conflict.",
        7: "Ego projected onto partnerships. Spouse becomes mirror for self-image. Pride in marriage.",
        8: "Transformative ego. Pride broken through crises. Deep psychological ego death and rebirth cycles.",
        9: "Dharmic ego. Pride in wisdom, teaching, and spiritual authority. Father figure strongly influences ego.",
        10: "Career-driven ego. Professional success is primary self-worth indicator. Authority-seeking nature.",
        11: "Social ego. Pride in networks, gains, and social status. Ego fed through friendships and achievements.",
        12: "Detached ego. Spiritual practice dissolves ego. Pride diminishes through isolation and liberation.",
    }

    if sun_house >= 1:
        sun_ego = SUN_HOUSE_EGO.get(sun_house, "")
        venus_insights.append(
            RelationshipInsight(
                category="Sun Placement",
                planet="SUN",
                house=sun_house,
                sign=sun_sign,
                analysis_type="ego_pride",
                title=f"Sun in {SIGN_NAMES.get(sun_sign, sun_sign)} ({sun_house}{_get_suffix(sun_house)} House)",
                description=sun_ego,
                classical_reference="BPHS Ch 33 — Sun as natural karaka of soul and ego",
                strength_indicator="strong" if sun_house in (1, 5, 9, 10) else "moderate",
                specific_combinations=[
                    f"Sun in {SIGN_NAMES.get(sun_sign, sun_sign)} — ego colored by this sign",
                ],
            )
        )

    # ── Mercury Analysis (Communication & Friendship) ──
    mercury_data = planet_details.get("MERCURY", {})
    mercury_sign = mercury_data.get("sign", "")
    mercury_house = _get_house(mercury_sign, lagna) if mercury_sign else 0

    MERCURY_HOUSE_COMMUNICATION = {
        1: "Intellectual approach to relationships. Communicates feelings through logic. May intellectualize emotions.",
        2: "Wealthy communication. Expresses love through eloquent speech and financial generosity.",
        3: "Communication master in relationships. Writes, texts, and talks love fluently.",
        4: "Domestic communication. Intellectually nurturing home environment. Educational discussions with partner.",
        5: "Creative communication. Romantic, witty, and intellectually playful in love. Flirtatious nature.",
        6: "Communicative conflicts. Arguments may be frequent but intellectual resolution possible.",
        7: "Partnership communication. Intellectual connection with spouse is paramount.",
        8: "Research-oriented communication. Deep, analytical approach to intimacy.",
        9: "Philosophical communication. Discusses higher truths with partner.",
        10: "Career communication. Professional discussions affect personal life.",
        11: "Social communication. Communicates through networks. Friends influence relationship patterns.",
        12: "Secret communication. May keep relationship secrets. Foreign language connections.",
    }

    if mercury_house >= 1:
        mercury_comm = MERCURY_HOUSE_COMMUNICATION.get(mercury_house, "")
        venus_insights.append(
            RelationshipInsight(
                category="Mercury Placement",
                planet="MERCURY",
                house=mercury_house,
                sign=mercury_sign,
                analysis_type="communication_style",
                title=f"Mercury in {SIGN_NAMES.get(mercury_sign, mercury_sign)} ({mercury_house}{_get_suffix(mercury_house)} House)",
                description=mercury_comm,
                classical_reference="BPHS Ch 33 — Mercury as karaka of communication and intellect",
                strength_indicator="strong" if mercury_house in (3, 5, 7, 11) else "moderate",
                specific_combinations=[
                    f"Mercury in {SIGN_NAMES.get(mercury_sign, mercury_sign)} — communication style",
                ],
            )
        )

    # ── Rahu/Ketu extraction (used by the taboo analysis below and the
    # axis analysis further down) ──
    rahu_data = planet_details.get("RAHU", {})
    ketu_data = planet_details.get("KETU", {})
    rahu_sign = rahu_data.get("sign", "")
    ketu_sign = ketu_data.get("sign", "")

    # ── Deep Taboo/Obsession Analysis ──
    taboo_analysis = []
    rahu_house_val = _get_house(rahu_sign, lagna) if rahu_sign else 0

    if rahu_house_val in (7, 8, 12) or venus_house in (7, 8, 12):
        taboo_analysis.append(
            f"RAHU-VENUS DYNAMIC: Rahu in House {rahu_house_val} and Venus in House {venus_house} create "
            f"unconventional attraction patterns — attraction to taboo relationships, foreign partners, "
            f"or unconventional romantic arrangements. Obsessive love patterns, secret affairs, or "
            f"simultaneous relationships are indicated."
        )

    if rahu_house_val in (1, 4, 7, 8, 12) and moon_house in (1, 4, 7, 8, 12):
        taboo_analysis.append(
            f"RAHU-MOON DYNAMIC: Rahu in House {rahu_house_val} and Moon in House {moon_house} create "
            f"emotional turbulence and obsessive emotional patterns. Simultaneous emotional attachments "
            f"or unconventional family dynamics are indicated."
        )

    if mars_house in (7, 8, 12) or rahu_house_val in (7, 8, 12):
        taboo_analysis.append(
            f"MARS-RAHU DYNAMIC: Mars in House {mars_house} and Rahu in House {rahu_house_val} create "
            f"aggressive, intense, and unconventional physical desires. Risk of sexual obsession or "
            f"aggressive relationship dynamics."
        )

    hidden_houses = sum(
        1
        for p in ["VENUS", "MARS", "MOON", "RAHU", "SUN", "MERCURY"]
        if _get_house(planet_details.get(p, {}).get("sign", ""), lagna) in (8, 12)
    )
    if hidden_houses >= 3:
        taboo_analysis.append(
            f"HIDDEN HOUSE DENSITY: {hidden_houses} planets in 8th/12th houses indicate significant "
            f"hidden dimensions in relationships — secret affairs, unconventional sexual practices, "
            f"and simultaneous relationships are strongly indicated."
        )

    if taboo_analysis:
        classical_combinations.append(
            RelationshipInsight(
                category="Deep Psychological Profile",
                planet="MULTIPLE",
                analysis_type="taboo_obsession",
                title="Deep Psychological & Taboo Analysis",
                description=" ".join(taboo_analysis),
                classical_reference="BPHS Ch 41 — Rahu effects on relationship dynamics",
                strength_indicator="challenging" if len(taboo_analysis) >= 2 else "moderate",
                specific_combinations=taboo_analysis,
            )
        )

    # ── 7th Lord Analysis ──
    seventh_lord_house = 0  # Initialize before conditional block
    seventh_lord = ""
    seventh_house_sign = ""
    if lagna in SIGN_ORDER:
        lagna_idx = SIGN_ORDER.index(lagna)
        seventh_house_sign = SIGN_ORDER[(lagna_idx + 6) % 12]
        seventh_lord = SIGN_LORDS.get(seventh_house_sign, "")
        seventh_lord_data = planet_details.get(seventh_lord, {})
        seventh_lord_house = (
            _get_house(seventh_lord_data.get("sign", ""), lagna)
            if seventh_lord_data.get("sign")
            else 0
        )

        if seventh_lord in SEVENTH_LORD_ANALYSIS:
            sl_info = SEVENTH_LORD_ANALYSIS[seventh_lord]
            seventh_lord_insights.append(
                RelationshipInsight(
                    category="7th House Lord",
                    planet=seventh_lord,
                    house=seventh_lord_house,
                    sign=seventh_lord_data.get("sign", ""),
                    analysis_type="spouse_nature",
                    title=f"7th Lord {seventh_lord} in {SIGN_NAMES.get(seventh_lord_data.get('sign', ''), seventh_lord_data.get('sign', ''))} ({seventh_lord_house}{_get_suffix(seventh_lord_house)} House)",
                    description=sl_info.get("spouse_nature", ""),
                    classical_reference="BPHS Ch 33 — 7th lord placement analysis",
                    strength_indicator="strong"
                    if seventh_lord_house in (1, 4, 5, 7, 9, 10)
                    else "moderate"
                    if seventh_lord_house in (2, 3, 11)
                    else "challenging",
                    specific_combinations=[
                        f"Relationship Dynamic: {sl_info.get('relationship_dynamic', '')}",
                        f"Intimacy Pattern: {sl_info.get('intimacy', '')}",
                        f"Timing: {sl_info.get('timing', '')}",
                    ],
                )
            )

    # ── Rahu-Ketu Axis Analysis ──
    rahu_house = _get_house(rahu_sign, lagna) if rahu_sign else 0
    ketu_house = _get_house(ketu_sign, lagna) if ketu_sign else 0

    axis_key = f"RAHU_{rahu_house}_KETU_{ketu_house}"
    if axis_key in RAHU_KETU_RELATIONSHIP:
        rk_info = RAHU_KETU_RELATIONSHIP[axis_key]
        rahu_ketu_insights.append(
            RelationshipInsight(
                category="Rahu-Ketu Axis",
                planet="RAHU-KETU",
                house=rahu_house,
                sign=rahu_sign,
                analysis_type="axis_pattern",
                title=f"Rahu in House {rahu_house} — Ketu in House {ketu_house}",
                description=rk_info.get("pattern", ""),
                classical_reference="BPHS Ch 41 — Rahu-Ketu axis effects on relationships",
                strength_indicator="challenging"
                if "High" in rk_info.get("affair_risk", "")
                else "moderate",
                specific_combinations=[
                    f"Intimacy Effect: {rk_info.get('intimacy_effect', '')}",
                    f"Risk Indicator: {rk_info.get('affair_risk', '')}",
                ],
            )
        )

    # ── Classical Combinations ──
    # Check for specific relationship-related yogas
    for yoga in yogas:
        yoga_name = yoga.get("yoga_name", "")
        if yoga_name in ("Gajakesari", "Dhana", "Raja"):
            classical_combinations.append(
                RelationshipInsight(
                    category="Classical Yoga",
                    planet=", ".join(yoga.get("involved_planets", [])),
                    analysis_type="yoga_effect",
                    title=f"{yoga_name} Yoga — {yoga.get('status', '')}",
                    description=f"This yoga affects overall life quality including relationships. Status: {yoga.get('status', '')}.",
                    classical_reference=f"BPHS — {yoga_name} Yoga",
                    strength_indicator="strong" if yoga.get("status") == "FORMED" else "weakened",
                )
            )

    # Check for Venus-Mars conjunction or aspect
    if venus_sign and mars_sign and venus_sign == mars_sign:
        classical_combinations.append(
            RelationshipInsight(
                category="Venus-Mars Conjunction",
                planet="VENUS-MARS",
                house=venus_house,
                sign=venus_sign,
                analysis_type="passion_indicator",
                title=f"Venus-Mars Conjunction in {SIGN_NAMES.get(venus_sign, venus_sign)}",
                description="Venus and Mars in the same sign create extremely high physical passion and sexual magnetism. This is one of the strongest indicators of intense romantic and physical attraction.",
                classical_reference="BPHS Ch 36 — Venus-Mars conjunction effects",
                strength_indicator="strong",
                specific_combinations=[
                    "High physical chemistry and sexual compatibility",
                    "Intense romantic attraction that can be overwhelming",
                    "Risk of obsessive or aggressive romantic patterns",
                ],
            )
        )

    # Check for Venus-Mars aspect
    if venus_sign and mars_sign and venus_sign != mars_sign:
        v_deg = venus_data.get("degree_in_sign", 0)
        m_deg = mars_data.get("degree_in_sign", 0)
        is_asp, asp_type = _get_aspect_type(v_deg, m_deg)
        if is_asp:
            classical_combinations.append(
                RelationshipInsight(
                    category="Venus-Mars Aspect",
                    planet="VENUS-MARS",
                    analysis_type="passion_indicator",
                    title=f"Venus-Mars {asp_type} Aspect",
                    description=f"Venus and Mars in {asp_type} aspect create strong physical attraction across different life areas. The aspect type ({asp_type}) modifies how passion manifests.",
                    classical_reference="BPHS Ch 36 — Venus-Mars aspect effects",
                    strength_indicator="strong",
                )
            )

    # Check for Rahu-Venus combination (secret affairs indicator)
    if rahu_sign and venus_sign:
        rahu_house_for_check = _get_house(rahu_sign, lagna)
        venus_house_for_check = _get_house(venus_sign, lagna)
        if rahu_house_for_check in (7, 8, 12) or venus_house_for_check in (7, 8, 12):
            classical_combinations.append(
                RelationshipInsight(
                    category="Secret Relationship Indicator",
                    planet="RAHU-VENUS",
                    analysis_type="affair_indicator",
                    title="Rahu-Venus Affiliation in Sensitive Houses",
                    description=(
                        f"Rahu in House {rahu_house_for_check} and Venus in House {venus_house_for_check} "
                        f"create a pattern of unconventional or secret romantic tendencies. "
                        f"When Rahu occupies the 7th, 8th, or 12th house and Venus is similarly placed, "
                        f"there is a classical indication of attraction to forbidden or unconventional relationships."
                    ),
                    classical_reference="BPHS Ch 41 — Rahu's effects on Venus significations",
                    strength_indicator="challenging",
                    specific_combinations=[
                        f"Rahu in {rahu_house_for_check}{_get_suffix(rahu_house_for_check)} house amplifies Venusian desires in hidden or unconventional ways",
                        "May attract partners from different social/cultural backgrounds",
                        "Strong pull toward secretive or taboo romantic connections",
                    ],
                )
            )

    # ── Overall Assessment — 4-part psychological structure ──
    strong_count = sum(
        1
        for i in venus_insights + mars_insights + seventh_lord_insights
        if i.strength_indicator == "strong"
    )
    challenge_count = sum(
        1
        for i in venus_insights + mars_insights + seventh_lord_insights
        if i.strength_indicator == "challenging"
    )

    if strong_count > challenge_count:
        strength = "strong"
    elif challenge_count > strong_count:
        strength = "challenging"
    else:
        strength = "moderate"

    # Part 1: Psychological Foundation & Desire Nature
    venus_style = VENUS_HOUSE_INTIMACY.get(venus_house, {}).get("style", "")
    mars_style = MARS_HOUSE_INTIMACY.get(mars_house, {}).get("style", "")
    venus_strength = VENUS_HOUSE_INTIMACY.get(venus_house, {}).get("strength", "")
    mars_strength = MARS_HOUSE_INTIMACY.get(mars_house, {}).get("strength", "")

    psychological = (
        f"Your desire nature is shaped by Venus in {SIGN_NAMES.get(venus_sign, venus_sign)} (House {venus_house}) and "
        f"Mars in {SIGN_NAMES.get(mars_sign, mars_sign)} (House {mars_house}). "
        f"{venus_style} "
        f"{mars_style} "
        f"{venus_strength}. {mars_strength}."
    )

    # Part 2: Specific Behavioral Risk Factors & Triggers
    risk_factors = []
    # Dual-sign alignments
    dual_signs = ["MITHUNA", "KANYA", "DHANUSHA", "MEENA"]
    venus_dual = venus_sign in dual_signs
    mars_dual = mars_sign in dual_signs
    if venus_dual:
        risk_factors.append(
            f"Venus in dual sign {SIGN_NAMES.get(venus_sign, venus_sign)} creates parallel romantic options — "
            f"tendency toward multiple simultaneous attractions or indecision in partnerships."
        )
    if mars_dual:
        risk_factors.append(
            f"Mars in dual sign {SIGN_NAMES.get(mars_sign, mars_sign)} adds restless physical energy — "
            f"may pursue multiple physical outlets or change desires frequently."
        )

    # 8th/12th house activations
    if venus_house in (8, 12) or mars_house in (8, 12):
        houses_involved = [h for h in [venus_house, mars_house] if h in (8, 12)]
        risk_factors.append(
            f"Venus/Mars in {'/'.join(str(h) for h in houses_involved)} house activates secrecy and hidden dimensions — "
            f"attraction to forbidden, taboo, or clandestine romantic connections increases."
        )

    # Rahu afflictions
    rahu_house = _get_house(rahu_sign, lagna) if rahu_sign else 0
    if rahu_house in (7, 8, 12):
        risk_factors.append(
            f"Rahu in {rahu_house}{_get_suffix(rahu_house)} house amplifies obsessive tendencies in partnerships — "
            f"unconventional attraction patterns and potential for illusion in relationships."
        )

    # Severe afflictions
    if venus_house in (6, 8) and mars_house in (6, 8):
        risk_factors.append(
            f"Both Venus ({venus_house}{_get_suffix(venus_house)}) and Mars ({mars_house}{_get_suffix(mars_house)}) in Dusthana houses — "
            f"significant relationship friction. Patience and conscious effort required."
        )

    behavioral = (
        " ".join(risk_factors)
        if risk_factors
        else (
            "No severe behavioral risk factors detected. "
            "Venus and Mars placements show clear, uncomplicated desire patterns without hidden complications."
        )
    )

    # Part 3: Timing Windows & Vulnerability Cycles
    # Analyze 7th lord house for timing hints
    seventh_lord_house_str = (
        f"{seventh_lord_house}{_get_suffix(seventh_lord_house)}"
        if seventh_lord_house
        else "Unknown"
    )
    timing = (
        f"The 7th lord {seventh_lord} is placed in the {seventh_lord_house_str} house, indicating "
        f"{'strong partnership activation during its Dasha/AD periods' if seventh_lord_house in (1, 4, 5, 7, 9, 10) else 'delays or challenges in partnership timing — marriage or partnership events likely during favorable transits'}. "
    )
    if venus_house in (8, 12) or rahu_house in (7, 8, 12):
        timing += (
            "Vulnerability windows increase when transiting Rahu or Saturn aspects natal Venus or the 7th lord. "
            "During these periods, exercise caution in romantic decisions and avoid impulsive commitments."
        )
    else:
        timing += (
            "No major vulnerability windows detected in the current chart configuration. "
            "Relationships proceed with natural timing without forced acceleration."
        )

    # Part 4: The Protective Layer & Final Mitigation
    jupiter_data = planet_details.get("JUPITER", {})
    jupiter_sign = jupiter_data.get("sign", "")
    jupiter_house = _get_house(jupiter_sign, lagna) if jupiter_sign else 0
    jupiter_dignity = dignity_map.get("JUPITER", "Neutral") if dignity_map else "Neutral"

    protective_parts = []
    if jupiter_house in (1, 5, 7, 9, 11):
        protective_parts.append(
            f"Jupiter in {SIGN_NAMES.get(jupiter_sign, jupiter_sign)} (House {jupiter_house}) provides strong protective influence — "
            f"moral compass, wisdom in relationships, and dharmic guidance."
        )
    if "Exalted" in jupiter_dignity or "Own" in jupiter_dignity:
        protective_parts.append(
            f"Jupiter's {jupiter_dignity} dignity amplifies protective influence — strong spiritual and ethical foundation."
        )
    if not protective_parts:
        protective_parts.append(
            f"Jupiter in {SIGN_NAMES.get(jupiter_sign, jupiter_sign)} (House {jupiter_house}) provides moderate protective influence. "
            f"Spiritual practices and ethical living serve as the primary protective layer."
        )

    protective = " ".join(protective_parts)

    # ── DETAILED 4-Part Psychological Analysis (minimum 50 words per section) ──

    # Part 1: Psychological Foundation & Desire Nature (3-5 paragraphs)
    psychological = (
        f"PSYCHOLOGICAL FOUNDATION: Your desire nature is fundamentally shaped by the interplay between "
        f"Venus in {SIGN_NAMES.get(venus_sign, venus_sign)} (House {venus_house}) and Mars in "
        f"{SIGN_NAMES.get(mars_sign, mars_sign)} (House {mars_house}). "
        f"{venus_style} "
        f"{mars_style} "
        f"{venus_strength}. {mars_strength}. "
        f"This combination creates a specific psychological pattern where your romantic and physical "
        f"desires are expressed through the lens of these house placements. "
        f"The emotional wiring of your relationship nature is deeply influenced by how Venus and Mars "
        f"interact across the chart — whether they support each other through favorable aspects or "
        f"create tension through challenging positions. "
        f"Your subconscious attachment style, learned from early family dynamics and past-life patterns, "
        f"manifests through these planetary placements, creating predictable patterns in how you "
        f"attract, engage with, and maintain intimate relationships throughout your life."
    )

    # Part 2: Behavioral Risk Factors (3-5 sentences)
    behavioral = f"BEHAVIORAL RISK FACTORS: " + (
        " ".join(risk_factors)
        if risk_factors
        else (
            "No severe behavioral risk factors detected. "
            "Venus and Mars placements show clear, uncomplicated desire patterns without hidden complications. "
            "The native's romantic approach is straightforward and authentic, without the distortions that "
            "dual signs, dusthana placements, or Rahu afflictions can create. "
            "This clarity allows for healthy relationship dynamics and genuine emotional connection."
        )
    )

    # Part 3: Timing Windows (3-5 sentences)
    timing = (
        f"TIMING WINDOWS: The 7th lord {seventh_lord} is placed in the {seventh_lord_house_str} house, "
        f"indicating {'strong partnership activation during its Dasha/AD periods' if seventh_lord_house in (1, 4, 5, 7, 9, 10) else 'delays or challenges in partnership timing — marriage or partnership events likely during favorable transits'}. "
        f"Vulnerability windows increase when transiting Rahu or Saturn aspects natal Venus or the 7th lord. "
        f"During these periods, exercise caution in romantic decisions and avoid impulsive commitments. "
        f"The current chart configuration suggests {'relationship events will unfold naturally with divine timing' if seventh_lord_house in (1, 4, 5, 7, 9, 10) else 'patience is required, and the native should focus on personal growth while waiting for optimal partnership timing'}. "
        f"Understanding these cycles allows the native to prepare for challenging periods and capitalize "
        f"on favorable ones, creating a more conscious and intentional approach to romantic life."
    )

    # Part 4: Protective Layer (3-5 sentences)
    protective = (
        f"PROTECTIVE LAYER: "
        + (" ".join(protective_parts))
        + f" The combination of Jupiter's protective influence and the native's own spiritual practice "
        f"creates a powerful shield against relationship challenges. "
        f"When difficulties arise, the native should lean into Jupiterian qualities — wisdom, faith, "
        f"generosity, and ethical conduct — to navigate through turbulent times. "
        f"Regular spiritual practice, charitable acts, and mentoring relationships provide additional "
        f"protection and guidance during periods of relationship vulnerability."
    )

    overall = f"{psychological} {behavioral} {timing} {protective}"

    # Intimacy profile — specific, not truncated
    intimacy_profile = (
        f"Venus in {SIGN_NAMES.get(venus_sign, venus_sign)} (House {venus_house}): {venus_style} "
        f"Mars in {SIGN_NAMES.get(mars_sign, mars_sign)} (House {mars_house}): {mars_style}"
    )

    # Debug prints
    analysis_sections = []
    if psychological:
        analysis_sections.append("Psychological Foundation")
    if behavioral:
        analysis_sections.append("Behavioral Risk Factors")
    if timing:
        analysis_sections.append("Timing Windows")
    if protective:
        analysis_sections.append("Protective Layer")
    total_words = len(overall.split())
    print(f"RELATIONSHIP DEBUG: Generated {len(analysis_sections)} detailed analysis sections")
    print(f"RELATIONSHIP DEBUG: Total word count: {total_words} words")

    return RelationshipAnalysisResult(
        lagna=lagna,
        venus_analysis=venus_insights,
        mars_analysis=mars_insights,
        seventh_lord_analysis=seventh_lord_insights,
        rahu_ketu_analysis=rahu_ketu_insights,
        classical_combinations=classical_combinations,
        overall_assessment=overall,
        intimacy_profile=intimacy_profile,
        relationship_strength=strength,
    )


def _get_suffix(n: int) -> str:
    if n >= 11 and n <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def relationship_analysis_to_dict(result: RelationshipAnalysisResult) -> dict[str, Any]:
    """Convert RelationshipAnalysisResult to JSON-serializable dict."""

    def _insight(i: RelationshipInsight) -> dict[str, Any]:
        return {
            "category": i.category,
            "planet": i.planet,
            "house": i.house,
            "sign": i.sign,
            "analysis_type": i.analysis_type,
            "title": i.title,
            "description": i.description,
            "classical_reference": i.classical_reference,
            "strength_indicator": i.strength_indicator,
            "specific_combinations": i.specific_combinations,
        }

    return {
        "lagna": result.lagna,
        "venus_analysis": [_insight(i) for i in result.venus_analysis],
        "mars_analysis": [_insight(i) for i in result.mars_analysis],
        "seventh_lord_analysis": [_insight(i) for i in result.seventh_lord_analysis],
        "rahu_ketu_analysis": [_insight(i) for i in result.rahu_ketu_analysis],
        "classical_combinations": [_insight(i) for i in result.classical_combinations],
        "overall_assessment": result.overall_assessment,
        "intimacy_profile": result.intimacy_profile,
        "relationship_strength": result.relationship_strength,
    }
