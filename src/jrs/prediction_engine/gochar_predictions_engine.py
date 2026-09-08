"""
Complete Gochar Predictions Engine - All 12 Rashis + All 27 Nakshatras
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RashiPrediction:
    sign: str
    symbol: str
    prediction: str


@dataclass
class NakshatraPrediction:
    name: str
    parent_sign: str
    lord: str
    deity: str
    prediction: str


RASHI_TEMPLATES = {
    "Mesha": "Today carries a quiet intensity for you. The cosmic energies are aligning to bring subtle shifts in your professional relationships—you may notice colleagues becoming more receptive to your ideas, especially after midday. Trust your intuition when negotiating; Mercury's favorable aspect suggests your words carry extra weight right now. In matters of the heart, patience is your greatest ally. Financially, avoid impulsive decisions before sunset. The evening favors reflection over action.",
    "Vrishabha": "The stars are weaving a gentle tapestry of opportunities for you today. Your natural steadiness is your superpower right now—while others rush, your measured approach will yield better results. Career-wise, a conversation with someone senior could open unexpected doors. Relationships bring warmth today; if there's been distance with a loved one, a simple gesture of kindness can bridge the gap. Health-wise, pay attention to your throat and neck.",
    "Mithuna": "Your mind is particularly sharp today, and the cosmos supports intellectual pursuits. Conversations flow effortlessly—you might find yourself mediating a disagreement or offering wisdom that others desperately need. Career opportunities arise through unexpected channels. In love, your wit and charm are magnetic, but be mindful not to overpromise. Health favors mental clarity—meditation or journaling will amplify your natural gifts.",
    "Karka": "Today the universe invites you to nurture your own needs alongside caring for others. Your emotional intelligence is heightened—use it to navigate workplace dynamics with grace. A family matter may require your attention; approach it with compassion rather than urgency. In relationships, vulnerability is your strength today—sharing your true feelings deepens bonds. Health-wise, water is your ally; stay hydrated.",
    "Simha": "The spotlight finds you naturally today, but true leadership means lifting others as you rise. Your confidence inspires those around you—use this energy to mentor or encourage someone who's struggling. Career-wise, recognition is likely, but stay humble; grace in victory is more memorable than the victory itself. In love, grand gestures aren't necessary—small, consistent acts of devotion speak louder.",
    "Kanya": "Your analytical mind is your greatest asset today, but remember to balance logic with intuition. Work projects benefit from your attention to detail—trust your instincts when something doesn't quite add up. In relationships, clear communication prevents misunderstandings; say what you mean with kindness. Health-wise, your digestive system needs attention today—choose whole foods and avoid overthinking meals.",
    "Tula": "Harmony is your birthright, and today the universe supports your quest for balance. Partnerships—business or personal—thrive under today's energies. If you've been avoiding a difficult conversation, now is the time; approach it with your characteristic diplomacy. Career-wise, collaboration yields better results than going solo. In love, compromise doesn't mean losing yourself—it means finding the middle ground where both hearts are heard.",
    "Vrischika": "Your intensity is magnetic today, but channel it wisely. Transformation is in the air—you may realize something about yourself that shifts your entire perspective. Career-wise, strategic moves made today have long-lasting impact; think three steps ahead. In relationships, depth over breadth serves you better—one meaningful connection outweighs ten superficial ones. Health-wise, release stored emotions through movement or creative expression.",
    "Dhanu": "Adventure calls—not necessarily through travel, but through expanding your mind. Today favors learning, teaching, and sharing wisdom. Career-wise, international connections or higher education opportunities may arise. In relationships, honesty is your best policy; sugarcoating only delays resolution. Health favors your hips, thighs, and liver—outdoor activity and fresh air will rejuvenate you. The afternoon brings a moment of philosophical clarity.",
    "Makara": "Discipline meets opportunity today. Your natural ambition is supported by favorable cosmic energies—channel it toward meaningful goals rather than just climbing ladders. Career-wise, authority figures notice your dedication; position yourself for advancement. In relationships, showing your softer side strengthens bonds; vulnerability isn't weakness. Health-wise, your bones and joints need care—calcium-rich foods and gentle stretching serve you well.",
    "Kumbha": "Your innovative spirit shines today, and the world needs your unique perspective. Technology, social causes, and community building are favored. Career-wise, unconventional approaches yield breakthrough results—don't dilute your vision to fit in. In relationships, friendship is the foundation; nurture your social circle. Health-wise, your ankles and circulatory system benefit from movement—dance, walk, or try something new.",
    "Meena": "Your sensitivity is your gift today—use it to create beauty and healing. Artistic pursuits flow effortlessly; let your imagination run wild. Career-wise, roles involving compassion, counseling, or creative arts are highly favored. In relationships, your empathy creates deep connections; just ensure you're not absorbing others' emotions. Health-wise, your feet need attention—foot massages and comfortable shoes are essential.",
}

NAKSHATRA_TEMPLATES = {
    "Ashwini": "Your natural healing abilities are amplified today. Favorable for starting new ventures, especially in healthcare or service. Challenges may arise from impatience—temper your speed with wisdom. Your leadership inspires others; use it to uplift those who are struggling.",
    "Bharani": "Transformation is your theme today. You possess the strength to bear heavy burdens and emerge stronger. Favorable for research, deep work, and confronting difficult truths. Avoid extremes in behavior—balance is your ally. Your determination can move mountains.",
    "Krittika": "Your purifying fire burns away what no longer serves you. Favorable for cleansing rituals, decluttering, and setting boundaries. Your sharp intellect cuts through confusion—use it wisely. Avoid harsh words; your tongue can wound as easily as it can heal.",
    "Rohini": "Creativity and abundance flow through you today. Favorable for artistic pursuits, romance, and financial negotiations. Avoid possessiveness; love flourishes in freedom. Your nurturing nature heals those around you—share your warmth generously.",
    "Mrigashira": "Your searching mind seeks truth today. Favorable for research, travel, and exploring new ideas. Your curiosity leads to breakthrough discoveries. Avoid restlessness; commit to one path long enough to see results. Your gentle nature attracts others.",
    "Ardra": "Emotional storms may arise, but they bring necessary cleansing. Favorable for deep psychological work and releasing old patterns. Your intensity can be overwhelming—practice self-care. Tears today are medicine; allow yourself to feel fully.",
    "Punarvasu": "Return and renewal mark your day. Favorable for coming home, reconnecting with roots, and second chances. Your optimistic nature lifts spirits—share your hope generously. Avoid clinging to the past; renewal requires releasing what was.",
    "Pushya": "Nourishment and nurturing define your day. Favorable for starting businesses, ceremonies, and learning. Your caring nature creates safe spaces for others. Avoid over-giving; you must nourish yourself too. Spiritual practices yield abundant blessings.",
    "Ashlesha": "Your intuitive powers are heightened today. Favorable for occult studies, healing, and navigating complex situations. Your penetrating gaze sees through illusions—use this gift ethically. Avoid manipulation; your influence carries great karma.",
    "Magha": "Ancestral blessings flow to you today. Favorable for honoring lineage and claiming your inheritance (material and spiritual). Your leadership carries the weight of tradition—use it wisely. Avoid ego; true authority serves others.",
    "Purva Phalguni": "Creativity and relaxation mark your day. Favorable for arts, entertainment, romance, and enjoying life's pleasures. Your charm opens doors—use it to spread joy. Avoid laziness; rest should rejuvenate, not stagnate.",
    "Uttara Phalguni": "Service and friendship define your day. Favorable for helping others, marriages, and social causes. Your generous heart creates lasting bonds. Avoid being taken advantage of; set healthy boundaries.",
    "Hasta": "Your skilled hands create magic today. Favorable for crafts, healing touch, and practical problem-solving. Your dexterity—physical and mental—solves complex puzzles. Avoid trickery; your cleverness should serve truth.",
    "Chitra": "Beauty and architecture bless your endeavors today. Favorable for design, fashion, building, and creating aesthetic spaces. Your eye for detail creates masterpieces. Avoid vanity; true beauty comes from within.",
    "Swati": "Independence and movement mark your day. Favorable for travel, trade, and starting fresh. Your adaptable nature helps you bend without breaking. Avoid scattering energy; focus on one goal at a time.",
    "Vishakha": "Your focused determination achieves goals today. Favorable for spiritual practices, competitions, and multi-step projects. Your ability to hold opposing views creates wisdom. Avoid obsession; healthy ambition differs from fixation.",
    "Anuradha": "Friendship and devotion shine through you today. Favorable for building alliances, devotional practices, and long-distance travel. Your loyalty creates deep, lasting bonds. Avoid isolation; you thrive in community.",
    "Jyeshtha": "Seniority and protection mark your day. Favorable for leadership roles, protecting the vulnerable, and managing complex affairs. Your wisdom guides others through difficult times. Avoid authoritarianism; true elders serve with humility.",
    "Mula": "Destruction of ignorance leads to liberation today. Favorable for research, root cause analysis, and spiritual awakening. Your penetrating insight reveals hidden truths. Avoid nihilism; destruction makes way for renewal.",
    "Purva Ashadha": "Invincibility and inspiration flow through you today. Favorable for speeches, legal matters, and water-related activities. Your words carry power—use them to uplift. Avoid arrogance; true invincibility comes from humility.",
    "Uttara Ashadha": "Universal victory and responsibility mark your day. Favorable for leadership, completing long-term projects, and social reform. Your consistent effort creates lasting impact. Avoid rigidity; true victory adapts to circumstances.",
    "Shravana": "Listening and learning define your day. Favorable for education, music, and receiving wisdom. Your attentive nature absorbs knowledge like a sponge. Avoid gossip; your ears should hear truth, not rumors.",
    "Dhanishta": "Rhythm and wealth flow through you today. Favorable for music, dance, real estate, and group activities. Your ability to synchronize with others creates harmony. Avoid greed; true wealth includes spiritual abundance.",
    "Shatabhisha": "Healing and mystery surround you today. Favorable for medical treatment, astronomy, and esoteric studies. Your connection to the cosmic brings healing to others. Avoid isolation; solitude should replenish, not imprison.",
    "Purva Bhadrapada": "Spiritual fire transforms you today. Favorable for austerities, confronting shadows, and spiritual warfare. Your intensity purifies karma. Avoid fanaticism; true spirituality includes compassion.",
    "Uttara Bhadrapada": "Wisdom and compassion mark your day. Favorable for teaching, counseling, and spiritual practices. Your calm presence soothes troubled souls. Avoid emotional suppression; wisdom includes feeling deeply.",
    "Revati": "Protection and journey mark your day. Favorable for travel, final completion of projects, and caring for animals. Your gentle nature nurtures all beings. Avoid escapism; healthy boundaries protect your sensitivity.",
}


def generate_rashi_predictions() -> List[RashiPrediction]:
    signs = [
        ("Mesha", "♈"),
        ("Vrishabha", "♉"),
        ("Mithuna", "♊"),
        ("Karka", "♋"),
        ("Simha", "♌"),
        ("Kanya", ""),
        ("Tula", "♎"),
        ("Vrischika", "♏"),
        ("Dhanu", "♐"),
        ("Makara", "♑"),
        ("Kumbha", "♒"),
        ("Meena", "♓"),
    ]
    return [
        RashiPrediction(sign=sign, symbol=symbol, prediction=RASHI_TEMPLATES[sign])
        for sign, symbol in signs
    ]


def generate_nakshatra_predictions() -> List[NakshatraPrediction]:
    # All 27 Nakshatras - 3 per sign (some span 2 signs)
    nakshatra_data = [
        # 1. Mesha (Aries) - 3 nakshatras
        ("Ashwini", "Mesha", "Ketu", "Ashwini Kumaras"),
        ("Bharani", "Mesha", "Venus", "Yama"),
        ("Krittika", "Mesha", "Sun", "Agni"),  # 1st pada in Aries
        # 2. Vrishabha (Taurus) - 3 nakshatras
        ("Krittika", "Vrishabha", "Sun", "Agni"),  # 2-4 padas in Taurus
        ("Rohini", "Vrishabha", "Moon", "Brahma"),
        ("Mrigashira", "Vrishabha", "Mars", "Soma"),  # 1-2 padas in Taurus
        # 3. Mithuna (Gemini) - 3 nakshatras
        ("Mrigashira", "Mithuna", "Mars", "Soma"),  # 3-4 padas in Gemini
        ("Ardra", "Mithuna", "Rahu", "Rudra"),
        ("Punarvasu", "Mithuna", "Jupiter", "Aditi"),  # 1-3 padas in Gemini
        # 4. Karka (Cancer) - 3 nakshatras
        ("Punarvasu", "Karka", "Jupiter", "Aditi"),  # 4th pada in Cancer
        ("Pushya", "Karka", "Saturn", "Brihaspati"),
        ("Ashlesha", "Karka", "Mercury", "Nagas"),
        # 5. Simha (Leo) - 3 nakshatras
        ("Magha", "Simha", "Ketu", "Pitris"),
        ("Purva Phalguni", "Simha", "Venus", "Bhaga"),
        ("Uttara Phalguni", "Simha", "Sun", "Aryaman"),  # 1st pada in Leo
        # 6. Kanya (Virgo) - 3 nakshatras
        ("Uttara Phalguni", "Kanya", "Sun", "Aryaman"),  # 2-4 padas in Virgo
        ("Hasta", "Kanya", "Moon", "Savitar"),
        ("Chitra", "Kanya", "Mars", "Vishwakarma"),  # 1-2 padas in Virgo
        # 7. Tula (Libra) - 3 nakshatras
        ("Chitra", "Tula", "Mars", "Vishwakarma"),  # 3-4 padas in Libra
        ("Swati", "Tula", "Rahu", "Vayu"),
        ("Vishakha", "Tula", "Jupiter", "Indra-Agni"),  # 1-3 padas in Libra
        # 8. Vrischika (Scorpio) - 3 nakshatras
        ("Vishakha", "Vrischika", "Jupiter", "Indra-Agni"),  # 4th pada in Scorpio
        ("Anuradha", "Vrischika", "Saturn", "Mitra"),
        ("Jyeshtha", "Vrischika", "Mercury", "Indra"),
        # 9. Dhanu (Sagittarius) - 3 nakshatras
        ("Mula", "Dhanu", "Ketu", "Nirriti"),
        ("Purva Ashadha", "Dhanu", "Venus", "Apas"),
        ("Uttara Ashadha", "Dhanu", "Sun", "Vishvedevas"),  # 1st pada in Sagittarius
        # 10. Makara (Capricorn) - 3 nakshatras
        ("Uttara Ashadha", "Makara", "Sun", "Vishvedevas"),  # 2-4 padas in Capricorn
        ("Shravana", "Makara", "Moon", "Vishnu"),
        ("Dhanishta", "Makara", "Mars", "Vasus"),  # 1-2 padas in Capricorn
        # 11. Kumbha (Aquarius) - 3 nakshatras
        ("Dhanishta", "Kumbha", "Mars", "Vasus"),  # 3-4 padas in Aquarius
        ("Shatabhisha", "Kumbha", "Rahu", "Varuna"),
        ("Purva Bhadrapada", "Kumbha", "Jupiter", "Aja Ekapada"),  # 1-3 padas in Aquarius
        # 12. Meena (Pisces) - 3 nakshatras
        ("Purva Bhadrapada", "Meena", "Jupiter", "Aja Ekapada"),  # 4th pada in Pisces
        ("Uttara Bhadrapada", "Meena", "Saturn", "Ahir Budhnya"),
        ("Revati", "Meena", "Mercury", "Pushan"),
    ]

    return [
        NakshatraPrediction(
            name=name,
            parent_sign=parent,
            lord=lord,
            deity=deity,
            prediction=NAKSHATRA_TEMPLATES[name],
        )
        for name, parent, lord, deity in nakshatra_data
    ]


def get_gochar_predictions(date_str: str) -> Dict:
    return {
        "date": date_str,
        "rashis": [r.__dict__ for r in generate_rashi_predictions()],
        "nakshatras": [n.__dict__ for n in generate_nakshatra_predictions()],
    }
