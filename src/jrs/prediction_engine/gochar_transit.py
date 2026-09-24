"""Gochar Transit Prediction Engine — Current Sky analysis.

Analyzes the current planetary positions in the sky:
  1. Transiting planets' house placements from Lagna and Moon
  2. Transit-to-Transit aspects (e.g., Saturn aspecting Jupiter)
  3. Combined predictions from house placements + transit geometries

All outputs are deterministic — no LLM, no randomness.
NO natal planet references — pure current-cosmic-dynamics analysis.
Reference: BPHS Ch 45-46, Phaladeepika Ch 12 (Transit Effects).
"""

from __future__ import annotations

import json as _json
import os as _os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

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

# ── Benefic / Malefic classification ─────────────────────────────────────────

BENEFICS: frozenset[str] = frozenset({"JUPITER", "VENUS", "MOON", "MERCURY"})
MALEFICS: frozenset[str] = frozenset({"SUN", "MARS", "SATURN", "RAHU", "KETU"})

# ── House significance keywords ──────────────────────────────────────────────

HOUSE_KEYWORDS: dict[int, dict[str, str]] = {
    1: {
        "domain": "Self & Personality",
        "effect": "physical health, vitality, appearance, and overall personality",
    },
    2: {
        "domain": "Wealth & Family",
        "effect": "family finances, speech, food, and accumulated wealth",
    },
    3: {
        "domain": "Courage & Siblings",
        "effect": "courage, communication, short journeys, and sibling relationships",
    },
    4: {
        "domain": "Home & Happiness",
        "effect": "domestic peace, property, vehicles, mother's health, and inner happiness",
    },
    5: {
        "domain": "Children & Creativity",
        "effect": "children, education, creative intelligence, and past-life merit",
    },
    6: {
        "domain": "Health & Obstacles",
        "effect": "diseases, enemies, debts, litigation, and service",
    },
    7: {
        "domain": "Marriage & Partnership",
        "effect": "spouse, business partnerships, sexual relationships, and public dealings",
    },
    8: {
        "domain": "Longevity & Transformation",
        "effect": "longevity, sudden events, hidden matters, insurance, and occult",
    },
    9: {
        "domain": "Fortune & Dharma",
        "effect": "luck, father, higher learning, long travel, and spiritual inclinations",
    },
    10: {
        "domain": "Career & Status",
        "effect": "profession, reputation, authority, karma, and social standing",
    },
    11: {
        "domain": "Gains & Aspirations",
        "effect": "income, gains, older siblings, fulfillment of desires, and social networks",
    },
    12: {
        "domain": "Loss & Liberation",
        "effect": "expenses, losses, foreign travel, sleep, isolation, and spiritual liberation",
    },
}

# ── Transit effects by planet per house (classical BPHS rules) ──────────────
# Key: (transit_planet, house_from_lagna) → prediction text

