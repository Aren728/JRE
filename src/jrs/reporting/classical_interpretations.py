"""JRE Reporting — Classical Interpretation Database.

Structured, easily expandable dictionary of classical Vedic astrology meanings
for planets in houses, planets in nakshatras, key conjunctions, and karmic
interpretations. Based on BPHS (Brihat Parashara Hora Shastra), Phaladeepika,
Jataka Parijata, and Uttara Kalamrita.

NO engine logic — pure interpretive data for the narrative layer.
"""

from __future__ import annotations

from typing import Any

# ══════════════════════════════════════════════════════════════════════════════
# 1. PLANETS IN HOUSES (1–12)
# ══════════════════════════════════════════════════════════════════════════════
# Keys: planet name (uppercase) → dict of house number (as string) → text.
# Each entry is a single interpretive paragraph suitable for inclusion in
# a professional report.

PLANETS_IN_HOUSES: dict[str, dict[str, str]] = {
    "SUN": {
        "1": (
            "Sun in the 1st house bestows a strong sense of self, natural authority, "
            "and radiant personality. The native possesses leadership qualities, "
            "confidence, and a commanding presence. There is an innate drive toward "
            "self-expression and personal achievement. The father's influence is "
            "prominent in shaping the native's identity."
        ),
        "2": (
            "Sun in the 2nd house blesses the native with eloquent speech, a strong "
            "moral compass, and the ability to accumulate wealth through personal "
            "effort. The family lineage carries significance, and the native may "
            "inherit leadership responsibilities within the family. There can be "
            "tension between personal ego and family traditions."
        ),
        "3": (
            "Sun in the 3rd house confers courage, initiative, and strong "
            "communication skills. The native is a natural self-starter who thrives "
            "in short journeys, writing, and media. Sibling relationships are "
            "influenced by the Sun's dignity — strong and supportive when well-placed, "
            "competitive when afflicted. The native's courage becomes a defining trait."
        ),
        "4": (
            "Sun in the 4th house creates a deep connection to home, land, and "
            "emotional foundations. The native may experience tension between career "
            "ambitions and domestic peace. Property matters and the mother's influence "
            "are significant themes. Despite internal restlessness, the native "
            "eventually finds emotional security through their own achievements."
        ),
        "5": (
            "Sun in the 5th house is a powerful placement for intelligence, creativity, "
            "and authority. The native possesses sharp intellect, strong intuitive "
            "abilities, and natural leadership in speculative ventures. Children bring "
            "joy and recognition. This is a classic placement for political leaders, "
            "educators, and spiritual practitioners."
        ),
        "6": (
            "Sun in the 6th house, while in a dusthana house, actually strengthens "
            "the native's ability to overcome enemies and obstacles. The native excels "
            "in service-oriented roles, legal matters, and healing. Health requires "
            "attention, particularly to the heart and bones. The native's authority "
            "grows through confronting and resolving conflicts."
        ),
        "7": (
            "Sun in the 7th house places the soul's purpose in the realm of "
            "partnerships and public life. The native seeks recognition through "
            "relationships and partnerships. Marriage is a significant life theme, "
            "and the partner often possesses strong Sun-like qualities — confident, "
            "authoritative, and ambitious. Business partnerships are favored."
        ),
        "8": (
            "Sun in the 8th house brings the native face-to-face with transformation, "
            "hidden truths, and the deeper mysteries of life. There may be sudden "
            "changes in fortune, inheritance matters, or involvement with research, "
            "occult, or healing arts. The native develops profound resilience and "
            "regenerative power through life's trials."
        ),
        "9": (
            "Sun in the 9th house is one of the most auspicious placements, blessing "
            "the native with Dharma, wisdom, long-distance travel, and a strong "
            "connection to higher learning. The father or a father figure serves as a "
            "guiding light. The native is naturally drawn to philosophy, spirituality, "
            "and teaching. Fortunate events and good fortune accompany this placement."
        ),
        "10": (
            "Sun in the 10th house (the house of karma and career) is a powerful "
            "placement for professional success, public recognition, and authority. "
            "The native is destined for leadership roles and may achieve fame or "
            "governmental position. Career achievements bring personal fulfillment, "
            "and the native's reputation grows throughout life."
        ),
        "11": (
            "Sun in the 11th house brings gains through authoritative positions, "
            "networks, and influential friendships. The native benefits from "
            "government connections, elder siblings, and organizational involvement. "
            "Wishes are fulfilled, and the native's social circle provides both "
            "material and spiritual support."
        ),
        "12": (
            "Sun in the 12th house turns the native's attention inward toward "
            "spiritual liberation, isolation, and foreign lands. There may be "
            "expenditures related to the father or governmental matters. The native "
            "finds true self-expression through meditation, spiritual retreats, or "
            "work in foreign countries. Material ambitions gradually yield to "
            "transcendental aspirations."
        ),
    },
    "MOON": {
        "1": (
            "Moon in the 1st house bestows a gentle, nurturing, and emotionally "
            "expressive personality. The native possesses strong intuitive abilities, "
            "a caring disposition, and natural magnetism. The mind is sensitive and "
            "reflective, often mirroring the emotions of those around them. Public "
            "popularity and emotional accessibility are hallmarks of this placement."
        ),
        "2": (
            "Moon in the 2nd house connects the native's emotional well-being to "
            "family, wealth, and speech. The native possesses a melodious voice, "
            "emotional attachment to family traditions, and the ability to earn "
            "through nurturing or caretaking roles. Financial fluctuations may mirror "
            "emotional states. The native's words carry emotional weight and influence."
        ),
        "3": (
            "Moon in the 3rd house enhances communication skills, courage, and "
            "mental adaptability. The native is naturally curious, emotionally "
            "intelligent in social settings, and possesses a vivid imagination. "
            "Short journeys and creative writing are favored. The native's "
            "relationship with siblings is emotionally significant."
        ),
        "4": (
            "Moon in the 4th house is deeply auspicious for emotional fulfillment, "
            "domestic happiness, and property matters. The native possesses a strong "
            "connection to their roots, homeland, and mother. Inner peace is achieved "
            "through creating a beautiful and harmonious home environment. Real estate "
            "and vehicles bring comfort."
        ),
        "5": (
            "Moon in the 5th house blesses the native with strong intuitive "
            "intelligence, creative talent, and emotional depth in romantic "
            "relationships. Children bring immense emotional fulfillment. The native "
            "may possess psychic or clairvoyant abilities. Speculative gains are "
            "possible through emotional intelligence and gut instincts."
        ),
        "6": (
            "Moon in the 6th house creates emotional challenges through service "
            "demands, health concerns, or workplace dynamics. The native may work in "
            "healing, nursing, or service professions. Emotional well-being requires "
            "conscious attention, as the native tends to absorb others' suffering. "
            "Overcoming emotional obstacles builds genuine inner strength."
        ),
        "7": (
            "Moon in the 7th house places emotional fulfillment through partnership "
            "and marriage at the center of life. The native seeks an emotionally "
            "nurturing partner and thrives in close relationships. There is sensitivity "
            "to the partner's needs, and the domestic life is emotionally rich. "
            "Business partnerships also benefit from the native's emotional intelligence."
        ),
        "8": (
            "Moon in the 8th house brings emotional depth, transformative experiences, "
            "and sensitivity to life's hidden currents. The native may experience "
            "emotional upheavals that ultimately lead to profound psychological "
            "growth. Inheritance, occult interests, and research are prominent themes. "
            "Emotional resilience is developed through facing life's mysteries."
        ),
        "9": (
            "Moon in the 9th house blesses the native with emotional connection to "
            "spirituality, higher learning, and long-distance travel. The native finds "
            "emotional nourishment through philosophical inquiry, spiritual practice, "
            "and cultural exploration. The father or mentor provides emotional guidance. "
            "Faith and intuition work harmoniously."
        ),
        "10": (
            "Moon in the 10th house connects the native's career and public image to "
            "emotional intelligence and nurturing qualities. The native may work in "
            "counseling, healthcare, hospitality, or public service. Career satisfaction "
            "comes from roles that allow emotional expression and care for others. "
            "Public reputation is emotionally resonant."
        ),
        "11": (
            "Moon in the 11th house brings emotional fulfillment through friendships, "
            "community involvement, and fulfillment of desires. The native possesses "
            "a wide social circle and benefits emotionally from group activities. "
            "Gains come through networks, and the native's empathic nature attracts "
            "supportive friendships."
        ),
        "12": (
            "Moon in the 12th house turns emotional energy inward toward spiritual "
            "pursuits, meditation, and detachment from material concerns. The native "
            "may experience vivid dreams, psychic experiences, and emotional "
            "sensitivity to subtle energies. Foreign lands and ashrams provide "
            "emotional nourishment. Sleep and subconscious processing are significant."
        ),
    },
    "MARS": {
        "1": (
            "Mars in the 1st house endows the native with exceptional courage, "
            "physical vitality, and a warrior-like temperament. The native is "
            "assertive, competitive, and driven by a strong desire to lead and "
            "conquer. Athletic ability and mechanical aptitude are pronounced. "
            "Temper requires management, but the energy, when channeled, produces "
            "remarkable achievements."
        ),
        "2": (
            "Mars in the 2nd house creates a sharp, sometimes cutting, speech "
            "pattern and a strong drive to accumulate wealth. The native may face "
            "family disputes or財financial conflicts, but also possesses the "
            "determination to build substantial material resources. Courage in "
            "financial matters is a defining trait."
        ),
        "3": (
            "Mars in the 3rd house is one of its strongest placements, granting "
            "exceptional courage, mental strength, and initiative. The native excels "
            "in communication, short journeys, and entrepreneurial ventures. Sibling "
            "relationships are dynamic and energetic. The native's bravery and "
            "determination become well-known."
        ),
        "4": (
            "Mars in the 4th house can create restlessness in domestic life and "
            "property matters. The native possesses strong willpower regarding home "
            "and family but may experience conflicts or frequent relocations. The "
            "mother's temperament may be strong-willed. Inner peace comes through "
            "physical activity and constructive use of energy."
        ),
        "5": (
            "Mars in the 5th house brings aggressive intelligence, competitive "
            "creativity, and passion in romantic relationships. The native possesses "
            "sharp analytical abilities and may excel in sports, engineering, or "
            "martial arts. Children are energetic and may require patient guidance. "
            "Speculative ventures benefit from strategic boldness."
        ),
        "6": (
            "Mars in the 6th house is another powerful dusthana placement that "
            "strengthens the native's ability to overcome enemies,疾病, and legal "
            "challenges. The native is a formidable opponent in any conflict and "
            "excels in competitive service roles. Health requires attention, "
            "particularly inflammation and fevers."
        ),
        "7": (
            "Mars in the 7th house (Mangal Dosha) creates intensity in partnerships "
            "and marriage. The native possesses strong physical desire and may attract "
            "an equally passionate partner. While this placement can create friction, "
            "it also generates dynamic energy in relationships. The partner is often "
            "courageous and assertive."
        ),
        "8": (
            "Mars in the 8th house brings sudden transformative events, hidden "
            "energetic forces, and potential for accidents or surgeries. The native "
            "possesses deep occult or research abilities and may excel in surgery, "
            "engineering, or crisis management. Longevity and inheritance matters "
            "require careful navigation."
        ),
        "9": (
            "Mars in the 9th house channels warrior energy into philosophical "
            "pursuits, spiritual practice, and long-distance travel. The native may "
            "be passionate about religion, philosophy, or foreign cultures. The "
            "father's temperament is strong and influential. Courage in defending "
            "one's beliefs is a hallmark."
        ),
        "10": (
            "Mars in the 10th house is a powerful placement for career success in "
            "military, engineering, surgery, sports, or competitive fields. The "
            "native possesses exceptional drive and determination in professional "
            "life. Authority is earned through bold action and decisive leadership. "
            "The native may work long hours with intense dedication."
        ),
        "11": (
            "Mars in the 11th house brings gains through bold action, competitive "
            "ventures, and leadership in group settings. The native benefits from "
            "friendships with energetic, ambitious individuals. Financial gains come "
            "through courage, entrepreneurship, and strategic risk-taking."
        ),
        "12": (
            "Mars in the 12th house channels aggressive energy into spiritual "
            "practices, foreign lands, or behind-the-scenes activities. The native "
            "may experience expenses related to conflicts or hospitalization, but "
            "also finds liberation through channeling warrior energy into meditation "
            "and self-discipline. Foreign residences are favored."
        ),
    },
    "MERCURY": {
        "1": (
            "Mercury in the 1st house bestows a sharp intellect, excellent "
            "communication skills, and a youthful, adaptable personality. The native "
            "possesses quick wit, analytical abilities, and a natural talent for "
            "business and learning. The speech is eloquent, and the mind is "
            "constantly active, processing information from multiple sources."
        ),
        "2": (
            "Mercury in the 2nd house blesses the native with eloquent speech, "
            "financial acumen, and the ability to earn through intellectual "
            "pursuits. The family environment is intellectually stimulating, and "
            "the native may possess talent in music, mathematics, or accounting. "
            "Wealth accumulation through communication or trade is favored."
        ),
        "3": (
            "Mercury in the 3rd house is a natural placement for communication, "
            "writing, and intellectual curiosity. The native excels in journalism, "
            "teaching, and short-form communication. Sibling relationships are "
            "intellectually stimulating, and the native possesses a versatile, "
            "adaptable mind that learns quickly."
        ),
        "4": (
            "Mercury in the 4th house connects the native's intelligence to home, "
            "education, and emotional foundations. The native possesses a scholarly "
            "mind that finds comfort in study and intellectual pursuits at home. "
            "Property matters may involve intellectual or communication-based "
            "professions. The native's education is a source of emotional security."
        ),
        "5": (
            "Mercury in the 5th house is an excellent placement for intellectual "
            "creativity, speculative gains, and children. The native possesses "
            "sharp analytical intelligence, mathematical ability, and talent in "
            "debate or logic. Romantic relationships are intellectually stimulating, "
            "and children may inherit the native's communicative gifts."
        ),
        "6": (
            "Mercury in the 6th house enhances analytical abilities in service, "
            "healing, or legal contexts. The native excels in detail-oriented work, "
            "medical practice, or legal analysis. Health may be affected by nervous "
            "tension or overthinking, but the native's analytical mind is a powerful "
            "tool for solving complex problems."
        ),
        "7": (
            "Mercury in the 7th house blesses partnerships with intellectual "
            "compatibility, communication skills, and business acumen. The native "
            "seeks a mentally stimulating partner and thrives in relationships that "
            "involve intellectual exchange. Business partnerships are particularly "
            "favorable, especially in trade or communication fields."
        ),
        "8": (
            "Mercury in the 8th house turns the analytical mind toward hidden "
            "subjects, research, and transformation. The native may excel in "
            "investigation, occult studies, psychology, or financial analysis. "
            "Sudden changes in fortune require intellectual adaptation. The native "
            "possesses a penetrating, investigative mind."
        ),
        "9": (
            "Mercury in the 9th house connects intelligence to philosophy, higher "
            "learning, and long-distance travel. The native excels in academic "
            "pursuits, philosophical debate, and cross-cultural communication. "
            "The father or mentor figure provides intellectual guidance. Teaching "
            "and publishing are naturally favored."
        ),
        "10": (
            "Mercury in the 10th house brings career success through communication, "
            "intellect, and business acumen. The native may work in writing, "
            "commerce, consulting, or technology. Career advancement comes through "
            "clever strategy, articulate expression, and intellectual leadership. "
            "The native's reputation is built on intelligence and eloquence."
        ),
        "11": (
            "Mercury in the 11th house brings gains through intellectual networks, "
            "communication, and business ventures. The native benefits from "
            "friendships with intelligent, articulate individuals. Financial gains "
            "come through trade, writing, or technology. Wishes are fulfilled "
            "through mental acuity and social connections."
        ),
        "12": (
            "Mercury in the 12th house turns the intellectual energy inward toward "
            "spiritual study, foreign languages, and behind-the-scenes work. The "
            "native may experience expenses related to education or communication, "
            "but also finds liberation through spiritual knowledge and meditation. "
            "Foreign lands provide intellectual stimulation."
        ),
    },
    "JUPITER": {
        "1": (
            "Jupiter in the 1st house is one of the most auspicious placements, "
            "bestowing wisdom, generosity, philosophical temperament, and natural "
            "authority. The native possesses a broad-minded, optimistic outlook and "
            "is often respected as a teacher or guide. The body is well-built, and "
            "the native enjoys good fortune throughout life."
        ),
        "2": (
            "Jupiter in the 2nd house blesses the native with wealth, eloquent "
            "speech, and strong family values. The native's words carry wisdom and "
            "authority, and financial prosperity comes through honest means. The "
            "family environment is spiritually and intellectually enriching. Charity "
            "and generosity are natural traits."
        ),
        "3": (
            "Jupiter in the 3rd house grants courage of conviction, philosophical "
            "communication, and success in teaching or writing. The native's siblings "
            "are supportive, and short journeys bring wisdom. The native possesses a "
            "natural talent for inspiring others through words and personal example."
        ),
        "4": (
            "Jupiter in the 4th house creates deep emotional and spiritual "
            "fulfillment through home, education, and family. The native possesses "
            "a philosophical home environment, strong maternal influence, and natural "
            "interest in spiritual or educational pursuits at home. Property and "
            "vehicles come through good fortune."
        ),
        "5": (
            "Jupiter in the 5th house is a powerful placement for intelligence, "
            "creativity, and spiritual practice. The native possesses exceptional "
            "analytical abilities, philosophical insight, and natural talent for "
            "teaching. Children bring great joy, and speculative ventures are "
            "blessed with good fortune. This is a classic placement for spiritual "
            "teachers and scholars."
        ),
        "6": (
            "Jupiter in the 6th house, while in a dusthana, provides protection "
            "through wisdom and moral authority in service, healing, and legal "
            "matters. The native may work in healthcare, counseling, or charitable "
            "organizations. Health is generally good, and the native overcomes "
            "obstacles through faith and ethical conduct."
        ),
        "7": (
            "Jupiter in the 7th house blesses marriage and partnerships with "
            "wisdom, spiritual compatibility, and mutual respect. The native seeks "
            "a learned, philosophical partner and thrives in relationships based on "
            "shared values. Business partnerships are particularly fortunate, "
            "especially in education, counseling, or spiritual fields."
        ),
        "8": (
            "Jupiter in the 8th house brings wisdom through transformation, "
            "inheritance, and occult knowledge. The native may possess psychic "
            "abilities or talent in astrology, tantra, or healing. Longevity is "
            "generally good, and the native finds wisdom through life's deeper "
            "mysteries. Inheritance matters are favorable."
        ),
        "9": (
            "Jupiter in the 9th house is perhaps the most auspicious placement in "
            "all of Vedic astrology, blessing the native with Dharma, wisdom, "
            "long-distance travel, and divine grace. The native is naturally drawn "
            "to philosophy, spirituality, and teaching. The father or guru serves "
            "as a powerful guiding force. This placement often indicates a life of "
            "spiritual leadership and philosophical contribution."
        ),
        "10": (
            "Jupiter in the 10th house brings career success through wisdom, "
            "teaching, counseling, or spiritual leadership. The native's reputation "
            "is built on moral authority and philosophical insight. Careers in "
            "education, law, religion, or consulting are particularly favored. "
            "The native's professional life is guided by ethical principles."
        ),
        "11": (
            "Jupiter in the 11th house brings abundant gains through wisdom, "
            "philosophical networks, and charitable endeavors. The native benefits "
            "from friendships with spiritual or learned individuals. Financial "
            "prosperity comes through teaching, counseling, or philosophical "
            "pursuits. Wishes are fulfilled through faith and generosity."
        ),
        "12": (
            "Jupiter in the 12th house turns the native's wisdom inward toward "
            "spiritual liberation, meditation, and foreign lands. The native may "
            "spend on spiritual pursuits or charitable causes abroad. Sleep and "
            "dream life are spiritually significant. This placement often indicates "
            "a life path toward renunciation and higher consciousness."
        ),
    },
    "VENUS": {
        "1": (
            "Venus in the 1st house bestows beauty, charm, artistic talent, and a "
            "refined temperament. The native possesses natural magnetism, appreciation "
            "for luxury, and strong creative abilities. Relationships and partnerships "
            "are central to the native's identity. The native often possesses a "
            "youthful appearance and graceful demeanor."
        ),
        "2": (
            "Venus in the 2nd house blesses the native with wealth, beautiful speech, "
            "and appreciation for fine arts and cuisine. The native's family "
            "environment is aesthetically rich, and financial prosperity comes through "
            "artistic, musical, or luxury-related fields. The native possesses a "
            "talent for accumulating beautiful objects and experiences."
        ),
        "3": (
            "Venus in the 3rd house enhances creative communication, artistic "
            "writing, and talent in performing arts. The native's sibling "
            "relationships are affectionate and supportive. Short journeys bring "
            "pleasure and aesthetic enrichment. The native possesses a natural "
            "charm in social interactions and creative self-expression."
        ),
        "4": (
            "Venus in the 4th house creates a beautiful, harmonious home environment "
            "and deep emotional satisfaction through domestic life. The native "
            "possesses artistic talent in interior design, music, or cooking. "
            "Property matters are fortunate, and the native's mother or maternal "
            "influence is loving and aesthetically inclined."
        ),
        "5": (
            "Venus in the 5th house blesses the native with romantic love, "
            "creative talent, and joy through children. The native possesses strong "
            "artistic abilities, particularly in music, dance, or visual arts. "
            "Romantic relationships are passionate and fulfilling. Speculative "
            "ventures in art or luxury fields are favored."
        ),
        "6": (
            "Venus in the 6th house can create challenges in relationships and "
            "health, but also brings the ability to find beauty in service and "
            "daily routines. The native may work in healthcare, wellness, or "
            "aesthetic fields. Relationships require conscious effort, but the "
            "native's charm helps navigate conflicts."
        ),
        "7": (
            "Venus in the 7th house is the natural karaka (significator) of marriage "
            "and partnership placed in its own domain. The native attracts a "
            "beautiful, charming, and refined partner. Marriage brings pleasure, "
            "comfort, and artistic fulfillment. Business partnerships in creative "
            "fields are particularly fortunate."
        ),
        "8": (
            "Venus in the 8th house brings transformation through love, inheritance "
            "of artistic or aesthetic values, and deep sensual experiences. The "
            "native may possess talent in tantra, healing arts, or occult aesthetics. "
            "Relationships undergo profound transformation, ultimately leading to "
            "deeper intimacy and understanding."
        ),
        "9": (
            "Venus in the 9th house connects love and beauty to philosophy, "
            "spirituality, and long-distance travel. The native finds aesthetic "
            "fulfillment through cultural exploration, spiritual practice, and "
            "philosophical inquiry. The partner may be foreign or philosophically "
            "inclined. Art and spirituality blend harmoniously."
        ),
        "10": (
            "Venus in the 10th house brings career success through artistic, "
            "creative, or luxury-related fields. The native's public image is "
            "charming and aesthetically appealing. Careers in art, music, fashion, "
            "entertainment, or hospitality are particularly favored. The native's "
            "professional reputation is built on beauty and refinement."
        ),
        "11": (
            "Venus in the 11th house brings gains through artistic networks, "
            "friendships, and creative collaborations. The native benefits from "
            "social connections in artistic, musical, or luxury fields. Financial "
            "prosperity comes through creative partnerships and aesthetic "
            "enterprises."
        ),
        "12": (
            "Venus in the 12th house turns aesthetic energy inward toward "
            "spiritual devotion, artistic retreat, and foreign lands. The native "
            "may experience expenses on luxury or artistic pursuits abroad. "
            "Spiritual love and devotion become central themes. The native finds "
            "beauty in solitude, meditation, and transcendent experiences."
        ),
    },
    "SATURN": {
        "1": (
            "Saturn in the 1st house brings a serious, disciplined, and responsible "
            "temperament. The native possesses strong endurance, patience, and the "
            "ability to work long hours toward their goals. While early life may "
            "present challenges, the native's perseverance eventually leads to "
            "profound achievement and respect. The native often appears mature "
            "beyond their years."
        ),
        "2": (
            "Saturn in the 2nd house creates a disciplined approach to wealth "
            "accumulation and family responsibilities. The native may experience "
            "early financial struggles but develops strong financial management "
            "skills over time. Speech is measured and serious, and the native's "
            "family values emphasize hard work and frugality."
        ),
        "3": (
            "Saturn in the 3rd house brings discipline to communication, short "
            "journeys, and sibling relationships. The native possesses a methodical, "
            "careful approach to learning and self-expression. While early efforts "
            "may seem slow, the native's persistence leads to mastery. Sibling "
            "relationships may be serious or involve responsibility."
        ),
        "4": (
            "Saturn in the 4th house can create challenges in domestic happiness "
            "and emotional fulfillment, but also builds tremendous inner strength. "
            "The native may experience a disciplined or restrictive home environment "
            "in youth, which ultimately teaches resilience. Property matters require "
            "patience and careful planning."
        ),
        "5": (
            "Saturn in the 5th house brings a serious approach to creativity, "
            "intelligence, and children. The native's creative expression is "
            "disciplined and structured, often excelling in fields requiring "
            "patience and precision. Children bring responsibility, and romantic "
            "relationships are approached with maturity and caution."
        ),
        "6": (
            "Saturn in the 6th house is one of Saturn's strongest placements, "
            "granting exceptional ability to overcome enemies,疾病, and obstacles. "
            "The native excels in service-oriented roles, particularly in "
            "healthcare, law, or organizational management. Health requires "
            "discipline, but the native's endurance is remarkable."
        ),
        "7": (
            "Saturn in the 7th house brings seriousness and responsibility to "
            "marriage and partnerships. The native may marry later in life or seek "
            "a mature, stable partner. While there can be delays or challenges in "
            "partnerships, the eventual relationship is built on deep commitment "
            "and shared responsibility. Business partnerships are conservative "
            "and long-lasting."
        ),
        "8": (
            "Saturn in the 8th house brings profound transformation through "
            "endurance, discipline, and confronting life's deepest challenges. The "
            "native possesses exceptional longevity and the ability to navigate "
            "crises with composure. Inheritance and occult matters require patient "
            "study. The native develops profound wisdom through facing mortality "
            "and impermanence."
        ),
        "9": (
            "Saturn in the 9th house brings a disciplined approach to philosophy, "
            "spirituality, and higher learning. The native may experience delays "
            "or challenges in finding a spiritual teacher, but eventually discovers "
            "profound wisdom through persistent study. Long-distance travel may be "
            "delayed but ultimately rewarding. The father's influence may be "
            "serious or demanding."
        ),
        "10": (
            "Saturn in the 10th house is a powerful placement for career success "
            "through discipline, hard work, and perseverance. The native builds "
            "career achievements through methodical effort over many years. While "
            "early career may be slow, the native eventually reaches positions of "
            "authority and respect. This is a classic placement for senior "
            "executives, judges, and industrialists."
        ),
        "11": (
            "Saturn in the 11th house brings gains through patience, discipline, "
            "and long-term networking. The native benefits from friendships with "
            "mature, responsible individuals. Financial prosperity comes through "
            "steady accumulation rather than speculative ventures. Wishes are "
            "fulfilled through persistent, disciplined effort."
        ),
        "12": (
            "Saturn in the 12h turns the native's discipline inward toward "
            "spiritual practice, meditation, and asceticism. The native may "
            "experience isolation, foreign lands, or charitable giving. While "
            "there can be expenses or losses, the ultimate result is spiritual "
            "liberation through self-discipline and detachment."
        ),
    },
    "RAHU": {
        "1": (
            "Rahu in the 1st house creates a powerful desire for self-expression, "
            "recognition, and worldly achievement. The native possesses unconventional "
            "qualities and may be drawn to foreign cultures, technology, or innovative "
            "fields. There is a strong karmic pull toward establishing personal "
            "identity through worldly accomplishment. The native's life path involves "
            "balancing material ambition with spiritual grounding."
        ),
        "2": (
            "Rahu in the 2nd house creates intense desire for wealth, family "
            "recognition, and eloquent speech. The native may acquire wealth through "
            "unconventional means or foreign connections. Family life may involve "
            "unusual dynamics. The karmic lesson involves learning to value "
            "authentic expression over material accumulation."
        ),
        "3": (
            "Rahu in the 3rd house amplifies courage, communication skills, and "
            "desire for recognition through self-effort. The native may excel in "
            "media, technology, or unconventional communication. Sibling "
            "relationships involve karmic lessons. Short journeys and entrepreneurial "
            "ventures are favored, though the native must learn discernment."
        ),
        "4": (
            "Rahu in the 4th house creates restlessness in domestic life and a "
            "desire for unconventional living arrangements. The native may move "
            "frequently or live in foreign lands. Property matters involve karmic "
            "lessons. The mother's influence may be unusual or complicated. Inner "
            "peace comes through embracing change rather than resisting it."
        ),
        "5": (
            "Rahu in the 5th house amplifies creative intelligence and desire for "
            "speculative gains. The native possesses unconventional thinking and "
            "may excel in technology, astrology, or research. Romantic relationships "
            "involve intense karmic connections. Children bring both joy and "
            "unexpected lessons. The native must learn to ground creative vision "
            "in practical reality."
        ),
        "6": (
            "Rahu in the 6th house is one of Rahu's most favorable placements, "
            "granting power over enemies, disease, and obstacles. The native excels "
            "in competitive fields, legal matters, and healing. There is a karmic "
            "gift for overcoming challenges through unconventional methods. Service "
            "to others brings karmic rewards."
        ),
        "7": (
            "Rahu in the 7th house creates intense desire for partnership and "
            "marriage, often with unconventional or foreign partners. The native's "
            "karmic lessons involve learning about authentic partnership versus "
            "illusion. Marriage brings transformation, and the partner may possess "
            "strong Rahu-like qualities — innovative, ambitious, and non-traditional."
        ),
        "8": (
            "Rahu in the 8th house brings sudden transformations, hidden knowledge, "
            "and karmic encounters with life's mysteries. The native may be drawn to "
            "occult sciences, tantra, or research. Inheritance and longevity matters "
            "involve unexpected developments. The karmic path involves transforming "
            "through facing fears and embracing the unknown."
        ),
        "9": (
            "Rahu in the 9th house creates desire for philosophical knowledge, "
            "foreign cultures, and spiritual experience. The native may follow "
            "unconventional spiritual paths or seek wisdom in foreign lands. The "
            "father's influence may be unusual or distant. The karmic lesson involves "
            "finding authentic spiritual truth amidst many options."
        ),
        "10": (
            "Rahu in the 10th house amplifies career ambition and desire for public "
            "recognition. The native may achieve success through unconventional "
            "careers, technology, or foreign connections. The karmic path involves "
            "learning to balance worldly ambition with ethical conduct. Career "
            "success often comes suddenly after periods of uncertainty."
        ),
        "11": (
            "Rahu in the 11th house brings gains through unconventional networks, "
            "technology, and innovative ventures. The native benefits from friendships "
            "with eccentric or visionary individuals. Financial gains may come through "
            "foreign sources or new-age industries. The karmic lesson involves "
            "distinguishing genuine friendships from superficial connections."
        ),
        "12": (
            "Rahu in the 12th house creates desire for spiritual liberation, "
            "foreign lands, and transcendence of material existence. The native may "
            "experience expenses or losses that ultimately lead to spiritual growth. "
            "Foreign residences and spiritual retreats are karmically significant. "
            "The native's path involves finding liberation through surrender rather "
            "than control."
        ),
    },
    "KETU": {
        "1": (
            "Ketu in the 1st house indicates a native who has already mastered "
            "personal identity in past lives and now seeks spiritual liberation. "
            "The native possesses innate spiritual wisdom but may feel disconnected "
            "from worldly identity. Physical appearance may be unusual or ethereal. "
            "The karmic path involves learning to engage with the material world "
            "while maintaining spiritual awareness."
        ),
        "2": (
            "Ketu in the 2nd house indicates detachment from family and wealth "
            "accumulation. The native possesses innate speech patterns from past "
            "lives but may feel disconnected from family traditions. Financial "
            "matters involve karmic release. The native's path involves finding "
            "spiritual value beyond material possessions."
        ),
        "3": (
            "Ketu in the 3rd house grants innate courage and communication abilities "
            "from past lives, but the native may feel disconnected from self-effort "
            "and sibling relationships. The karmic lesson involves learning to "
            "actively engage with the world rather than withdrawing. Short journeys "
            "and self-expression require conscious effort."
        ),
        "4": (
            "Ketu in the 4th house indicates detachment from domestic life and "
            "material comforts. The native possesses deep inner peace from past "
            "spiritual practice but may feel restless in domestic settings. The "
            "karmic path involves finding emotional fulfillment through spiritual "
            "practice rather than material security."
        ),
        "5": (
            "Ketu in the 5th house grants innate intelligence and creative talent "
            "from past lives, but the native may feel disconnected from romance, "
            "children, or speculative ventures. The karmic lesson involves learning "
            "to express creative gifts in the present rather than relying on past "
            "life abilities. Children and romance require conscious engagement."
        ),
        "6": (
            "Ketu in the 6th house indicates mastery over enemies and disease from "
            "past lives. The native possesses innate healing abilities but may feel "
            "disconnected from service and daily routines. The karmic path involves "
            "using past life skills to serve others in the present. Health matters "
            "require conscious attention."
        ),
        "7": (
            "Ketu in the 7th house indicates detachment from partnerships and "
            "marriage. The native possesses deep relationship wisdom from past lives "
            "but may feel disconnected from present partnerships. The karmic lesson "
            "involves learning to engage authentically in relationships while "
            "maintaining spiritual independence."
        ),
        "8": (
            "Ketu in the 8th house grants innate knowledge of occult sciences, "
            "transformation, and hidden truths. The native possesses deep intuitive "
            "abilities but may feel disconnected from material transformation. The "
            "karmic path involves using past life occult knowledge for present "
            "healing and spiritual service."
        ),
        "9": (
            "Ketu in the 9th house indicates deep spiritual wisdom from past lives "
            "but potential disconnection from formal philosophy or religious "
            "institutions. The native possesses innate Dharma but may struggle with "
            "organized religion. The karmic path involves expressing spiritual "
            "wisdom through personal practice rather than institutional affiliation."
        ),
        "10": (
            "Ketu in the 10th house indicates detachment from career ambitions "
            "and public recognition. The native possesses past life mastery in "
            "professional fields but may feel disconnected from worldly "
            "achievements. The karmic path involves using professional skills for "
            "spiritual service rather than personal glory."
        ),
        "11": (
            "Ketu in the 11th house indicates detachment from friendships, social "
            "networks, and material gains. The native possesses past life wisdom "
            "about community but may feel isolated in present social settings. The "
            "karmic path involves finding spiritual community beyond material "
            "networks."
        ),
        "12": (
            "Ketu in the 12th house is a profoundly spiritual placement, indicating "
            "mastery of spiritual liberation in past lives. The native possesses "
            "innate Moksha (liberation) qualities — detachment, meditation ability, "
            "and transcendence of material concerns. The karmic path involves "
            "applying past life spiritual mastery to present life challenges. "
            "Foreign lands and ashrams provide natural spiritual nourishment. "
            "This placement often indicates a soul very close to final liberation."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 2. PLANETS IN NAKSHATRAS
# ══════════════════════════════════════════════════════════════════════════════
# Keys: planet name → dict of nakshatra name → interpretive text.
# Focuses on the most significant nakshatra placements for key planets.

NAKSHATRA_INTERPRETATIONS: dict[str, dict[str, str]] = {
    "MOON": {
        "ASHWINI": (
            "Moon in Ashwini bestows quick healing abilities, pioneering spirit, "
            "and restless emotional energy. The native possesses innate medical "
            "intuition and the ability to initiate emotional healing in others."
        ),
        "BHARANI": (
            "Moon in Bharani brings emotional intensity, transformative experiences, "
            "and the ability to carry heavy emotional burdens. The native possesses "
            "deep creative power and the courage to face life's harsh truths."
        ),
        "KRITTIKA": (
            "Moon in Krittika grants sharp emotional perception, cutting intellect, "
            "and the ability to discern truth from illusion. The native's emotions "
            "are fiery and purifying, often serving as a catalyst for change."
        ),
        "ROHINI": (
            "Moon in Rohini is one of the most auspicious Moon placements, "
            "bestowing emotional abundance, beauty, creative fertility, and "
            "material prosperity. The native possesses natural charm and the "
            "ability to manifest desires through emotional focus."
        ),
        "MRIGASHIRA": (
            "Moon in Mrigashira creates a gentle, searching emotional nature. "
            "The native is drawn to beauty, nature, and the pursuit of "
            "knowledge. There is a deer-like quality — graceful, curious, "
            "and sometimes elusive."
        ),
        "ARDRA": (
            "Moon in Ardra brings emotional upheaval, tears of transformation, "
            "and the ability to channel grief into spiritual growth. The native "
            "possesses deep empathy and the power to heal through emotional "
            "catharsis. Rahu's energy intensifies emotional experiences."
        ),
        "PUNARVASU": (
            "Moon in Punarvasu bestows emotional renewal, optimism, and the "
            "ability to bounce back from adversity. The native possesses a "
            "buoyant, hopeful emotional nature and the gift of restoring "
            "emotional well-being in others."
        ),
        "PUSHYA": (
            "Moon in Pushya is considered one of the most nurturing Moon "
            "placements, bestowing emotional nourishment, spiritual devotion, "
            "and the ability to care for others with genuine compassion. The "
            "native's emotional nature is deeply nourishing and spiritually "
            "grounded."
        ),
        "ASHLESHA": (
            "Moon in Ashlesha brings emotional depth, kundalini energy, and "
            "penetrating intuitive perception. The native possesses the ability "
            "to sense hidden motives and navigate complex emotional landscapes. "
            "The emotional nature can be both healing and intense."
        ),
        "MAGHA": (
            "Moon in Magha connects the native's emotions to ancestral lineage, "
            "royal dignity, and past life karma. The native possesses natural "
            "authority and emotional strength inherited from the family lineage. "
            "Ancestral blessings and responsibilities are emotionally prominent."
        ),
        "PURVA_PHALGUNI": (
            "Moon in Purva Phalguni bestows emotional warmth, creative passion, "
            "and the ability to enjoy life's pleasures. The native possesses "
            "artistic talent and the gift of creating beautiful, harmonious "
            "emotional environments."
        ),
        "UTTARA_PHALGUNI": (
            "Moon in Uttara Phalguni grants emotional stability, generous "
            "friendship, and the ability to provide emotional support. The "
            "native possesses a reliable, nurturing emotional nature that "
            "creates lasting bonds of friendship and trust."
        ),
        "HASTA": (
            "Moon in Hasta bestows emotional dexterity, healing hands, and the "
            "ability to manifest through manual skill. The native possesses "
            "a gift for craftsmanship, healing arts, and creating beauty "
            "through skilled hands. Emotional expression is practical and "
            "tangible."
        ),
        "CHITRA": (
            "Moon in Chitra brings emotional creativity, artistic vision, and "
            "the ability to create beauty in all forms. The native possesses "
            "a brilliant, sparkling emotional nature and the gift of transforming "
            "ordinary experiences into extraordinary art."
        ),
        "SWATI": (
            "Moon in Swati bestows emotional independence, flexibility, and the "
            "ability to grow in any direction. The native possesses a free-"
            "spirited emotional nature that values autonomy and self-expression. "
            "Like a young plant, the emotional nature is adaptable and resilient."
        ),
        "VISHAKHA": (
            "Moon in Vishakha creates a goal-oriented emotional nature driven "
            "by determination and focus. The native possesses the emotional "
            "strength to achieve long-term objectives through persistent effort. "
            "The emotional nature is purposeful and achievement-oriented."
        ),
        "ANURADHA": (
            "Moon in Anuradha bestows emotional devotion, friendship, and "
            "spiritual discipline. The native possesses a deeply loyal emotional "
            "nature and the ability to create profound emotional bonds. Devotion "
            "to a cause or person is emotionally fulfilling."
        ),
        "JYESHTHA": (
            "Moon in Jyeshta brings emotional power, seniority, and the ability "
            "to handle complex, challenging situations. The native possesses "
            "a mature, authoritative emotional nature that naturally assumes "
            "leadership in times of crisis."
        ),
        "MULA": (
            "Moon in Mula creates an emotional nature focused on getting to the "
            "root of matters. The native possesses deep investigative emotional "
            "intuition and the ability to uncover hidden truths. The emotional "
            "journey involves dismantling illusions to find core reality."
        ),
        "PURVA_ASHADHA": (
            "Moon in Purva Ashadha bestows emotional invincibility, optimism, "
            "and the ability to rise above adversity. The native possesses an "
            "unconquerable emotional spirit and the gift of inspiring hope "
            "in others. Water-related emotional healing is prominent."
        ),
        "UTTARA_ASHADHA": (
            "Moon in Uttara Ashadha grants emotional universality, "
            "unwavering determination, and the ability to lead with quiet "
            "strength. The native possesses a steady, enduring emotional "
            "nature that gains strength through persistence."
        ),
        "SHRAVANA": (
            "Moon in Shravana bestows deep listening abilities, emotional "
            "receptivity, and connection to sacred knowledge. The native "
            "possesses the gift of understanding through careful attention "
            "and the ability to absorb wisdom through emotional openness."
        ),
        "DHANISHTHA": (
            "Moon in Dhanishta brings emotional wealth, musical talent, and "
            "the ability to create abundance through rhythmic, coordinated "
            "action. The native possesses a rich, expansive emotional nature "
            "that attracts prosperity and celebration."
        ),
        "SHATABHISHA": (
            "Moon in Shatabhisha creates a healing emotional nature focused "
            "on secrecy, privacy, and deep transformation. The native possesses "
            "powerful healing abilities and the emotional capacity to work with "
            "hidden forces for restoration and renewal."
        ),
        "PURVA_BHADRAPADA": (
            "Moon in Purva Bhadrapada brings fiery emotional transformation, "
            "spiritual intensity, and the ability to channel emotional energy "
            "into spiritual practice. The native possesses a dramatic, "
            "passionate emotional nature that burns through illusions."
        ),
        "UTTARA_BHADRAPADA": (
            "Moon in Uttara Bhadrapada bestows deep emotional wisdom, "
            "spiritual maturity, and the ability to serve as an emotional "
            "anchor for others. The native possesses a serene, profound "
            "emotional nature rooted in ancient wisdom."
        ),
        "REVATI": (
            "Moon in Revati grants emotional compassion, spiritual "
            "completion, and the ability to guide others through life's "
            "final transitions. The native possesses a gentle, nurturing "
            "emotional nature connected to the cosmic journey of the soul."
        ),
    },
    "JUPITER": {
        "ASHWINI": (
            "Jupiter in Ashwini bestows healing wisdom, pioneering philosophy, "
            "and the ability to initiate spiritual or educational reform."
        ),
        "PUNARVASU": (
            "Jupiter in Punarvasu amplifies optimism, renewal, and philosophical "
            "renewal. The native possesses a naturally hopeful and restorative "
            "approach to wisdom and learning."
        ),
        "PUSHYA": (
            "Jupiter in Pushya is one of the most auspicious Jupiter placements, "
            "creating deep spiritual nourishment, moral authority, and the ability "
            "to guide others with genuine compassion. The native is a natural "
            "spiritual teacher and caretaker."
        ),
        "VISHAKHA": (
            "Jupiter in Vishakha brings goal-oriented wisdom, determination in "
            "spiritual pursuit, and the ability to achieve philosophical objectives "
            "through persistent effort."
        ),
        "ANURADHA": (
            "Jupiter in Anuradha bestows devotional wisdom, deep friendship in "
            "spiritual circles, and the ability to teach through loving example."
        ),
        "UTTARA_ASHADHA": (
            "Jupiter in Uttara Ashadha grants universal wisdom, unwavering "
            "spiritual conviction, and the ability to lead philosophical movements "
            "with quiet authority."
        ),
        "REVATI": (
            "Jupiter in Revati bestows cosmic wisdom, compassion, and the ability "
            "to guide souls through their spiritual journey. The native possesses "
            "a gentle, all-encompassing philosophical nature."
        ),
    },
    "SATURN": {
        "PUSHYA": (
            "Saturn in Pushya creates disciplined spiritual practice, structured "
            "nurturing, and the ability to provide long-term spiritual guidance. "
            "The native's wisdom grows through patient, consistent effort."
        ),
        "ANURADHA": (
            "Saturn in Anuradha brings disciplined devotion, structured friendship, "
            "and the ability to maintain spiritual commitments over decades. The "
            "native's loyalty to spiritual principles is unwavering."
        ),
        "UTTARA_ASHADHA": (
            "Saturn in Uttara Ashadha bestows disciplined universality, patient "
            "leadership, and the ability to create lasting philosophical or "
            "institutional structures through sustained effort."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 3. KEY CONJUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
# Keys: frozenset of planet names → interpretive text.

CONJUNCTION_INTERPRETATIONS: dict[frozenset[str], str] = {
    frozenset({"SUN", "MOON"}): (
        "Sun-Moon conjunction (Amavasya or near New Moon) blends the soul's "
        "purpose with emotional nature, creating a powerful sense of self but "
        "potential inner tension between ego and feelings. The native's identity "
        "and emotional needs are deeply intertwined."
    ),
    frozenset({"SUN", "MARS"}): (
        "Sun-Mars conjunction amplifies courage, leadership, and competitive "
        "drive. The native possesses exceptional willpower and the ability to "
        "take decisive action. Temper management is important, as the combined "
        "fire energy can be intense."
    ),
    frozenset({"SUN", "MERCURY"}): (
        "Sun-Mercury conjunction (Budhaditya Yoga) sharpens intellect, "
        "communication, and analytical ability. The native possesses a brilliant, "
        "quick mind and the ability to express ideas with authority. This is "
        "a classic placement for scholars, writers, and professionals."
    ),
    frozenset({"SUN", "JUPITER"}): (
        "Sun-Jupiter conjunction combines soul purpose with wisdom, creating "
        "a natural teacher and spiritual leader. The native possesses moral "
        "authority, philosophical insight, and the ability to inspire others "
        "through personal example."
    ),
    frozenset({"SUN", "VENUS"}): (
        "Sun-Venus conjunction blends ego with aesthetic sensibility, creating "
        "a creative, charming personality. The native possesses artistic talent, "
        "romantic magnetism, and the ability to create beauty. Relationships "
        "are central to the native's self-expression."
    ),
    frozenset({"SUN", "SATURN"}): (
        "Sun-Saturn conjunction creates tension between authority and discipline, "
        "ego and responsibility. The native possesses the ability to build lasting "
        "authority through persistent effort, though early life may involve "
        "challenges with father figures or authority. The eventual result is "
        "mature, tested leadership."
    ),
    frozenset({"SUN", "RAHU"}): (
        "Sun-Rahu conjunction amplifies ambition, worldly desire, and the pursuit "
        "of recognition. The native possesses intense drive but must learn to "
        "balance material ambition with authentic self-expression. Eclipsed Sun "
        "energy requires spiritual grounding."
    ),
    frozenset({"SUN", "KETU"}): (
        "Sun-Ketu conjunction connects the soul to past life spiritual mastery. "
        "The native possesses innate spiritual authority but may feel detached "
        "from worldly identity. The karmic path involves expressing spiritual "
        "wisdom in the material world."
    ),
    frozenset({"MOON", "MARS"}): (
        "Moon-Mars conjunction creates emotional intensity, courage, and the "
        "ability to act on emotional instincts. The native possesses a passionate, "
        "dynamic emotional nature. Emotional management is important, as feelings "
        "can be expressed with force."
    ),
    frozenset({"MOON", "MERCURY"}): (
        "Moon-Mercury conjunction blends emotional sensitivity with intellectual "
        "sharpness, creating an emotionally intelligent communicator. The native "
        "possesses the ability to express feelings with clarity and understand "
        "others' emotional states intuitively."
    ),
    frozenset({"MOON", "JUPITER"}): (
        "Moon-Jupiter conjunction (Gajakesari-like influence) brings emotional "
        "wisdom, generosity, and spiritual nurturing. The native possesses a "
        "broad-minded, compassionate emotional nature and the ability to guide "
        "others with emotional intelligence and philosophical insight."
    ),
    frozenset({"MOON", "VENUS"}): (
        "Moon-Venus conjunction creates deep emotional beauty, artistic "
        "sensitivity, and romantic fulfillment. The native possesses natural "
        "charm, aesthetic appreciation, and the ability to create emotionally "
        "harmonious environments."
    ),
    frozenset({"MOON", "SATURN"}): (
        "Moon-Saturn conjunction creates emotional depth, seriousness, and the "
        "ability to endure emotional challenges with patience. The native "
        "possesses a mature emotional nature but may experience early emotional "
        "restrictions that ultimately build profound inner strength."
    ),
    frozenset({"MOON", "RAHU"}): (
        "Moon-Rahu conjunction amplifies emotional desire, illusion, and the "
        "pursuit of unconventional emotional experiences. The native possesses "
        "intense emotional depth but must discern between authentic feelings "
        "and emotional projections."
    ),
    frozenset({"MOON", "KETU"}): (
        "Moon-Ketu conjunction creates emotional detachment, spiritual intuition, "
        "and past life emotional wisdom. The native possesses deep psychic "
        "abilities and emotional understanding that transcends ordinary "
        "perception. The emotional journey involves balancing detachment with "
        "present life engagement."
    ),
    frozenset({"MARS", "MERCURY"}): (
        "Mars-Mercury conjunction sharpens analytical ability and creates a "
        "quick, strategic mind. The native possesses the ability to think and "
        "act decisively. Communication may be assertive or argumentative, "
        "but the intellectual energy is formidable."
    ),
    frozenset({"MARS", "JUPITER"}): (
        "Mars-Jupiter conjunction combines courage with wisdom, creating a "
        "warrior-philosopher archetype. The native possesses the ability to "
        "fight for philosophical causes and defend moral principles with action. "
        "This is a powerful placement for spiritual warriors and reformers."
    ),
    frozenset({"MARS", "VENUS"}): (
        "Mars-Venus conjunction creates passionate desire, artistic fire, and "
        "intense romantic energy. The native possesses strong physical desire "
        "and creative passion. Relationships are intense and transformative, "
        "requiring conscious channeling of powerful energy."
    ),
    frozenset({"MARS", "SATURN"}): (
        "Mars-Saturn conjunction creates disciplined aggression, strategic "
        "patience, and the ability to achieve through persistent effort. The "
        "native possesses the warrior's courage combined with the sage's "
        "endurance, creating a formidable force for long-term achievement."
    ),
    frozenset({"JUPITER", "VENUS"}): (
        "Jupiter-Venus conjunction (Saraswati Yoga influence) combines wisdom "
        "with beauty, creating exceptional artistic and philosophical talent. "
        "The native possesses the ability to express profound truths through "
        "art, music, or beautiful communication."
    ),
    frozenset({"JUPITER", "SATURN"}): (
        "Jupiter-Saturn conjunction blends expansion with restriction, creating "
        "a dynamic tension between growth and limitation. The native possesses "
        "the wisdom to know when to expand and when to conserve, developing "
        "a balanced, pragmatic approach to life."
    ),
    frozenset({"VENUS", "SATURN"}): (
        "Venus-Saturn conjunction brings discipline to love, beauty, and "
        "creativity. The native's artistic expression is structured and enduring, "
        "and relationships are approached with maturity and commitment. While "
        "there may be delays in romantic fulfillment, the eventual bonds are "
        "deep and lasting."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# 4. KARMIC / PREDICTIVE INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
# Specific rules for challenging placements, framed constructively with
# classical remedial context.

KARMIC_INDICATORS: dict[str, dict[str, Any]] = {
    "Ketu_12th": {
        "condition": "Ketu in 12th house",
        "interpretation": (
            "Ketu in the 12th house indicates deep spiritual detachment, a natural "
            "inclination toward liberation (moksha), and a life path that may "
            "involve stepping back from material accomplishments to seek higher "
            "truth. The native possesses innate spiritual gifts from past lives "
            "and finds natural fulfillment in meditation, foreign ashrams, or "
            "solitary spiritual practice. Material losses may ultimately serve "
            "spiritual growth."
        ),
        "remedy": (
            "Classical remedy: Practice regular meditation and spiritual retreats. "
            "Serve in hospitals, ashrams, or charitable institutions. Foreign travel "
            "for spiritual purposes is beneficial. Chant 'Om Ketave Namaha' on "
            "Saturdays. BPHS Ch. 42 recommends Ketu remedies for spiritual "
            "liberation and transcendence of material attachment."
        ),
    },
    "Saturn_8th": {
        "condition": "Saturn in 8th house",
        "interpretation": (
            "Saturn in the 8th house brings sudden transformations, tests of "
            "endurance, and the need for disciplined spiritual practice. While "
            "this placement can indicate challenges with longevity, health, or "
            "inheritance matters, it also bestows extraordinary resilience and "
            "the ability to navigate life's deepest crises with composure. The "
            "native develops profound wisdom through facing impermanence."
        ),
        "remedy": (
            "Classical remedy: Practice regular spiritual discipline (sadhana) "
            "and maintain ethical conduct. Visit Shani temples on Saturdays and "
            "offer mustard oil to Shani idols. Serve the elderly and disabled. "
            "Chant 'Om Shanicharaya Namaha' 108 times daily. BPHS Ch. 29 "
            "recommends Saturn remedies for longevity and overcoming obstacles."
        ),
    },
    "Rahu_8th": {
        "condition": "Rahu in 8th house",
        "interpretation": (
            "Rahu in the 8th house brings sudden, unexpected transformations and "
            "encounters with life's hidden forces. The native may experience "
            "unpredictable events related to inheritance, occult experiences, or "
            "psychological upheaval. However, this placement also grants powerful "
            "intuitive abilities and the potential for profound spiritual "
            "transformation through facing the unknown."
        ),
        "remedy": (
            "Classical remedy: Study occult sciences, astrology, or psychology "
            "with disciplined intention. Practice meditation to manage Rahu's "
            "illusions. Avoid deception and maintain ethical conduct in hidden "
            "matters. Chant 'Om Ra Namaha' on Wednesdays. BPHS recommends "
            "Rahu remedies through spiritual practice and ethical living."
        ),
    },
    "Mars_7th": {
        "condition": "Mars in 7th house (Mangal Dosha)",
        "interpretation": (
            "Mars in the 7th house creates intensity, passion, and potential "
            "friction in partnerships and marriage. The native possesses strong "
            "physical desire and may attract an equally passionate partner. While "
            "this placement requires conscious management of anger and ego in "
            "relationships, it also generates dynamic energy that can fuel "
            "shared achievements. The karmic lesson involves learning to channel "
            "warrior energy into partnership rather than conflict."
        ),
        "remedy": (
            "Classical remedy: Perform Kumbh Vivah (symbolic marriage to a "
            "banana plant or silver/gold idol) before actual marriage. Worship "
            "Lord Hanuman on Tuesdays and recite Hanuman Chalisa. Practice anger "
            "management and conscious communication in relationships. BPHS Ch. 39 "
            "recommends Mars remedies for relationship harmony."
        ),
    },
    "Saturn_7th": {
        "condition": "Saturn in 7th house",
        "interpretation": (
            "Saturn in the 7th house brings seriousness, responsibility, and "
            "potential delays in marriage and partnerships. The native may marry "
            "later in life or seek a mature, stable partner. While early "
            "relationship challenges build character, the eventual partnership "
            "is built on deep commitment and shared responsibility. The karmic "
            "lesson involves learning patience and maturity in relationships."
        ),
        "remedy": (
            "Classical remedy: Practice patience and develop maturity before "
            "committing to partnerships. Visit Shani temples on Saturdays. "
            "Chant 'Om Shanicharaya Namaha' and serve the elderly. BPHS Ch. 29 "
            "recommends Saturn remedies for relationship stability and longevity."
        ),
    },
    "Sun_12th": {
        "condition": "Sun in 12th house",
        "interpretation": (
            "Sun in the 12th house turns the native's energy inward toward "
            "spiritual pursuits, foreign lands, and behind-the-scenes activities. "
            "While there may be expenditures related to the father or governmental "
            "matters, the native finds true self-expression through meditation, "
            "spiritual retreats, or work in foreign countries. The karmic path "
            "involves finding inner authority beyond worldly recognition."
        ),
        "remedy": (
            "Classical remedy: Offer water to the rising Sun (Arghya) daily while "
            "reciting Aditya Hridayam. Practice meditation and spiritual retreats. "
            "Serve in foreign lands or spiritual institutions. BPHS Ch. 26 "
            "recommends Surya Upasana for strengthening inner authority."
        ),
    },
    "Moon_8th": {
        "condition": "Moon in 8th house",
        "interpretation": (
            "Moon in the 8th house brings emotional depth, transformative "
            "experiences, and sensitivity to life's hidden currents. The native "
            "may experience emotional upheavals that ultimately lead to profound "
            "psychological growth. Inheritance, occult interests, and research "
            "are prominent themes. Emotional resilience is developed through "
            "facing life's mysteries and embracing change."
        ),
        "remedy": (
            "Classical remedy: Practice regular meditation for emotional balance. "
            "Chant 'Om Chandraya Namaha' 108 times on Mondays. Worship at Shiva "
            "temples with bel leaves. Maintain emotional honesty and avoid "
            "suppression. Phaladeepika recommends Moon remedies for emotional "
            "stability and transformative growth."
        ),
    },
    "Jupiter_6th": {
        "condition": "Jupiter in 6th house",
        "interpretation": (
            "Jupiter in the 6th house, while in a dusthana house, provides "
            "protection through wisdom and moral authority in service, healing, "
            "and legal contexts. The native may work in healthcare, counseling, "
            "or charitable organizations. Health is generally good, and the "
            "native overcomes obstacles through faith and ethical conduct. The "
            "karmic lesson involves applying wisdom in practical, service-oriented "
            "ways."
        ),
        "remedy": (
            "Classical remedy: Serve in educational or charitable institutions. "
            "Chant 'Om Gurave Namaha' on Thursdays. Practice ethical conduct "
            "in daily service. BPHS Ch. 27 recommends Jupiter remedies for "
            "overcoming obstacles through wisdom and moral authority."
        ),
    },
    "Venus_6th": {
        "condition": "Venus in 6th house",
        "interpretation": (
            "Venus in the 6th house can create challenges in relationships and "
            "health, but also brings the ability to find beauty in service and "
            "daily routines. The native may work in healthcare, wellness, or "
            "aesthetic fields. Relationships require conscious effort and "
            "discernment, but the native's charm helps navigate conflicts "
            "gracefully."
        ),
        "remedy": (
            "Classical remedy: Practice devotion (bhakti) through art, music, "
            "or beauty. Serve in healthcare or wellness organizations. Chant "
            "'Om Shukraya Namaha' on Fridays. Offer white flowers at Lakshmi "
            "temples. Phaladeepika Ch. 10 recommends Venus remedies for "
            "relationship harmony and finding beauty in service."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 5. ASPECT THEMES (Planet Aspect Narratives)
# ══════════════════════════════════════════════════════════════════════════════
# Translates the raw aspect matrix into narrative text.

ASPECT_NARRATIVES: dict[str, str] = {
    "JUPITER_opposition": (
        "Jupiter's aspect brings protective wisdom, philosophical insight, "
        "and moral guidance to the receiving house. The native's relationships, "
        "higher learning, or spiritual practice are blessed with expansive "
        "energy and benevolent protection."
    ),
    "JUPITER_square_special": (
        "Jupiter's 5th aspect infuses creative intelligence, spiritual "
        "discrimination, and philosophical depth into the receiving house. "
        "The native's creativity, children, or speculative ventures benefit "
        "from Jupiter's wise and expansive influence."
    ),
    "JUPITER_trine_special": (
        "Jupiter's 9th aspect brings Dharma, good fortune, and philosophical "
        "blessings to the receiving house. This is one of the most auspicious "
        "aspects, bringing divine grace and spiritual protection to the "
        "native's higher learning, travel, or spiritual practice."
    ),
    "SATURN_opposition": (
        "Saturn's aspect brings discipline, structure, and karmic lessons to "
        "the receiving house. The native's partnerships, public life, or "
        "relationships are strengthened through patience, responsibility, and "
        "mature understanding. Challenges ultimately build enduring foundations."
    ),
    "SATURN_square_special": (
        "Saturn's 3rd aspect brings disciplined communication, methodical "
        "effort, and karmic responsibility to the receiving house. The native's "
        "courage, sibling relationships, or short journeys are structured and "
        "strengthened through persistent, ethical effort."
    ),
    "SATURN_trine_special": (
        "Saturn's 10th aspect brings career discipline, public responsibility, "
        "and karmic structure to the receiving house. The native's professional "
        "life, social status, or organizational abilities are strengthened "
        "through patient, methodical achievement."
    ),
    "MARS_opposition": (
        "Mars's aspect brings dynamic energy, courage, and protective force to "
        "the receiving house. The native's partnerships, public life, or "
        "relationships are energized and challenged to grow through bold, "
        "decisive action."
    ),
    "MARS_square_special": (
        "Mars's 4th aspect infuses protective courage, physical vitality, and "
        "assertive energy into the receiving house. The native's home life, "
        "emotional foundations, or property matters are energized through "
        "dynamic, protective action."
    ),
    "MARS_trine_special": (
        "Mars's 8th aspect brings transformative courage, research ability, "
        "and investigative power to the receiving house. The native's hidden "
        "talents, occult interests, or transformative experiences are energized "
        "through bold, penetrating inquiry."
    ),
    "opposition": (
        "The aspect between these planets creates a dynamic tension that "
        "stimulates growth through contrast and opposition. The native's "
        "challenge is to integrate opposing energies into a balanced, "
        "synthesized approach to life."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# 6. HOUSE SIGNIFICATIONS (for generating domain-grouped narratives)
# ══════════════════════════════════════════════════════════════════════════════

HOUSE_SIGNIFICATIONS: dict[int, dict[str, str]] = {
    1: {
        "name": "Lagna",
        "domain": "Personality & Self",
        "signifies": "Body, appearance, temperament, vitality, overall life direction",
    },
    2: {
        "name": "Dhana",
        "domain": "Wealth & Family",
        "signifies": "Family, accumulated wealth, speech, food, early education",
    },
    3: {
        "name": "Sahaja",
        "domain": "Communication & Courage",
        "signifies": "Siblings, courage, communication, short journeys, self-effort",
    },
    4: {
        "name": "Sukha",
        "domain": "Home & Happiness",
        "signifies": "Mother, home, property, vehicles, education, emotional peace",
    },
    5: {
        "name": "Putra",
        "domain": "Children & Creativity",
        "signifies": "Children, intelligence, creativity, romance, speculation, past life merit",
    },
    6: {
        "name": "Ripu",
        "domain": "Health & Service",
        "signifies": "Enemies, disease, debt, service, litigation, maternal uncle",
    },
    7: {
        "name": "Kalatra",
        "domain": "Marriage & Partnership",
        "signifies": "Spouse, business partnership, public dealings, sexual organs",
    },
    8: {
        "name": "Ayur",
        "domain": "Obstacles & Transformation",
        "signifies": "Longevity, obstacles, inheritance, occult, transformation, chronic disease",
    },
    9: {
        "name": "Dharma",
        "domain": "Fortune & Dharma",
        "signifies": "Father, fortune, philosophy, religion, long journeys, higher learning",
    },
    10: {
        "name": "Karma",
        "domain": "Career & Status",
        "signifies": "Career, profession, reputation, authority, government, social status",
    },
    11: {
        "name": "Labha",
        "domain": "Gains & Aspirations",
        "signifies": "Income, gains, fulfillment of desires, elder siblings, friends",
    },
    12: {
        "name": "Vyaya",
        "domain": "Loss & Liberation",
        "signifies": "Expenses, losses, foreign lands, sleep, dreams, spiritual liberation (moksha)",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# LOOKUP HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def get_planet_house_interpretation(planet: str, house: int) -> str | None:
    """Look up a planet-in-house interpretation.

    Args:
        planet: Planet name (uppercase, e.g., "SUN", "JUPITER").
        house: House number (1–12).

    Returns:
        Interpretive text, or None if not found.
    """
    planet_data = PLANETS_IN_HOUSES.get(planet.upper(), {})
    return planet_data.get(str(house))


def get_nakshatra_interpretation(planet: str, nakshatra: str) -> str | None:
    """Look up a planet-in-nakshatra interpretation.

    Args:
        planet: Planet name (uppercase).
        nakshatra: Nakshatra name (uppercase with underscores, e.g., "ASHWINI").

    Returns:
        Interpretive text, or None if not found.
    """
    planet_data = NAKSHATRA_INTERPRETATIONS.get(planet.upper(), {})
    return planet_data.get(nakshatra.upper())


def get_conjunction_interpretation(planets: list[str]) -> str | None:
    """Look up a conjunction interpretation for a set of planets.

    Args:
        planets: List of planet names involved in the conjunction.

    Returns:
        Interpretive text, or None if no matching conjunction is found.
    """
    key = frozenset(p.upper() for p in planets)
    return CONJUNCTION_INTERPRETATIONS.get(key)


def get_karmic_indicator(condition_key: str) -> dict[str, Any] | None:
    """Look up a karmic/predictive indicator.

    Args:
        condition_key: Key like "Ketu_12th", "Saturn_8th", etc.

    Returns:
        Dict with 'condition', 'interpretation', and 'remedy', or None.
    """
    return KARMIC_INDICATORS.get(condition_key)


def get_aspect_narrative(planet: str, aspect_type: str) -> str | None:
    """Look up a narrative for a specific planet aspect.

    Args:
        planet: Source planet name (uppercase).
        aspect_type: Type of aspect (e.g., "opposition", "trine_special").

    Returns:
        Narrative text, or None if not found.
    """
    # Try planet-specific first, then generic
    key = f"{planet.upper()}_{aspect_type}"
    result = ASPECT_NARRATIVES.get(key)
    if result:
        return result
    return ASPECT_NARRATIVES.get(aspect_type)


def get_house_signification(house: int) -> dict[str, str] | None:
    """Get the name, domain, and significations for a house number.

    Args:
        house: House number (1–12).

    Returns:
        Dict with 'name', 'domain', 'signifies' keys, or None.
    """
    return HOUSE_SIGNIFICATIONS.get(house)