TRANSIT_EFFECTS: dict[tuple[str, int], str] = {
    # ── Jupiter Transit ───────────────────────────────────────────────
    (
        "JUPITER",
        1,
    ): "Jupiter transit through the 1st house brings wisdom, good health, new opportunities, and overall auspiciousness. Enhanced confidence and spiritual growth.",
    (
        "JUPITER",
        2,
    ): "Jupiter in the 2nd house from Lagna promises wealth accumulation, harmonious family life, eloquent speech, and fulfillment of desires through accumulated resources.",
    (
        "JUPITER",
        3,
    ): "Jupiter in the 3rd house reduces its natural beneficence. Short journeys, increased communication, but courage may be tested. Sibling relationships need attention.",
    (
        "JUPITER",
        4,
    ): "Jupiter transit through the 4th house brings domestic happiness, property gains, vehicle acquisition, and peace of mind. Mother's health improves.",
    (
        "JUPITER",
        5,
    ): "Jupiter in the 5th house is highly auspicious — educational success, progeny blessings, creative breakthroughs, and strong romantic prospects.",
    (
        "JUPITER",
        6,
    ): "Jupiter in the 6th house creates obstacles in legal matters, health concerns, and increase in enemies. Debts may arise. Remedial measures recommended.",
    (
        "JUPITER",
        7,
    ): "Jupiter transit through the 7th house brings marital harmony, business partnerships, and public recognition. Spouse benefits significantly.",
    (
        "JUPITER",
        8,
    ): "Jupiter in the 8th house brings sudden transformations, hidden gains, inheritance possibilities, and deep spiritual insights. Health requires monitoring.",
    (
        "JUPITER",
        9,
    ): "Jupiter in its natural 9th house position is supremely auspicious — fortune, father's blessings, pilgrimages, higher education, and dharmic fulfillment.",
    (
        "JUPITER",
        10,
    ): "Jupiter transit through the 10th house brings career advancement, professional recognition, authority expansion, and karma fulfillment.",
    (
        "JUPITER",
        11,
    ): "Jupiter in the 11th house is excellent for income growth, network expansion, desire fulfillment, and gains through elder siblings or mentors.",
    (
        "JUPITER",
        12,
    ): "Jupiter in the 12th house brings expenses on spiritual pursuits, foreign travel, hospitalization possibilities, but also spiritual liberation.",
    # ── Saturn Transit ────────────────────────────────────────────────
    (
        "SATURN",
        1,
    ): "Saturn transit through the 1st house (beginning of Sade Sati if Moon in 1st) brings health challenges, reduced confidence, and increased responsibilities.",
    (
        "SATURN",
        2,
    ): "Saturn in the 2nd house causes financial restructuring, family tensions, speech-related issues, and dietary restrictions. Sade Sati peak phase.",
    (
        "SATURN",
        3,
    ): "Saturn in the 3rd house is favorable — increased courage, successful short journeys, sibling support, and communication skills improve.",
    (
        "SATURN",
        4,
    ): "Saturn in the 4th house brings domestic upheaval, property disputes, vehicle issues, and emotional distance from mother. Sade Sati concluding phase.",
    (
        "SATURN",
        5,
    ): "Saturn in the 5th house delays progeny, creates educational obstacles, reduces creative output, and tests romantic relationships.",
    (
        "SATURN",
        6,
    ): "Saturn in the 6th house is highly favorable — victory over enemies, disease recovery, debt clearance, and litigation success.",
    (
        "SATURN",
        7,
    ): "Saturn in the 7th house brings delays in marriage, coldness in partnerships, spouse's health concerns, and mature relationship dynamics.",
    (
        "SATURN",
        8,
    ): "Saturn in the 8th house brings longevity concerns, sudden health issues, inheritance matters, and deep transformative experiences.",
    (
        "SATURN",
        9,
    ): "Saturn in the 9th house creates obstacles in fortune, father's health concerns, delays in higher education, and spiritual tests.",
    (
        "SATURN",
        10,
    ): "Saturn in the 10th house brings career restructuring, professional setbacks leading to growth, authority through perseverance.",
    (
        "SATURN",
        11,
    ): "Saturn in the 11th house is excellent for long-term income growth, network building, and gradual fulfillment of desires.",
    (
        "SATURN",
        12,
    ): "Saturn in the 12th house brings expenses, isolation, foreign connections, spiritual awakening, and release from material bonds.",
    # ── Rahu Transit ──────────────────────────────────────────────────
    (
        "RAHU",
        1,
    ): "Rahu transit through the 1st house brings confusion in identity, unconventional approaches, foreign connections, and obsessive self-focus.",
    (
        "RAHU",
        2,
    ): "Rahu in the 2nd house creates unconventional wealth accumulation, foreign food/diet changes, speech controversies, and family disruptions.",
    (
        "RAHU",
        3,
    ): "Rahu in the 3rd house brings courage for unconventional pursuits, short foreign journeys, and communication breakthroughs through technology.",
    (
        "RAHU",
        4,
    ): "Rahu in the 4th house creates domestic unrest, property controversies, vehicle issues, and emotional detachment from homeland.",
    (
        "RAHU",
        5,
    ): "Rahu in the 5th house brings unconventional romance, creative innovation, speculative gains, but progeny-related concerns.",
    (
        "RAHU",
        6,
    ): "Rahu in the 6th house is favorable — victory over enemies, disease recovery, and success through unconventional methods.",
    (
        "RAHU",
        7,
    ): "Rahu in the 7th house brings unconventional partnerships, foreign spouse possibilities, obsessive relationships, and sexual experimentation.",
    (
        "RAHU",
        8,
    ): "Rahu in the 8th house brings hidden enemies, occult interests, sudden transformations, secret affairs, and longevity concerns.",
    (
        "RAHU",
        9,
    ): "Rahu in the 9th house creates unorthodox spiritual practices, foreign travel for learning, and conflicts with traditional beliefs.",
    (
        "RAHU",
        10,
    ): "Rahu in the 10th house brings career in unconventional fields, foreign professional connections, and reputation through innovation.",
    (
        "RAHU",
        11,
    ): "Rahu in the 11th house brings gains through unconventional networks, foreign income sources, and fulfillment of unusual desires.",
    (
        "RAHU",
        12,
    ): "Rahu in the 12th house brings expenses on foreign items, secret enemies, sleep disturbances, and spiritual experiences through isolation.",
    # ── Ketu Transit ──────────────────────────────────────────────────
    (
        "KETU",
        1,
    ): "Ketu transit through the 1st house brings spiritual detachment, health issues, confusion about self-identity, and past-life karma resolution.",
    (
        "KETU",
        2,
    ): "Ketu in the 2nd house creates detachment from wealth, dietary changes, family disputes, and speech-related issues.",
    (
        "KETU",
        3,
    ): "Ketu in the 3rd house reduces courage, creates communication difficulties, but enhances intuitive abilities and spiritual writing.",
    (
        "KETU",
        4,
    ): "Ketu in the 4th house brings domestic detachment, property losses, emotional distance from mother, and spiritual home-seeking.",
    (
        "KETU",
        5,
    ): "Ketu in the 5th house creates detachment from children, educational obstacles, but enhances past-life spiritual merit and intuition.",
    (
        "KETU",
        6,
    ): "Ketu in the 6th house brings health concerns, hidden enemies, but also victory through spiritual remedies and karmic resolution.",
    (
        "KETU",
        7,
    ): "Ketu in the 7th house creates detachment from partnerships, unconventional marriage dynamics, and spiritual approach to relationships.",
    (
        "KETU",
        8,
    ): "Ketu in the 8th house brings sudden spiritual transformations, occult experiences, health crises, and karmic debt resolution.",
    (
        "KETU",
        9,
    ): "Ketu in the 9th house brings detachment from traditional religion, unconventional spirituality, and father-related concerns.",
    (
        "KETU",
        10,
    ): "Ketu in the 10th house creates career detachment, unconventional profession, and spiritual approach to work.",
    (
        "KETU",
        11,
    ): "Ketu in the 11th house brings detachment from social networks, unusual gains, and spiritual community involvement.",
    (
        "KETU",
        12,
    ): "Ketu in the 12th house is highly spiritual — moksha potential, foreign isolation, dream experiences, and liberation from material bonds.",
    # ── Mars Transit ──────────────────────────────────────────────────
    (
        "MARS",
        1,
    ): "Mars transit through the 1st house increases physical energy, courage, and competitive drive. Risk of accidents and inflammation.",
    (
        "MARS",
        2,
    ): "Mars in the 2nd house brings aggressive speech, financial disputes, dietary heat, and conflicts within family.",
    (
        "MARS",
        3,
    ): "Mars in the 3rd house is excellent — maximum courage, successful short journeys, sibling support, and communication breakthroughs.",
    (
        "MARS",
        4,
    ): "Mars in the 4th house creates domestic unrest, property disputes, vehicle accidents, and conflicts with mother.",
    (
        "MARS",
        5,
    ): "Mars in the 5th house brings passionate romance, creative energy, speculative gains, but progeny-related concerns.",
    (
        "MARS",
        6,
    ): "Mars in the 6th house is highly favorable — victory over enemies, disease recovery, litigation success, and competitive wins.",
    (
        "MARS",
        7,
    ): "Mars in the 7th house (Manglik transit) brings passion but also conflicts in marriage, sexual intensity, and partnership disputes.",
    (
        "MARS",
        8,
    ): "Mars in the 8th house brings sudden accidents, surgeries, sexual intensity, hidden enemies, and transformative crises.",
    (
        "MARS",
        9,
    ): "Mars in the 9th house creates conflicts with father/guru, religious disputes, and aggressive pursuit of higher knowledge.",
    (
        "MARS",
        10,
    ): "Mars in the 10th house brings career aggression, professional conflicts, authority expansion, and karmic intensity.",
    (
        "MARS",
        11,
    ): "Mars in the 11th house brings income through aggressive pursuits, network conflicts, and competitive gains.",
    (
        "MARS",
        12,
    ): "Mars in the 12th house brings expenses on litigation, sexual desires, foreign travel, and spiritual warrior energy.",
    # ── Venus Transit ─────────────────────────────────────────────────
    (
        "VENUS",
        1,
    ): "Venus transit through the 1st house brings beauty, charm, romantic opportunities, and artistic expression.",
    (
        "VENUS",
        2,
    ): "Venus in the 2nd house brings wealth through luxury goods, harmonious family life, and eloquent speech.",
    (
        "VENUS",
        3,
    ): "Venus in the 3rd house brings creative communication, artistic short journeys, and romantic correspondence.",
    (
        "VENUS",
        4,
    ): "Venus in the 4th house brings domestic happiness, property beautification, vehicle luxury, and mother's blessings.",
    (
        "VENUS",
        5,
    ): "Venus in the 5th house is highly romantic — passionate love affairs, creative breakthroughs, and progeny happiness.",
    (
        "VENUS",
        6,
    ): "Venus in the 6th house brings health concerns related to sugar/kidneys, legal disputes in partnerships, and service-oriented love.",
    (
        "VENUS",
        7,
    ): "Venus in the 7th house brings marital harmony, romantic partnerships, business success through partnerships, and sexual bliss.",
    (
        "VENUS",
        8,
    ): "Venus in the 8th house brings secret romantic affairs, hidden relationships, sexual intensity, and transformation through love.",
    (
        "VENUS",
        9,
    ): "Venus in the 9th house brings romantic fortune, love during travel, spiritual romance, and artistic higher learning.",
    (
        "VENUS",
        10,
    ): "Venus in the 10th house brings career in arts/beauty, professional charm, and success through creative industries.",
    (
        "VENUS",
        11,
    ): "Venus in the 11th house brings gains through arts, romantic social networks, and fulfillment of desires through beauty.",
    (
        "VENUS",
        12,
    ): "Venus in the 12th house brings secret romantic affairs, expenses on luxury, foreign romantic connections, and spiritual love.",
    # ── Mercury Transit ───────────────────────────────────────────────
    (
        "MERCURY",
        1,
    ): "Mercury transit through the 1st house brings intellectual clarity, communication skills, and analytical thinking.",
    (
        "MERCURY",
        2,
    ): "Mercury in the 2nd house brings financial intelligence, eloquent speech, and gains through writing/trade.",
    (
        "MERCURY",
        3,
    ): "Mercury in the 3rd house is excellent — communication mastery, successful short journeys, and sibling support.",
    (
        "MERCURY",
        4,
    ): "Mercury in the 4th house brings intellectual domestic environment, educational pursuits, and property-related communication.",
    (
        "MERCURY",
        5,
    ): "Mercury in the 5th house brings creative intelligence, educational success, and romantic communication.",
    (
        "MERCURY",
        6,
    ): "Mercury in the 6th house brings success in legal matters, health through diet management, and competitive intelligence.",
    (
        "MERCURY",
        7,
    ): "Mercury in the 7th house brings intellectual partnerships, business communication, and articulate spouse.",
    (
        "MERCURY",
        8,
    ): "Mercury in the 8th house brings research abilities, hidden knowledge, occult intelligence, and investigative skills.",
    (
        "MERCURY",
        9,
    ): "Mercury in the 9th house brings educational success, philosophical thinking, and communication with gurus.",
    (
        "MERCURY",
        10,
    ): "Mercury in the 10th house brings career in communication, intellectual profession, and professional networking.",
    (
        "MERCURY",
        11,
    ): "Mercury in the 11th house brings gains through communication, intellectual networks, and fulfillment of desires.",
    (
        "MERCURY",
        12,
    ): "Mercury in the 12th house brings expenses through communication, foreign travel, and spiritual intellectualism.",
    # ── Sun Transit ───────────────────────────────────────────────────
    (
        "SUN",
        1,
    ): "Sun transit through the 1st house brings vitality, confidence, authority, and health improvement.",
    (
        "SUN",
        2,
    ): "Sun in the 2nd house brings financial authority, family leadership, and gains through government.",
    (
        "SUN",
        3,
    ): "Sun in the 3rd house brings courage, successful short journeys, and communication authority.",
    (
        "SUN",
        4,
    ): "Sun in the 4th house reduces its beneficence — domestic authority issues, property concerns, and mother's health.",
    (
        "SUN",
        5,
    ): "Sun in the 5th house brings creative authority, educational success, and progeny-related prominence.",
    (
        "SUN",
        6,
    ): "Sun in the 6th house is favorable — victory over enemies, health improvement, and litigation success.",
    (
        "SUN",
        7,
    ): "Sun in the 7th house brings partnership authority, but ego conflicts in marriage and public dealings.",
    (
        "SUN",
        8,
    ): "Sun in the 8th house brings hidden authority, transformation through crisis, and longevity concerns.",
    (
        "SUN",
        9,
    ): "Sun in the 9th house brings dharmic authority, father's blessings, and educational prominence.",
    (
        "SUN",
        10,
    ): "Sun in the 10th house is supremely favorable — career peak, professional authority, and government recognition.",
    (
        "SUN",
        11,
    ): "Sun in the 11th house brings gains through authority, network leadership, and desire fulfillment.",
    (
        "SUN",
        12,
    ): "Sun in the 12th house brings expenses through authority, foreign connections, and spiritual illumination.",
}


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class TransitPrediction:
    """A single transit prediction."""

    transit_planet: str
    transit_sign: str
    transit_house: int  # House from Lagna
    aspect_type: str | None = None
    target_planet: str | None = None  # For transit-to-transit: the other planet
    target_sign: str | None = None  # For transit-to-transit: the other planet's sign
    target_house: int | None = None  # For transit-to-transit: other planet's house from Moon
    prediction: str = ""
    category: str = ""  # e.g., "House Transit", "Transit-to-Transit"
    severity: str = "neutral"  # "positive", "negative", "neutral", "mixed"
    # Dynamic state info
    retrograde: bool = False
    combust: bool = False
    dignity: str = ""  # Exalted, Debilitated, Own Sign, Moolatrikona, Friendly, Enemy
    nakshatra: str = ""
    nakshatra_lord: str = ""


@dataclass
class GocharTransitResult:
    """Complete gochar transit prediction result."""

    timestamp: str
    lagna: str
    moon_sign: str
    transit_positions: dict[str, dict[str, Any]]
    predictions: list[TransitPrediction]  # House placements
    transit_to_transit_aspects: list[TransitPrediction]  # Transit-to-transit aspects
    summary_by_planet: dict[str, list[TransitPrediction]]
    overall_assessment: str
    chandrasthamam_active: bool = False
    chandrasthamam_warning: str = ""


# ── Planet significations for transit-to-transit predictions ─────────────────

PLANET_SIGNIFICATIONS: dict[str, dict[str, str]] = {
    "SUN": {
        "domain": "authority, soul, vitality, government",
        "element": "fire",
        "nature": "hot and dry",
    },
    "MOON": {
        "domain": "mind, emotions, mother, public life",
        "element": "water",
        "nature": "cool and nourishing",
    },
    "MARS": {
        "domain": "energy, courage, siblings, property",
        "element": "fire",
        "nature": "hot and sharp",
    },
    "MERCURY": {
        "domain": "intellect, communication, trade, education",
        "element": "earth",
        "nature": "adaptable and analytical",
    },
    "JUPITER": {
        "domain": "wisdom, fortune, children, dharma",
        "element": "ether",
        "nature": "benefic and expansive",
    },
    "VENUS": {
        "domain": "love, beauty, luxury, partnerships",
        "element": "water",
        "nature": "benefic and sensual",
    },
    "SATURN": {
        "domain": "discipline, karma, longevity, obstacles",
        "element": "air",
        "nature": "malefic and transformative",
    },
    "RAHU": {
        "domain": "ambition, innovation, foreign connections, obsession",
        "element": "air",
        "nature": "amplifying and illusionary",
    },
    "KETU": {
        "domain": "spirituality, detachment, past-life, liberation",
        "element": "fire",
        "nature": "dissolving and liberating",
    },
}

# ── Transit-to-Transit aspect prediction templates ──────────────────────────
# Key: (planet_a, planet_b, aspect_type) → prediction template
# Fallback: generic template based on planet natures

_TRANSIT_ASPECT_TEMPLATES: dict[tuple[str, str, str], str] = {
    # ── Saturn aspects Jupiter (most important slow pair) ──
    ("SATURN", "JUPITER", "7th"): (
        "Saturn in {sign_a} forms a powerful 7th aspect with Jupiter in {sign_b}, creating a dynamic tension between discipline and expansion. "
        "This alignment structures Jupiter's naturally expansive energy, demanding careful planning before any major financial or educational ventures. "
        "The cosmic weather favors patience over haste — those who build solid foundations now will reap lasting rewards. "
        "Expect delays in legal matters and foreign travel, but deep, lasting wisdom gained through the process. "
        "Spiritual practices and ethical conduct are strongly supported during this transit geometry."
    ),
    ("SATURN", "JUPITER", "Conjunction"): (
        "Saturn conjunct Jupiter in {sign_b} merges discipline with wisdom, creating a rare window for structuring long-term goals. "
        "This conjunction tempers Jupiter's optimism with Saturn's realism, making it ideal for business planning, investments, and educational commitments. "
        "The combined energy supports methodical progress in career and dharmic pursuits. "
        "Relationships benefit from honest, mature communication. "
        "Avoid overextension — the restrictive nature of Saturn demands measured ambition."
    ),
    ("SATURN", "JUPITER", "5th"): (
        "Saturn's 5th aspect on Jupiter in {sign_b} activates house matters related to creativity, children, and education with karmic weight. "
        "This aspect brings the need for disciplined creative expression and responsible approach to progeny-related matters. "
        "Financial gains through patient speculation and long-term educational investments are favored. "
        "Romantic relationships may face tests of commitment and loyalty. "
        "Spiritual practices focused on past-life resolution are particularly potent now."
    ),
    ("SATURN", "JUPITER", "9th"): (
        "Saturn's 9th aspect on Jupiter in {sign_b} influences higher learning, fortune, and spiritual inclinations. "
        "This aspect creates delays but ultimately deeper understanding in philosophical and educational pursuits. "
        "Father's health and mentor relationships require attention and care. "
        "Long-distance travel may face obstacles but yields transformative experiences. "
        "Dharmic discipline and adherence to tradition are strongly supported."
    ),
    # ── Mars aspects key planets ──
    ("MARS", "VENUS", "7th"): (
        "Mars aspects Venus with its powerful 7th aspect, igniting passion in romantic and creative domains. "
        "This transit geometry intensifies desires and brings boldness to relationship matters, though impulsiveness must be managed. "
        "Creative projects receive a burst of energetic inspiration. "
        "Property and vehicle matters may see competitive dynamics. "
        "Channel this fiery energy into disciplined artistic expression for best results."
    ),
    ("MARS", "VENUS", "Conjunction"): (
        "Mars conjunct Venus creates a potent blend of desire and passion, energizing romantic, creative, and luxury-related matters. "
        "This conjunction favors bold romantic gestures, artistic endeavors, and passionate creative projects. "
        "However, the combative nature of Mars can create friction in partnerships if patience is lacking. "
        "Financial gains through creative industries or partnership ventures are indicated. "
        "Physical energy is heightened — excellent for sports and competitive activities."
    ),
    ("MARS", "MERCURY", "7th"): (
        "Mars aspecting Mercury sharpens communication with directness and courage. "
        "This aspect favors assertive negotiation, competitive business strategies, and bold intellectual pursuits. "
        "However, speech may become harsh or argumentative if not carefully modulated. "
        "Short journeys and sibling-related matters receive energetic activation. "
        "Write, speak, and decide with conviction, but avoid haste in important documents."
    ),
    ("MARS", "SUN", "7th"): (
        "Mars aspecting the Sun amplifies authority, vitality, and leadership qualities. "
        "This powerful 7th aspect energizes government-related matters and professional authority. "
        "Physical energy and competitive drive peak during this alignment. "
        "Health requires monitoring — inflammation and fevers are possible if body heat is not managed. "
        "Career boldness is rewarded, but ego clashes with authority figures should be handled diplomatically."
    ),
    # ── Jupiter aspects key planets ──
    ("JUPITER", "VENUS", "7th"): (
        "Jupiter's 7th aspect on Venus creates a harmonious blend of wisdom and beauty, favoring romantic partnerships and creative abundance. "
        "This transit geometry brings fortune through artistic endeavors and luxury businesses. "
        "Marriage and business partnerships receive dharmic blessings. "
        "Educational pursuits in arts, music, or design are particularly favored. "
        "Financial growth through ethical business practices and partnership harmony is strongly indicated."
    ),
    ("JUPITER", "VENUS", "Conjunction"): (
        "Jupiter conjunct Venus brings exceptional fortune in love, art, and material comfort. "
        "This rare alignment favors marriage celebrations, creative breakthroughs, and financial prosperity. "
        "Educational and spiritual pursuits benefit from Venus's creative grace. "
        "Luxury investments and property acquisitions are well-starred. "
        "This is one of the most auspicious transit geometries for relationship harmony and artistic expression."
    ),
    ("JUPITER", "MERCURY", "7th"): (
        "Jupiter aspecting Mercury enhances intellectual clarity with philosophical depth. "
        "This aspect favors educational achievements, business negotiations, and scholarly writing. "
        "Communication becomes more thoughtful and expansive — ideal for teaching and advisory roles. "
        "Financial intelligence peaks, making this excellent for strategic planning. "
        "Spiritual learning and scriptural study are particularly rewarding."
    ),
    # ── Saturn aspects inner planets ──
    ("SATURN", "VENUS", "7th"): (
        "Saturn's 7th aspect on Venus tempers romantic ideals with mature responsibility. "
        "Relationships undergo restructuring — superficial connections dissolve while deep commitments strengthen. "
        "Financial caution is advised in luxury spending and partnership investments. "
        "Creative work benefits from disciplined, methodical effort rather than spontaneous inspiration. "
        "Long-term relationship foundations built now will prove enduring."
    ),
    ("SATURN", "MARS", "7th"): (
        "Saturn aspects Mars with its 7th aspect, creating a tension between action and restraint. "
        "This aspect demands patience in matters requiring courage and physical energy. "
        "Property disputes and sibling conflicts require diplomatic resolution rather than confrontation. "
        "Professional competition favors those who plan methodically rather than act impulsively. "
        "Health benefits from structured exercise and careful management of body heat."
    ),
    ("SATURN", "MERCURY", "7th"): (
        "Saturn's aspect on Mercury brings depth and seriousness to communication and intellectual matters. "
        "Business contracts and legal documents require extra scrutiny and patient review. "
        "Educational pursuits become more structured and research-oriented. "
        "Siblings and neighbors may need support during challenging times. "
        "Slow, deliberate thinking produces better results than rapid-fire decision making."
    ),
    # ── Rahu/Ketu aspects ──
    ("RAHU", "JUPITER", "7th"): (
        "Rahu's 7th aspect on Jupiter creates unconventional wisdom and innovative spiritual practices. "
        "This aspect may bring foreign mentors, unorthodox educational experiences, or sudden fortune through unexpected channels. "
        "Children-related matters may face unusual developments requiring flexible responses. "
        "Speculative gains are possible but come with inherent illusion — verify all information carefully. "
        "Spiritual growth through breaking traditional boundaries is strongly supported."
    ),
    ("KETU", "JUPITER", "7th"): (
        "Ketu's 7th aspect on Jupiter detaches material ambitions and directs energy toward spiritual liberation. "
        "This transit geometry favors meditation, spiritual study, and charitable giving over material acquisition. "
        "Children and educational matters may require release of attachment to specific outcomes. "
        "Fortune comes through letting go rather than pursuing. "
        "Past-life spiritual merit activates powerfully now, guiding toward dharmic fulfillment."
    ),
    ("RAHU", "SATURN", "7th"): (
        "Rahu aspecting Saturn amplifies karmic lessons and accelerates transformative restructuring. "
        "Career disruptions may feel sudden but serve long-term evolutionary purposes. "
        "Foreign connections and unconventional professional paths are activated. "
        "Patience is tested more intensely — the usual Saturnian discipline becomes both more necessary and more difficult. "
        "Health requires extra vigilance, especially regarding chronic conditions."
    ),
}


# ── Engine ───────────────────────────────────────────────────────────────────


def _get_house(planet_sign: str, lagna: str) -> int:
    """Compute house number from planet's sign and lagna."""
    try:
        p_idx = SIGN_ORDER.index(planet_sign)
        l_idx = SIGN_ORDER.index(lagna)
        return ((p_idx - l_idx) % 12) + 1
    except (ValueError, IndexError):
        return 0


def _check_aspect(transit_deg: float, natal_deg: float) -> tuple[bool, str, float]:
    """Check if transit planet aspects natal planet. Returns (is_aspect, type, orb)."""
    diff = abs(transit_deg - natal_deg)
    if diff > 180:
        diff = 360 - diff

    # 7th aspect (~180°)
    orb_7th = abs(diff - 180.0)
    if orb_7th <= 12.0:
        return True, "7th", orb_7th

    # 5th aspect (~120°)
    orb_5th = abs(diff - 120.0)
    if orb_5th <= 12.0:
        return True, "5th", orb_5th

    # 9th aspect (~240° → 120° from other side)
    if orb_5th <= 12.0:
        return True, "9th", orb_5th

    # Conjunction (~0°)
    if diff <= 6.0:
        return True, "Conjunction", diff

    return False, "", 0.0


def _to_ecliptic(sign: str, deg_in_sign: float) -> float:
    """Convert sign + degree_in_sign to full ecliptic longitude (0-360°)."""
    if sign in SIGN_ORDER:
        return SIGN_ORDER.index(sign) * 30.0 + deg_in_sign
    return deg_in_sign


# ── Dignity lookup ─────────────────────────────────────────────────────────

EXALTATION: dict[str, str] = {
    "SUN": "KARKA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}
DEBILITATION: dict[str, str] = {
    "SUN": "TULA",
    "MOON": "VRISHCHIKA",
    "MARS": "KARKA",
    "MERCURY": "MEENA",
    "JUPITER": "MAKARA",
    "VENUS": "KANYA",
    "SATURN": "MESHA",
}
OWN_SIGNS: dict[str, list[str]] = {
    "SUN": ["SIMHA"],
    "MOON": ["KARKA"],
    "MARS": ["MESHA", "VRISHCHIKA"],
    "MERCURY": ["MITHUNA", "KANYA"],
    "JUPITER": ["DHANUSHA", "MEENA"],
    "VENUS": ["VRISHABHA", "TULA"],
    "SATURN": ["MAKARA", "KUMBHA"],
}
MOOLATRIKONA: dict[str, str] = {
    "SUN": "SIMHA",
    "MOON": "VRISHABHA",
    "MARS": "ARIES",
    "MERCURY": "VIRGO",
    "JUPITER": "SAGITTARIUS",
    "VENUS": "LIBRA",
    "SATURN": "AQUARIUS",
}


def _get_dignity(planet: str, sign: str) -> str:
    """Determine planetary dignity based on sign placement."""
    if planet in EXALTATION and EXALTATION[planet] == sign:
        return "Exalted"
    if planet in DEBILITATION and DEBILITATION[planet] == sign:
        return "Debilitated"
    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return "Own Sign"
    return ""


# ── Chandrasthamam Calculation ──────────────────────────────────────────────


def check_chandrasthamam(transit_moon_sign: str, natal_moon_sign: str) -> tuple[bool, str]:
    """Check if Chandrasthamam is active.

    Chandrasthamam occurs when the transiting Moon enters the 8th house
    from the natal Moon. This is an emotionally volatile period.

    Args:
        transit_moon_sign: Current transit Moon's sign.
        natal_moon_sign: Natal Moon's sign.

    Returns:
        (is_active, warning_message)
    """
    if not transit_moon_sign or not natal_moon_sign:
        return False, ""
    if transit_moon_sign not in SIGN_ORDER or natal_moon_sign not in SIGN_ORDER:
        return False, ""

    transit_idx = SIGN_ORDER.index(transit_moon_sign)
    natal_idx = SIGN_ORDER.index(natal_moon_sign)
    house_from_moon = ((transit_idx - natal_idx) % 12) + 1

    if house_from_moon == 8:
        warning = (
            "Chandrasthamam Active: The Moon is in the 8th house from your natal Moon, "
            "creating an illusional and emotionally volatile period. "
            "Avoid major decisions, travel, and starting new ventures today. "
            "Emotional upheaval, hidden fears, and psychological turbulence are heightened. "
            "Practice meditation, avoid confrontations, and maintain emotional equilibrium."
        )
        return True, warning

    return False, ""


# ── Nakshatra lookup for transit planets ────────────────────────────────────

_NAKSHATRA_ORDER: tuple[str, ...] = (
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

_NAKSHATRA_LORDS: dict[str, str] = {
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


def _get_nakshatra_from_longitude(longitude: float) -> tuple[str, str]:
    """Get Nakshatra and its lord from ecliptic longitude."""
    normalized = longitude % 360.0
    nak_span = 360.0 / 27.0
    nak_index = int(normalized / nak_span)
    nak = _NAKSHATRA_ORDER[nak_index % 27]
    lord = _NAKSHATRA_LORDS.get(nak, "")
    return nak, lord


# ── Nakshatra Parivartana Detection ────────────────────────────────────────


def detect_nakshatra_parivartana(
    planet_positions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect mutual Nakshatra lord exchanges between planets.

    A Nakshatra Parivartana occurs when:
    - Planet A is in a Nakshatra ruled by Planet B
    - Planet B is in a Nakshatra ruled by Planet A

    Args:
        planet_positions: {planet: {rashi, longitude, degree_in_sign, ...}}

    Returns:
        List of detected exchanges.
    """
    exchanges: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    # Compute Nakshatra for each planet
    planet_nakshatras: dict[str, tuple[str, str]] = {}  # planet -> (nakshatra, lord)
    for planet, data in planet_positions.items():
        lng = data.get("longitude", 0)
        if not lng:
            sign = data.get("rashi", "")
            deg = data.get("degree_in_sign", 0)
            if sign in SIGN_ORDER:
                lng = SIGN_ORDER.index(sign) * 30.0 + deg
        if lng:
            nak, lord = _get_nakshatra_from_longitude(lng)
            planet_nakshatras[planet] = (nak, lord)

    # Check for mutual exchanges
    planets = list(planet_nakshatras.keys())
    for i, pa in enumerate(planets):
        for pb in planets[i + 1 :]:
            nak_a, lord_a = planet_nakshatras[pa]
            nak_b, lord_b = planet_nakshatras[pb]

            # Mutual exchange: A's nakshatra lord is B, and B's nakshatra lord is A
            if lord_a.upper() == pb.upper() and lord_b.upper() == pa.upper():
                pair = tuple(sorted([pa, pb]))
                pair_typed: tuple[str, str] = (pair[0], pair[1])
                if pair_typed in seen_pairs:
                    continue
                seen_pairs.add(pair_typed)
                exchanges.append(
                    {
                        "planet_a": pa,
                        "planet_a_nakshatra": nak_a,
                        "planet_a_nakshatra_lord": lord_a,
                        "planet_b": pb,
                        "planet_b_nakshatra": nak_b,
                        "planet_b_nakshatra_lord": lord_b,
                        "type": "mutual",
                        "reading": (
                            f"Nakshatra Parivartana between {pa} and {pb}: "
                            f"{pa} sits in {nak_a} (lorded by {lord_a}), "
                            f"while {pb} sits in {nak_b} (lorded by {lord_b}). "
                            f"This mutual Nakshatra exchange creates a powerful karmic bond "
                            f"between the domains governed by these planets."
                        ),
                    }
                )

    print(f"NAKSHATRA PARIVARTANA DEBUG: Detected {len(exchanges)} exchanges.")
    return exchanges


def _generate_transit_aspect_prediction(
    planet_a: str,
    sign_a: str,
    house_a_moon: int,
    planet_b: str,
    sign_b: str,
    house_b_moon: int,
    aspect_type: str,
) -> str:
    """Generate a 4-5 sentence prediction for a transit-to-transit aspect.

    Uses pre-defined templates for known pairs, falls back to dynamic generation.
    NO natal planet references — pure current-cosmic-dynamics analysis.
    """
    # Normalize planet order for template lookup
    pair_key = (planet_a, planet_b, aspect_type)
    pair_key_rev = (planet_b, planet_a, aspect_type)

    template = _TRANSIT_ASPECT_TEMPLATES.get(pair_key)
    if template is None:
        template = _TRANSIT_ASPECT_TEMPLATES.get(pair_key_rev)
    if template is not None:
        # Fill in the template with actual positions
        return template.format(
            sign_a=sign_a,
            sign_b=sign_b,
            house_a=house_a_moon,
            house_b=house_b_moon,
        )

    # ── Fallback: dynamic prediction generation ──
    sig_a = PLANET_SIGNIFICATIONS.get(planet_a, {})
    sig_b = PLANET_SIGNIFICATIONS.get(planet_b, {})
    domain_a = sig_a.get("domain", "cosmic matters")
    domain_b = sig_b.get("domain", "cosmic matters")
    nature_a = sig_a.get("nature", "unique")
    nature_b = sig_b.get("nature", "unique")

    is_benefic_a = planet_a in BENEFICS
    is_benefic_b = planet_b in BENEFICS
    is_malefic_a = planet_a in MALEFICS
    is_malefic_b = planet_b in MALEFICS

    if aspect_type == "Conjunction":
        interaction = "merging their energies"
        if is_benefic_a and is_benefic_b:
            quality = "creating an especially auspicious alignment"
        elif is_malefic_a and is_malefic_b:
            quality = "intensifying challenging cosmic currents"
        elif (is_benefic_a and is_malefic_b) or (is_malefic_a and is_benefic_b):
            quality = "balancing expansion with restriction, creating productive tension"
        else:
            quality = "blending their distinct influences into a unified cosmic force"
    elif aspect_type == "7th":
        interaction = "forming a powerful opposition aspect"
        quality = "creating dynamic polarity between the domains of {domain_a} and {domain_b}"
    elif aspect_type == "5th":
        interaction = "creating a harmonious trine aspect"
        quality = "facilitating flow between the realms of {domain_a} and {domain_b}"
    elif aspect_type == "9th":
        interaction = "forming a flowing trine aspect"
        quality = "enhancing natural alignment between {domain_a} and {domain_b}"
    else:
        interaction = "interacting through cosmic geometry"
        quality = "influencing the balance between {domain_a} and {domain_b}"

    # Build readable aspect description
    if aspect_type == "Conjunction":
        aspect_desc = f"{planet_a} conjuncts {planet_b} in {sign_b}"
    else:
        aspect_desc = f"{planet_a}'s {aspect_type} aspect reaches {planet_b} in {sign_b}"

    pred = (
        f"With {planet_a} in {sign_a} (house {house_a_moon} from Moon) "
        f"{interaction} {planet_b} in {sign_b} (house {house_b_moon} from Moon), "
        f"the current cosmic weather emphasizes the interplay of {domain_a} and {domain_b}. "
        f"{planet_a}'s {nature_a} quality combines with {planet_b}'s {nature_b} nature, "
        f"creating conditions that influence life areas governed by these planetary forces. "
    )
    if quality:
        pred += f"This alignment is {quality.format(domain_a=domain_a, domain_b=domain_b)}, "
    pred += (
        f"favoring those who understand the underlying cosmic dynamics. "
        f"Awareness of this transit geometry allows for deliberate alignment with prevailing energies."
    )
    return pred


def compute_gochar_transits(
    natal_lagna: str,
    transit_positions: dict[str, dict[str, Any]],
    moon_sign: str = "",
    natal_planet_details: dict[str, dict[str, Any]] | None = None,
    parivartana_yogas: list[dict[str, Any]] | None = None,
    natal_aspects: list[dict[str, Any]] | None = None,
) -> GocharTransitResult:
    """Compute gochar transit predictions focused on the current sky.

    Analyzes:
      1. Transiting planets' house placements from Lagna AND Moon
      2. Transit-to-Transit aspects (aspects between transiting planets)

    Args:
        natal_lagna: Natal Lagna sign (for house calculations)
        transit_positions: Current transit positions {planet: {rashi, degree_in_sign, longitude, ...}}
        moon_sign: Natal Moon sign (for house-from-Moon calculations)
        natal_planet_details: (unused, kept for API compatibility)
        parivartana_yogas: (unused, kept for API compatibility)
        natal_aspects: (unused, kept for API compatibility)

    Returns:
        GocharTransitResult with all predictions
    """
    predictions: list[TransitPrediction] = []
    transit_aspect_predictions: list[TransitPrediction] = []
    effective_moon = moon_sign or natal_lagna

    # ── Chandrasthamam Check ──
    transit_moon = transit_positions.get("MOON", {})
    transit_moon_sign = transit_moon.get("rashi", "")
    chandrasthamam_active, chandrasthamam_warning = check_chandrasthamam(
        transit_moon_sign, effective_moon
    )
    print(
        f"CHANDRASTHAMAM DEBUG: Transit Moon={transit_moon_sign}, Natal Moon={effective_moon}, Active={chandrasthamam_active}"
    )

    # ── Step 1: Transit planet house placements from Lagna ──
    for t_planet, t_data in transit_positions.items():
        t_sign = t_data.get("rashi", "")
        if not t_sign:
            continue
        t_house = _get_house(t_sign, natal_lagna)
        if t_house < 1 or t_house > 12:
            continue

        effect_text = TRANSIT_EFFECTS.get((t_planet, t_house), "")
        if not effect_text:
            continue

        # Determine severity
        is_benefic = t_planet in BENEFICS
        severity = "positive" if is_benefic else "negative"
        if t_planet in BENEFICS and t_house in (3, 6, 10, 11):
            severity = "mixed"
        if t_planet in MALEFICS and t_house in (3, 6, 10, 11):
            severity = "positive"

        domain = HOUSE_KEYWORDS.get(t_house, {}).get("domain", f"House {t_house}")
        house_from_moon = _get_house(t_sign, effective_moon)

        # Dynamic state info
        lng = t_data.get("longitude", 0)
        if not lng and t_sign in SIGN_ORDER:
            lng = SIGN_ORDER.index(t_sign) * 30.0 + t_data.get("degree_in_sign", 0)
        nak, nak_lord = _get_nakshatra_from_longitude(lng) if lng else ("", "")
        dignity = _get_dignity(t_planet, t_sign)
        is_retro = t_data.get("is_retrograde", False)
        is_combust = t_data.get("is_combust", False)

        # Enrich prediction text with dynamic state
        state_info = []
        if is_retro:
            state_info.append("Retrograde")
        if is_combust:
            state_info.append("Combust")
        if dignity:
            state_info.append(dignity)
        if nak:
            state_info.append(f"in {nak} Nakshatra (lorded by {nak_lord})")

        enriched_text = effect_text
        if state_info:
            enriched_text += f" Currently {', '.join(state_info)}."

        predictions.append(
            TransitPrediction(
                transit_planet=t_planet,
                transit_sign=t_sign,
                transit_house=t_house,
                prediction=enriched_text,
                category=f"House Transit (Lagna H{t_house}, Moon H{house_from_moon})",
                severity=severity,
                retrograde=is_retro,
                combust=is_combust,
                dignity=dignity,
                nakshatra=nak,
                nakshatra_lord=nak_lord,
            )
        )

    # ── Step 2: Transit-to-Transit Aspects ──
    transit_list = [(p, d) for p, d in transit_positions.items() if d.get("rashi")]
    for i, (pa, da) in enumerate(transit_list):
        a_sign = da.get("rashi", "")
        a_deg = da.get("longitude", da.get("degree_in_sign", 0))
        if not a_sign:
            continue
        a_house_lagna = _get_house(a_sign, natal_lagna)
        a_house_moon = _get_house(a_sign, effective_moon)

        for pb, db in transit_list[i + 1 :]:
            b_sign = db.get("rashi", "")
            b_deg = db.get("longitude", db.get("degree_in_sign", 0))
            if not b_sign:
                continue

            is_aspect, aspect_type, orb = _check_aspect(a_deg, b_deg)
            if not is_aspect:
                continue

            b_house_lagna = _get_house(b_sign, natal_lagna)
            b_house_moon = _get_house(b_sign, effective_moon)

            pred_text = _generate_transit_aspect_prediction(
                planet_a=pa,
                sign_a=a_sign,
                house_a_moon=a_house_moon,
                planet_b=pb,
                sign_b=b_sign,
                house_b_moon=b_house_moon,
                aspect_type=aspect_type,
            )

            # Severity based on benefic/malefic combination
            a_benefic = pa in BENEFICS
            b_benefic = pb in BENEFICS
            if a_benefic and b_benefic:
                severity = "positive"
            elif (not a_benefic) and (not b_benefic):
                severity = "negative"
            else:
                severity = "mixed"

            transit_aspect_predictions.append(
                TransitPrediction(
                    transit_planet=pa,
                    transit_sign=a_sign,
                    transit_house=a_house_lagna,
                    aspect_type=aspect_type,
                    target_planet=pb,
                    target_sign=b_sign,
                    target_house=b_house_lagna,
                    prediction=pred_text,
                    category="Transit-to-Transit",
                    severity=severity,
                )
            )

    print(f"GOCHAR DEBUG: Calculated {len(transit_aspect_predictions)} Transit-to-Transit aspects.")

    # ── Build summary ──
    summary: dict[str, list[TransitPrediction]] = {}
    for pred in predictions:
        key = pred.transit_planet
        if key not in summary:
            summary[key] = []
        summary[key].append(pred)

    # Add transit-to-transit aspects to summary by planet
    for pred in transit_aspect_predictions:
        key = pred.transit_planet
        if key not in summary:
            summary[key] = []
        summary[key].append(pred)

    # Overall assessment
    assessment_parts = []

    benefic_preds = [p for p in predictions if p.severity == "positive"]
    if benefic_preds:
        benefic_planets = list(set(p.transit_planet for p in benefic_preds))
        benefic_houses = list(set(str(p.transit_house) for p in benefic_preds))
        assessment_parts.append(
            f"{', '.join(benefic_planets)} transit{'s are' if len(benefic_planets) > 1 else ' is'} currently positive "
            f"for house{'s' if len(benefic_houses) > 1 else ''} {', '.join(benefic_houses)} from your Lagna."
        )

    malefic_preds = [p for p in predictions if p.severity == "negative"]
    if malefic_preds:
        malefic_planets = list(set(p.transit_planet for p in malefic_preds))
        malefic_houses = list(set(str(p.transit_house) for p in malefic_preds))
        assessment_parts.append(
            f"{', '.join(malefic_planets)} transit{'s are' if len(malefic_planets) > 1 else ' is'} currently challenging "
            f"for house{'s' if len(malefic_houses) > 1 else ''} {', '.join(malefic_houses)}."
        )

    if transit_aspect_predictions:
        assessment_parts.append(
            f"{len(transit_aspect_predictions)} transit-to-transit aspect interactions detected in the current cosmic weather."
        )

    overall = (
        " ".join(assessment_parts)
        if assessment_parts
        else "Transit positions computed. Specific predictions available in the detailed sections below."
    )

    # Prepend Chandrasthamam warning to assessment if active
    if chandrasthamam_active:
        overall = chandrasthamam_warning + " " + overall

    # Detect Nakshatra Parivartana
    nak_parivartana = detect_nakshatra_parivartana(transit_positions)

    return GocharTransitResult(
        timestamp=transit_positions.get("SUN", {}).get("timestamp", ""),
        lagna=natal_lagna,
        moon_sign=effective_moon,
        transit_positions={
            p: {"sign": d.get("rashi", ""), "degree": d.get("degree_in_sign", 0)}
            for p, d in transit_positions.items()
        },
        predictions=predictions,
        transit_to_transit_aspects=transit_aspect_predictions,
        summary_by_planet=summary,
        overall_assessment=overall,
        chandrasthamam_active=chandrasthamam_active,
        chandrasthamam_warning=chandrasthamam_warning,
    )


def _get_suffix(n: int) -> str:
    if n >= 11 and n <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def gochar_transit_to_dict(result: GocharTransitResult) -> dict[str, Any]:
    """Convert GocharTransitResult to JSON-serializable dict."""

    def _pred(p: TransitPrediction) -> dict[str, Any]:
        d: dict[str, Any] = {
            "transit_planet": p.transit_planet,
            "transit_sign": p.transit_sign,
            "transit_house": p.transit_house,
            "aspect_type": p.aspect_type,
            "prediction": p.prediction,
            "category": p.category,
            "severity": p.severity,
            "retrograde": p.retrograde,
            "combust": p.combust,
            "dignity": p.dignity,
            "nakshatra": p.nakshatra,
            "nakshatra_lord": p.nakshatra_lord,
        }
        if p.target_planet:
            d["target_planet"] = p.target_planet
        if p.target_sign:
            d["target_sign"] = p.target_sign
        if p.target_house is not None:
            d["target_house"] = p.target_house
        return d

    return {
        "lagna": result.lagna,
        "moon_sign": result.moon_sign,
        "transit_positions": result.transit_positions,
        "predictions": [_pred(p) for p in result.predictions],
        "transit_to_transit_aspects": [_pred(p) for p in result.transit_to_transit_aspects],
        "summary_by_planet": {
            k: [_pred(p) for p in v] for k, v in result.summary_by_planet.items()
        },
        "chandrasthamam_active": result.chandrasthamam_active,
        "chandrasthamam_warning": result.chandrasthamam_warning,
        "overall_assessment": result.overall_assessment,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Planetary States (Retrograde, Combust, Stationary, Speed)
# ═══════════════════════════════════════════════════════════════════════════

# Combustion distance thresholds (degrees from Sun)
COMBUST_THRESHOLDS: dict[str, float] = {
    "MOON": 12.0,
    "MERCURY": 14.0,
    "VENUS": 10.0,
    "MARS": 17.0,
    "JUPITER": 11.0,
    "SATURN": 15.0,
}

# Speed thresholds (degrees/day) for Fast/Slow classification
FAST_SPEED: dict[str, float] = {
    "SUN": 1.02,
    "MOON": 13.2,
    "MARS": 0.64,
    "MERCURY": 1.5,
    "JUPITER": 0.083,
    "VENUS": 1.18,
    "SATURN": 0.034,
}

SLOW_SPEED: dict[str, float] = {
    "SUN": 0.95,
    "MOON": 11.5,
    "MARS": 0.3,
    "MERCURY": 0.8,
    "JUPITER": 0.04,
    "VENUS": 0.8,
    "SATURN": 0.015,
}

# Retrograde planets (classically: Mars, Mercury, Jupiter, Venus, Saturn)
# Rahu/Ketu are always retrograde
RETROGRADE_PLANETS: frozenset[str] = frozenset(
    {"MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"}
)


@dataclass
class PlanetaryState:
    """Computed state of a planet at a given time."""

    planet: str
    longitude: float
    speed: float  # degrees/day
    state: str  # "R", "D", "C", "S", "F", "L" (Retrograde/Direct/Combust/Stationary/Fast/Slow)
    state_label: str  # Human-readable label
    is_retrograde: bool = False
    is_combust: bool = False
    is_stationary: bool = False
    speed_class: str = "normal"  # "fast", "slow", "normal"
    degrees_from_sun: float = 0.0  # Only meaningful for combust check


def compute_planetary_states(
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict[str, PlanetaryState]:
    """Compute planetary states using Swiss Ephemeris.

    Returns retrograde, combust, stationary, and speed classification
    for all classical planets.

    Args:
        latitude: Observer latitude.
        longitude: Observer longitude.

    Returns:
        Dictionary of planet name -> PlanetaryState.
    """
    try:
        import swisseph as swe
    except ImportError:
        return {}

    swe.set_ephe_path(None)
    # CRITICAL: Set Sidereal Mode to Lahiri (Chitrapaksha) for Vedic astrology
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)
    now = datetime.now(timezone.utc)
    jd = swe.julday(
        now.year, now.month, now.day, now.hour + now.minute / 60.0 + now.second / 3600.0
    )
    print(
        f"DEBUG compute_planetary_states: Calculating transits for DATE: {now.date()} TIME: {now.time()} UTC — JD: {jd}"
    )

    # Get Sun position first
    sun_longitude = 0.0
    try:
        flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        xx = swe.calc_ut(jd, 0, flag)  # 0 = Sun
        sun_longitude = xx[0][0] % 360.0
    except Exception:
        pass

    states: dict[str, PlanetaryState] = {}

    # Swiss Ephemeris planet IDs:
    # SE_SUN=0, SE_MOON=1, SE_MERCURY=2, SE_VENUS=3, SE_MARS=4, SE_JUPITER=5, SE_SATURN=6
    planet_ids = {
        "SUN": 0,
        "MOON": 1,
        "MERCURY": 2,
        "VENUS": 3,
        "MARS": 4,
        "JUPITER": 5,
        "SATURN": 6,
    }

    # Vedic sign names for debug output
    _VEDIC_SIGNS = [
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

    for planet_name, planet_id in planet_ids.items():
        try:
            flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            xx = swe.calc_ut(jd, planet_id, flag)
            lng = xx[0][0] % 360.0
            speed = xx[0][3]  # speed in degrees/day

            # Retrograde: negative speed
            is_retro = speed < 0

            # Combust: within threshold degrees of Sun
            lng_diff = abs(lng - sun_longitude)
            if lng_diff > 180:
                lng_diff = 360 - lng_diff
            threshold = COMBUST_THRESHOLDS.get(planet_name, 10.0)
            is_combust = lng_diff <= threshold

            # Stationary: speed very close to 0 (within 0.02 deg/day)
            is_stationary = abs(speed) < 0.02

            # Speed classification
            fast_t = FAST_SPEED.get(planet_name, 1.0)
            slow_t = SLOW_SPEED.get(planet_name, 0.5)
            if speed > fast_t:
                speed_class = "fast"
            elif speed < slow_t:
                speed_class = "slow"
            else:
                speed_class = "normal"

            # Build state string
            state_parts = []
            if is_retro:
                state_parts.append("R")
            else:
                state_parts.append("D")
            if is_combust:
                state_parts.append("C")
            if is_stationary:
                state_parts.append("S")
            if speed_class == "fast":
                state_parts.append("F")
            elif speed_class == "slow":
                state_parts.append("L")

            state_label_parts = []
            if is_retro:
                state_label_parts.append("Retrograde")
            else:
                state_label_parts.append("Direct")
            if is_combust:
                state_label_parts.append("Combust")
            if is_stationary:
                state_label_parts.append("Stationary")
            if speed_class == "fast":
                state_label_parts.append("Fast")
            elif speed_class == "slow":
                state_label_parts.append("Slow")

            states[planet_name] = PlanetaryState(
                planet=planet_name,
                longitude=lng,
                speed=speed,
                state="/".join(state_parts) if state_parts else "D",
                state_label=" + ".join(state_label_parts) if state_label_parts else "Direct",
                is_retrograde=is_retro,
                is_combust=is_combust,
                is_stationary=is_stationary,
                speed_class=speed_class,
                degrees_from_sun=lng_diff,
            )
        except Exception:
            continue

    # Rahu/Ketu (always retrograde by convention)
    for node_name, node_id in [("RAHU", 10), ("KETU", 11)]:
        try:
            flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            xx = swe.calc_ut(jd, node_id, flag)
            lng = xx[0][0] % 360.0
            speed = xx[0][3]
            states[node_name] = PlanetaryState(
                planet=node_name,
                longitude=lng,
                speed=speed,
                state="R",
                state_label="Retrograde (Node)",
                is_retrograde=True,
                is_combust=False,
                is_stationary=False,
                speed_class="normal",
                degrees_from_sun=0.0,
            )
        except Exception:
            continue

    # Debug: print Vedic (Sidereal Lahiri) positions
    for pname in ["JUPITER", "SATURN"]:
        ps = states.get(pname)
        if ps:
            vedic_idx = int(ps.longitude // 30) % 12
            print(
                f"DEBUG VEDIC: {pname} is in {_VEDIC_SIGNS[vedic_idx]} (Sidereal Lahiri) at {ps.longitude:.4f}°"
            )

    return states


def compute_planetary_states_for_date(
    year: int,
    month: int,
    day: int,
) -> dict[str, PlanetaryState]:
    """Compute planetary states for a specific date.

    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
        day: Day (1-31)

    Returns:
        Dictionary of planet name -> PlanetaryState.
    """
    try:
        import swisseph as swe
    except ImportError:
        return {}

    swe.set_ephe_path(None)
    # CRITICAL: Set Sidereal Mode to Lahiri (Chitrapaksha) for Vedic astrology
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)
    jd = swe.julday(year, month, day, 12.0)  # Noon UTC
    print(
        f"DEBUG compute_planetary_states_for_date: Calculating transits for DATE: {year}-{month:02d}-{day:02d} at noon UTC — JD: {jd}"
    )

    # Sun position
    sun_longitude = 0.0
    try:
        flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        xx = swe.calc_ut(jd, 0, flag)
        sun_longitude = xx[0][0] % 360.0
    except Exception:
        pass

    planet_ids = {
        "SUN": 0,
        "MOON": 1,
        "MERCURY": 2,
        "VENUS": 3,
        "MARS": 4,
        "JUPITER": 5,
        "SATURN": 6,
    }

    states: dict[str, PlanetaryState] = {}

    for planet_name, planet_id in planet_ids.items():
        try:
            flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            xx = swe.calc_ut(jd, planet_id, flag)
            lng = xx[0][0] % 360.0
            speed = xx[0][3]

            is_retro = speed < 0
            lng_diff = abs(lng - sun_longitude)
            if lng_diff > 180:
                lng_diff = 360 - lng_diff
            threshold = COMBUST_THRESHOLDS.get(planet_name, 10.0)
            is_combust = lng_diff <= threshold
            is_stationary = abs(speed) < 0.02

            fast_t = FAST_SPEED.get(planet_name, 1.0)
            slow_t = SLOW_SPEED.get(planet_name, 0.5)
            speed_class = "fast" if speed > fast_t else "slow" if speed < slow_t else "normal"

            state_parts = ["R"] if is_retro else ["D"]
            if is_combust:
                state_parts.append("C")
            if is_stationary:
                state_parts.append("S")
            if speed_class == "fast":
                state_parts.append("F")
            elif speed_class == "slow":
                state_parts.append("L")

            state_label_parts = ["Retrograde"] if is_retro else ["Direct"]
            if is_combust:
                state_label_parts.append("Combust")
            if is_stationary:
                state_label_parts.append("Stationary")
            if speed_class == "fast":
                state_label_parts.append("Fast")
            elif speed_class == "slow":
                state_label_parts.append("Slow")

            states[planet_name] = PlanetaryState(
                planet=planet_name,
                longitude=lng,
                speed=speed,
                state="/".join(state_parts),
                state_label=" + ".join(state_label_parts),
                is_retrograde=is_retro,
                is_combust=is_combust,
                is_stationary=is_stationary,
                speed_class=speed_class,
                degrees_from_sun=lng_diff,
            )
        except Exception:
            continue

    for node_name, node_id in [("RAHU", 10), ("KETU", 11)]:
        try:
            flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            xx = swe.calc_ut(jd, node_id, flag)
            lng = xx[0][0] % 360.0
            speed = xx[0][3]
            states[node_name] = PlanetaryState(
                planet=node_name,
                longitude=lng,
                speed=speed,
                state="R",
                state_label="Retrograde (Node)",
                is_retrograde=True,
                is_combust=False,
                is_stationary=False,
                speed_class="normal",
                degrees_from_sun=0.0,
            )
        except Exception:
            continue

    return states


def planetary_states_to_dict(states: dict[str, PlanetaryState]) -> dict[str, Any]:
    """Convert planetary states to JSON-serializable dict."""
    return {
        planet: {
            "planet": s.planet,
            "longitude": round(s.longitude, 4),
            "speed": round(s.speed, 6),
            "state": s.state,
            "state_label": s.state_label,
            "is_retrograde": s.is_retrograde,
            "is_combust": s.is_combust,
            "is_stationary": s.is_stationary,
            "speed_class": s.speed_class,
            "degrees_from_sun": round(s.degrees_from_sun, 2),
        }
        for planet, s in states.items()
    }


# ═══════════════════════════════════════════════════════════════════════════
# Day-by-Day Transit Aspect Forecast
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class DailyTransitAspect:
    """A single day's transit aspect prediction."""

    date: str  # YYYY-MM-DD
    transit_planet: str
    transit_state: str  # "R", "D", "C", etc.
    target_type: str  # "natal_planet" or "natal_house"
    target: str  # planet name or house number
    aspect_type: str  # "7th", "Conjunction", etc.
    prediction: str
    severity: str  # "positive", "negative", "mixed"
    orb_degrees: float = 0.0


def _load_transit_predictions() -> dict[str, dict[str, str]]:
    """Load the detailed transit predictions from JSON file."""
    try:
        json_path = _os.path.join(_os.path.dirname(__file__), "transit_predictions.json")
        with open(json_path, "r") as f:
            data: dict[str, dict[str, str]] = _json.load(f)
        # Remove metadata key
        data.pop("_meta", None)
        return data
    except Exception:
        return {}


TRANSIT_PREDICTIONS = _load_transit_predictions()


def compute_day_by_day_transits(
    natal_planet_details: dict[str, dict[str, Any]],
    natal_lagna: str,
    natal_moon_sign: str = "",
    days: int = 14,
) -> list[DailyTransitAspect]:
    """Compute day-by-day transit aspects for the next N days.

    For each day, calculates which transiting planet is aspecting which
    natal planet/house, using Swiss Ephemeris for FUTURE positions.

    Args:
        natal_planet_details: Natal planet positions.
        natal_lagna: Natal Lagna sign.
        natal_moon_sign: Natal Moon sign (for house-from-Moon calculations).
        days: Number of days to forecast (default 14).

    Returns:
        List of DailyTransitAspect predictions.
    """
    results: list[DailyTransitAspect] = []
    now = datetime.now(timezone.utc)
    moon_sign = natal_moon_sign or natal_lagna

    for day_offset in range(days):
        target_date = now + timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")

        # Compute FUTURE transit positions using Swiss Ephemeris
        daily_states = compute_planetary_states_for_date(
            target_date.year,
            target_date.month,
            target_date.day,
        )

        # For each transiting planet, check aspects to natal planets
        for t_planet, t_state in daily_states.items():
            t_deg = t_state.longitude

            for n_planet, n_data in natal_planet_details.items():
                n_sign = n_data.get("sign", "")
                n_deg = _to_ecliptic(n_sign, n_data.get("degree_in_sign", 0))

                diff = abs(t_deg - n_deg)
                if diff > 180:
                    diff = 360 - diff

                is_aspect = False
                aspect_type = ""
                orb = 0.0

                if diff <= 6.0:
                    is_aspect, aspect_type, orb = True, "Conjunction", diff
                elif abs(diff - 180.0) <= 12.0:
                    is_aspect, aspect_type, orb = True, "7th", abs(diff - 180.0)
                elif abs(diff - 120.0) <= 12.0:
                    is_aspect, aspect_type, orb = True, "5th", abs(diff - 120.0)
                elif abs(diff - 240.0) <= 12.0:
                    is_aspect, aspect_type, orb = True, "9th", abs(diff - 240.0)

                if not is_aspect:
                    continue

                n_house = 0
                if n_sign in SIGN_ORDER and natal_lagna in SIGN_ORDER:
                    n_house = ((SIGN_ORDER.index(n_sign) - SIGN_ORDER.index(natal_lagna)) % 12) + 1

                # Build detailed prediction using transit_predictions.json
                state_desc = ""
                if t_state.is_retrograde:
                    state_desc = " (Retrograde)"
                elif t_state.is_combust:
                    state_desc = " (Combust)"

                # Look up classical prediction from JSON
                classical_pred = ""
                if t_planet in TRANSIT_PREDICTIONS:
                    # Use house-from-Moon for lookup
                    house_from_moon = 0
                    if n_sign in SIGN_ORDER and moon_sign in SIGN_ORDER:
                        house_from_moon = (
                            (SIGN_ORDER.index(n_sign) - SIGN_ORDER.index(moon_sign)) % 12
                        ) + 1
                    classical_pred = TRANSIT_PREDICTIONS[t_planet].get(str(house_from_moon), "")

                # Build transit longitude description
                t_sign_idx = int(t_deg / 30.0)
                t_sign_name = SIGN_ORDER[t_sign_idx % 12] if t_sign_idx < 12 else "MESHA"
                t_deg_in_sign = t_deg - (t_sign_idx * 30.0)

                pred_text = (
                    f"On {date_str}, Transit {t_planet}{state_desc} at "
                    f"{t_deg_in_sign:.1f}° {t_sign_name} {aspect_type}-aspects "
                    f"Natal {n_planet} in House {n_house} (orb: {orb:.1f}°). "
                )
                if classical_pred:
                    pred_text += classical_pred
                else:
                    pred_text += (
                        f"This {aspect_type} aspect activates {n_planet}-related themes "
                        f"in the native's life, creating opportunities for growth and "
                        f"transformation in the areas governed by House {n_house}."
                    )

                severity = "neutral"
                if t_planet in ("JUPITER", "VENUS", "MOON"):
                    severity = "positive"
                elif t_planet in ("SATURN", "MARS", "RAHU"):
                    severity = "negative"
                if t_state.is_retrograde:
                    severity = "mixed"

                results.append(
                    DailyTransitAspect(
                        date=date_str,
                        transit_planet=t_planet,
                        transit_state=t_state.state,
                        target_type="natal_planet",
                        target=n_planet,
                        aspect_type=aspect_type,
                        prediction=pred_text,
                        severity=severity,
                        orb_degrees=orb,
                    )
                )

    severity_order = {"negative": 0, "mixed": 1, "neutral": 2, "positive": 3}
    results.sort(key=lambda x: (x.date, severity_order.get(x.severity, 2)))

    print(f"TRANSIT ASPECTS DEBUG: Found {len(results)} transit-to-natal aspects")
    return results


def daily_transit_to_dict(aspects: list[DailyTransitAspect]) -> list[dict[str, Any]]:
    """Convert daily transit aspects to JSON-serializable list."""
    return [
        {
            "date": a.date,
            "transit_planet": a.transit_planet,
            "transit_state": a.transit_state,
            "target_type": a.target_type,
            "target": a.target,
            "aspect_type": a.aspect_type,
            "prediction": a.prediction,
            "severity": a.severity,
            "orb_degrees": a.orb_degrees,
        }
        for a in aspects
    ]


# ═══════════════════════════════════════════════════════════════════════════
# 14-Day Transit Forecast (using Swiss Ephemeris for future positions)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class TransitForecastDay:
    """A single day's complete transit forecast."""

    date: str
    transiting_planets: list[dict[str, Any]]
    predictions: list[str]


def compute_14day_transit_forecast(
    natal_planet_details: dict[str, dict[str, Any]],
    natal_lagna: str,
    natal_moon_sign: str = "",
    days: int = 14,
) -> list[TransitForecastDay]:
    """Compute a 14-day transit forecast using Swiss Ephemeris.

    For each future day, calculates exact planetary positions using pyswisseph,
    converts them to house positions relative to natal Moon and Lagna,
    and generates detailed classical predictions.

    Args:
        natal_planet_details: Natal planet positions.
        natal_lagna: Natal Lagna sign.
        natal_moon_sign: Natal Moon sign (for house-from-Moon).
        days: Number of days to forecast.

    Returns:
        List of TransitForecastDay with detailed predictions.
    """
    forecast: list[TransitForecastDay] = []
    now = datetime.now(timezone.utc)
    moon_sign = natal_moon_sign or natal_lagna

    # Classical planets for transit (include Rahu/Ketu)
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

        # Calculate FUTURE positions using Swiss Ephemeris
        daily_states = compute_planetary_states_for_date(
            target_date.year,
            target_date.month,
            target_date.day,
        )

        transiting_planets_data: list[dict[str, Any]] = []
        day_predictions: list[str] = []

        for planet in transit_planets:
            state = daily_states.get(planet)
            if not state:
                continue

            lng = state.longitude
            sign_idx = int(lng / 30.0)
            sign_name = SIGN_ORDER[sign_idx % 12] if sign_idx < 12 else "MESHA"
            deg_in_sign = lng - (sign_idx * 30.0)

            # House from Lagna
            house_from_lagna = 0
            if sign_name in SIGN_ORDER and natal_lagna in SIGN_ORDER:
                house_from_lagna = (
                    (SIGN_ORDER.index(sign_name) - SIGN_ORDER.index(natal_lagna)) % 12
                ) + 1

            # House from Moon
            house_from_moon = 0
            if sign_name in SIGN_ORDER and moon_sign in SIGN_ORDER:
                house_from_moon = (
                    (SIGN_ORDER.index(sign_name) - SIGN_ORDER.index(moon_sign)) % 12
                ) + 1

            planet_data = {
                "planet": planet,
                "sign": sign_name,
                "degree": round(deg_in_sign, 1),
                "longitude": round(lng, 4),
                "house_from_moon": house_from_moon,
                "house_from_lagna": house_from_lagna,
                "state": state.state,
                "state_label": state.state_label,
                "is_retrograde": state.is_retrograde,
            }
            transiting_planets_data.append(planet_data)

            # Look up classical prediction from transit_predictions.json
            if planet in TRANSIT_PREDICTIONS and house_from_moon > 0:
                classical_pred = TRANSIT_PREDICTIONS[planet].get(str(house_from_moon), "")
                if classical_pred:
                    state_desc = ""
                    if state.is_retrograde:
                        state_desc = " (Retrograde)"
                    elif state.is_combust:
                        state_desc = " (Combust)"
                    pred = (
                        f"Transit {planet}{state_desc} in {sign_name} at "
                        f"{deg_in_sign:.1f}° — House {house_from_moon} from Moon, "
                        f"House {house_from_lagna} from Lagna: {classical_pred}"
                    )
                    day_predictions.append(pred)

        forecast.append(
            TransitForecastDay(
                date=date_str,
                transiting_planets=transiting_planets_data,
                predictions=day_predictions,
            )
        )

    start_date = forecast[0].date if forecast else ""
    end_date = forecast[-1].date if forecast else ""
    total_preds = sum(len(d.predictions) for d in forecast)
    print(f"GOCHAR DEBUG: Calculated transits for dates {start_date} to {end_date}")
    print(f"GOCHAR DEBUG: Generated {total_preds} detailed predictions")
    if forecast and forecast[0].predictions:
        print(f"GOCHAR DEBUG: Sample prediction - {forecast[0].predictions[0][:100]}...")

    return forecast
