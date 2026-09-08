'use client';

import type { EvaluationResponse } from '@/lib/api';

// ── Sign / Planet helpers ────────────────────────────────
const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
];
const SIGN_NAMES: Record<string, string> = {
  MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer',
  SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio',
  DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces',
};

function getHouse(planetSign: string, lagna: string): number {
  const p = SIGN_ORDER.indexOf(planetSign);
  const l = SIGN_ORDER.indexOf(lagna);
  if (p < 0 || l < 0) return 0;
  return ((p - l) % 12 + 12) % 12 + 1;
}

// ── Prediction Types ─────────────────────────────────────
interface Prediction {
  category: string;
  icon: string;
  title: string;
  summary: string;
  details: string[];
  strength: 'strong' | 'moderate' | 'challenging';
  keyPlanets: string[];
}

// ── Generate Predictions from Chart ──────────────────────
function generatePredictions(data: EvaluationResponse): Prediction[] {
  const pd = data.planet_details || {};
  const yogas = data.yogas || [];
  const lagna = data.lagna;

  function getLord(house: number): string | null {
    for (const [planet, detail] of Object.entries(pd)) {
      if (getHouse(detail.sign, lagna) === house) return planet;
    }
    return null;
  }

  const predictions: Prediction[] = [];

  // ── Career ──
  const tenthLord = getLord(10);
  const tenthSign = tenthLord ? pd[tenthLord]?.sign : null;
  const saturnHouse = pd.SATURN ? getHouse(pd.SATURN.sign, lagna) : 0;
  const careerStrength = saturnHouse === 10 || saturnHouse === 1 ? 'strong' :
    saturnHouse === 6 || saturnHouse === 11 ? 'moderate' : 'challenging';
  const careerYogas = yogas.filter((y) => y.status === 'FORMED' && y.domains?.includes('CAREER'));
  predictions.push({
    category: 'career',
    icon: '🏆',
    title: 'Career & Profession',
    summary: tenthLord
      ? `Your professional destiny is shaped by ${tenthLord} as the lord of the 10th house, placed in ${SIGN_NAMES[tenthSign || ''] || tenthSign || 'unknown'}. This placement indicates a career oriented toward ${tenthLord === 'SUN' ? 'leadership, government, and authority positions' : tenthLord === 'MOON' ? 'emotions, healing, public service, and nurturing roles' : tenthLord === 'MARS' ? 'courage, engineering, military, or competitive fields' : tenthLord === 'MERCURY' ? 'communication, commerce, analytics, and intellectual pursuits' : tenthLord === 'JUPITER' ? 'teaching, law, counseling, and spiritual guidance' : tenthLord === 'VENUS' ? 'arts, luxury, entertainment, and creative industries' : tenthLord === 'SATURN' ? 'discipline, administration, long-term projects, and organizational roles' : 'diverse professional domains'}. The 10th house cusp and its lord reveal your karmic calling — the work that aligns with your soul's purpose in this incarnation.\n\nSaturn's placement in House ${saturnHouse || '—'} ${saturnHouse === 10 ? 'strengthens career through discipline and perseverance, indicating authority earned through sustained effort' : saturnHouse === 11 ? 'brings gains through professional networks and long-term career building' : saturnHouse === 6 ? 'provides competitive advantage and victory over workplace obstacles' : 'adds a layer of karmic responsibility to professional matters'}. ${careerYogas.length > 0 ? `The presence of ${careerYogas.length} career-enhancing yoga(s) — including ${careerYogas.map((y) => y.yoga_name).join(', ')} — significantly amplifies professional potential and recognition.` : 'Career growth will be steady and earned through consistent dedication to your craft.'}\n\nThe interaction between the 10th lord and other functional planets creates a unique professional fingerprint. Your career path is not merely about material success but about fulfilling the dharmic obligations encoded in your birth chart. The houses aspecting the 10th house and its lord further refine this picture, revealing specific industries, roles, and timing of professional milestones.`
      : 'Career analysis requires 10th house lord calculation.',
    details: [`10th Lord: ${tenthLord || '—'} in ${SIGN_NAMES[tenthSign || ''] || tenthSign || '—'}`],
    strength: careerStrength as Prediction['strength'],
    keyPlanets: tenthLord ? [tenthLord, 'SATURN'] : ['SATURN'],
  });

  // ── Marriage ──
  const seventhLord = getLord(7);
  const venusHouse = pd.VENUS ? getHouse(pd.VENUS.sign, lagna) : 0;
  const marriageStrength = venusHouse === 7 || venusHouse === 12 ? 'strong' :
    venusHouse === 1 || venusHouse === 4 ? 'moderate' : 'challenging';
  predictions.push({
    category: 'marriage',
    icon: '💍',
    title: 'Marriage & Relationships',
    summary: seventhLord
      ? `Your relationship destiny is governed by ${seventhLord} as the lord of the 7th house, the domain of partnerships, marriage, and public dealings. The nature of ${seventhLord} determines the type of partner you attract and the dynamics of your closest bonds. Venus, the natural significator of love and harmony, occupies House ${venusHouse}, ${venusHouse === 7 ? 'creating exceptional romantic potential and natural charm in partnerships' : venusHouse === 12 ? 'suggesting spiritual or unconventional partnerships, possibly with foreign connections' : venusHouse === 1 ? 'blessing you with attractiveness and diplomatic skills in relationships' : 'adding its artistic and harmonious influence to your relational sphere'}. The 7th house conditions reveal not just when partnership arrives, but the quality and karmic lessons embedded within it.\n\nThe interaction between the 7th lord and Venus, along with any aspects from Jupiter or Saturn, creates the complex tapestry of your relational life. Mars influence on the 7th house or Venus can indicate passionate but sometimes turbulent dynamics, while Jupiter's aspect brings wisdom, expansion, and dharmic alignment to partnerships. The Dasha periods of the 7th lord and Venus mark the most significant relationship milestones — meetings, commitments, and transformative phases.\n\nYour marriage chart also reflects the balance between personal freedom and partnership commitment. The placement of Rahu and Ketu across the axis of relationships reveals karmic patterns from past lives that play out in your closest bonds. Understanding these dynamics allows you to navigate relationship challenges with awareness rather than reaction, transforming potential conflicts into opportunities for spiritual growth.`
      : 'Marriage analysis requires 7th house lord calculation.',
    details: [`7th Lord: ${seventhLord || '—'}`],
    strength: marriageStrength as Prediction['strength'],
    keyPlanets: seventhLord ? [seventhLord, 'VENUS'] : ['VENUS'],
  });

  // ── Health ──
  const marsHouse = pd.MARS ? getHouse(pd.MARS.sign, lagna) : 0;
  const healthStrength = marsHouse === 1 || marsHouse === 3 || marsHouse === 6 ? 'moderate' :
    marsHouse === 8 || marsHouse === 12 ? 'challenging' : 'strong';
  predictions.push({
    category: 'health',
    icon: '⚕️',
    title: 'Health & Wellbeing',
    summary: `Your physical constitution is primarily influenced by Mars (vitality, energy, surgery) occupying House ${marsHouse || '—'} and Saturn (chronic conditions, endurance, aging) in House ${saturnHouse || '—'}. ${marsHouse === 1 ? 'Mars in the 1st house grants exceptional physical vitality, strong immune response, and natural athletic ability. Your body has a robust constitution that recovers quickly from illness.' : marsHouse === 6 ? 'Mars in the 6th house is a powerful placement for overcoming diseases, defeating health challenges, and maintaining competitive physical fitness.' : marsHouse === 8 ? 'Mars in the 8th house requires attention to sudden health events, surgical tendencies, and transformative health crises that ultimately lead to deeper self-awareness.' : marsHouse === 12 ? 'Mars in the 12th house suggests health issues that may manifest through hospitalization, hidden ailments, or sleep-related disturbances. Regular preventive care is essential.' : 'Mars in this house creates a specific health pattern that benefits from awareness and proactive wellness strategies.'}\n\nSaturn's placement in House ${saturnHouse || '—'} ${saturnHouse === 1 ? 'indicates a need for careful health management throughout life, with potential for chronic conditions that require disciplined lifestyle choices.' : saturnHouse === 6 ? 'is excellent for health — Saturn in the 6th house creates strong disease resistance and victory over health obstacles.' : saturnHouse === 8 ? 'brings longevity concerns but also transformative health experiences that deepen self-understanding.' : saturnHouse === 12 ? 'may indicate health expenses, hospitalization tendencies, or conditions requiring isolation for recovery.' : 'adds specific health considerations that benefit from awareness of Saturnian timing cycles.'} The 6th house lord and its placement further reveals the nature of health challenges and the body's innate healing capacity.\n\nThe Moon's condition reflects mental and emotional health — a strong Moon indicates psychological resilience, while a afflicted Moon may manifest as anxiety, emotional instability, or psychosomatic conditions. Regular physical exercise, balanced nutrition, and awareness of your body's natural rhythms are recommended. The Dasha periods of Mars, Saturn, and the 6th/8th house lords mark times when health requires extra vigilance.`,
    details: [`Mars in house ${marsHouse || '—'}`, `Saturn in house ${saturnHouse || '—'}`],
    strength: healthStrength as Prediction['strength'],
    keyPlanets: ['MARS', 'SATURN'],
  });

  // ── Finance ──
  const secondLord = getLord(2);
  const eleventhLord = getLord(11);
  const financeStrength = yogas.some((y) => y.yoga_name === 'Dhana' && y.status === 'FORMED') ? 'strong' :
    yogas.some((y) => y.yoga_name === 'Dhana' && y.status === 'WEAKENED') ? 'moderate' : 'moderate';
  const dhanaYogas = yogas.filter((y) => y.yoga_name === 'Dhana' && y.status === 'FORMED');
  predictions.push({
    category: 'finance',
    icon: '💰',
    title: 'Finance & Wealth',
    summary: `Your financial destiny is governed by the 2nd house lord ${secondLord || '—'} (accumulated wealth, family resources, speech) and the 11th house lord ${eleventhLord || '—'} (gains, income, fulfillment of desires). The interplay between these two houses determines your capacity for wealth accumulation and the channels through which financial prosperity flows into your life. ${secondLord === 'JUPITER' || secondLord === 'VENUS' ? 'Jupiter or Venus as 2nd lord creates strong wealth accumulation potential through wisdom, teaching, arts, or luxury goods.' : secondLord === 'SATURN' ? 'Saturn as 2nd lord indicates wealth built through patience, discipline, and long-term strategic planning — fortune favors your persistence.' : secondLord === 'MERCURY' ? 'Mercury as 2nd lord brings financial intelligence, commercial acumen, and gains through communication, trade, or analytical work.' : 'The specific nature of your 2nd lord creates unique pathways for wealth creation.'}\n\n${dhanaYogas.length > 0 ? `The presence of ${dhanaYogas.length} Dhana Yoga(s) — including ${dhanaYogas.map((y) => y.yoga_name).join(', ')} — significantly enhances your wealth potential. These yogas indicate that financial prosperity is encoded in your karmic blueprint and will manifest during the appropriate Dasha periods.` : 'While no specific Dhana Yogas are formed, wealth accumulation is still possible through consistent effort, wise investments, and alignment with your chart\'s financial indicators.'} Jupiter's aspect on the 2nd or 11th house amplifies financial blessings, while Saturn's influence brings delayed but substantial rewards through persistent effort.\n\nThe timing of financial peaks correlates strongly with the Dasha periods of the 2nd lord, 11th lord, and Jupiter (the natural significator of wealth expansion). Rahu's placement can indicate sudden, unexpected gains or losses — financial events that feel fated or karmic. Understanding these patterns allows you to make informed decisions about investments, career moves, and financial planning that align with your chart's natural prosperity cycles.`,
    details: [`2nd Lord: ${secondLord || '—'}`, `11th Lord: ${eleventhLord || '—'}`],
    strength: financeStrength as Prediction['strength'],
    keyPlanets: secondLord && eleventhLord ? [secondLord, eleventhLord] : ['JUPITER', 'VENUS'],
  });

  // ── Family ──
  const fourthLord = getLord(4);
  const ninthLord = getLord(9);
  predictions.push({
    category: 'family',
    icon: '👨‍👩‍👧‍👦',
    title: 'Family & Home',
    summary: `Your family dynamics are governed by the 4th house lord ${fourthLord || '—'} (mother, home, domestic happiness, property) and the 9th house lord ${ninthLord || '—'} (father, fortune, higher learning, spiritual lineage). ${fourthLord === 'MOON' ? 'Moon as 4th lord creates a deeply nurturing home environment where emotional bonds are paramount. Your mother plays a significant role in shaping your inner world, and domestic peace is essential for your overall wellbeing.' : fourthLord === 'VENUS' ? 'Venus as 4th lord blesses your home with beauty, comfort, and artistic sensibility. Property matters tend to be favorable, and your living spaces reflect refined taste and harmonious energy.' : fourthLord === 'JUPITER' ? 'Jupiter as 4th lord brings wisdom, expansion, and dharmic values to your family environment. Education, spiritual practices, and philosophical discussions are central to your home life.' : fourthLord === 'SATURN' ? 'Saturn as 4th lord indicates a structured, disciplined home environment where responsibilities are taken seriously. Property matters may involve delays but ultimately lead to stable foundations.' : 'The nature of your 4th lord creates specific patterns in your domestic and family life.'}\n\n${ninthLord === 'JUPITER' ? 'Jupiter as 9th lord strengthens the father figure, fortune, and spiritual inclinations. Higher education and philosophical pursuits bring fulfillment.' : ninthLord === 'SUN' ? 'Sun as 9th lord indicates a strong, authoritative father figure and dharmic authority. Government connections and leadership roles in spiritual or educational institutions are favored.' : ninthLord === 'MOON' ? 'Moon as 9th lord brings emotional connection to father and fortune through nurturing, healing, and public service activities.' : 'The 9th lord\'s placement reveals the nature of your fortune, father relationship, and spiritual path.'} The 4th-9th house axis creates a fundamental tension between domestic comfort and spiritual expansion — finding balance between these poles is a key life lesson.\n\nFamily harmony depends on the condition of the 4th house, its lord, and the Moon. Ketu's placement can indicate detachment from family roots or unconventional family structures, while Rahu may bring foreign or unusual family dynamics. The Dasha periods of the 4th and 9th lords mark significant family events — property acquisitions, mother's health matters, father-related events, or spiritual awakenings that reshape family relationships.`,
    details: [`4th Lord: ${fourthLord || '—'}`, `9th Lord: ${ninthLord || '—'}`],
    strength: 'moderate' as Prediction['strength'],
    keyPlanets: fourthLord && ninthLord ? [fourthLord, ninthLord] : ['MOON', 'JUPITER'],
  });

  // ── Spirituality ──
  const ketuHouse = pd.KETU ? getHouse(pd.KETU.sign, lagna) : 0;
  const spiritualityStrength = ketuHouse === 9 || ketuHouse === 12 ? 'strong' :
    ketuHouse === 1 || ketuHouse === 5 ? 'moderate' : 'moderate';
  predictions.push({
    category: 'spirituality',
    icon: '🕉️',
    title: 'Spirituality & Dharma',
    summary: `Your spiritual blueprint is revealed through Ketu's placement in House ${ketuHouse || '—'} and the 9th house lord ${ninthLord || '—'}. ${ketuHouse === 9 ? 'Ketu in the 9th house indicates deep past-life spiritual merit and natural access to higher wisdom. You are a born seeker who instinctively understands dharmic principles and may be drawn to teaching or guiding others on their spiritual path.' : ketuHouse === 12 ? 'Ketu in the 12th house is the classic moksha indicator — your soul has mastered material lessons and now seeks liberation. Foreign lands, isolation, meditation, and spiritual retreats call to you with particular power.' : ketuHouse === 1 ? 'Ketu in the 1st house creates a personality that oscillates between worldly engagement and spiritual detachment. Past-life spiritual mastery manifests as intuitive wisdom, but attachment to ego identity remains a karmic lesson.' : ketuHouse === 5 ? 'Ketu in the 5th house indicates past-life creative and spiritual merit, with strong intuitive abilities and potential for children who are spiritually advanced souls.' : 'Ketu\'s placement reveals where your soul has already mastered lessons and where detachment comes naturally.'}\n\n${ninthLord === 'JUPITER' ? 'Jupiter as 9th lord creates a powerful dharmic channel — higher learning, philosophical inquiry, and spiritual teaching are central to your life purpose. Pilgrimages, guru connections, and scriptural study bring profound fulfillment.' : ninthLord === 'SATURN' ? 'Saturn as 9th lord indicates a disciplined, structured approach to spirituality. Your dharmic path may involve patience, perseverance, and unconventional teachers who challenge established beliefs.' : ninthLord === 'SUN' ? 'Sun as 9th lord brings spiritual authority and dharmic leadership. Your father or father figures play a significant role in shaping your spiritual values and life direction.' : 'The 9th lord\'s placement reveals the nature of your spiritual path and dharmic obligations.'} The 9th-12th house axis is the primary indicator of spiritual evolution — strong placements here suggest a soul oriented toward transcendence rather than material accumulation.\n\nYour spiritual practice should align with your chart's dominant elements and planetary influences. Jupiter-dominant charts benefit from mantra meditation, scriptural study, and teaching. Saturn-dominant charts resonate with disciplined practices, service to the elderly, and patience-based meditation. Ketu-dominant charts favor meditation, past-life regression, and detachment practices. The Dasha periods of Ketu, Jupiter, and the 9th/12th lords mark times of spiritual awakening, guru connections, and transformative mystical experiences that reshape your understanding of reality.`,
    details: [`Ketu in house ${ketuHouse || '—'}`, `9th Lord: ${ninthLord || '—'}`],
    strength: spiritualityStrength as Prediction['strength'],
    keyPlanets: ninthLord && pd.KETU ? [ninthLord, 'KETU'] : ['JUPITER', 'KETU'],
  });

  return predictions;
}

// ── Prediction Card ──────────────────────────────────────
function PredictionCard({ prediction }: { prediction: Prediction }) {
  const strengthConfig = {
    strong: { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.06)', label: 'Strong' },
    moderate: { color: 'var(--cosmic-gold)', bg: 'rgba(197, 168, 128, 0.06)', label: 'Moderate' },
    challenging: { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.06)', label: 'Challenging' },
  };

  const cfg = strengthConfig[prediction.strength];

  return (
    <div className="rounded-2xl overflow-hidden" style={{ border: `1px solid ${cfg.color}30` }}>
      <div className="px-4 py-3" style={{ background: cfg.bg }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{prediction.icon}</span>
            <h4 className="font-bold text-sm" style={{ color: 'var(--cosmic-text)' }}>
              {prediction.title}
            </h4>
          </div>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{ background: `${cfg.color}20`, color: cfg.color }}
          >
            {cfg.label}
          </span>
        </div>
      </div>

      <div className="px-4 py-3 space-y-3">
        <div className="text-xs leading-relaxed whitespace-pre-line" style={{ color: 'var(--cosmic-muted)' }}>
          {prediction.summary}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {prediction.keyPlanets.map((p) => (
            <span key={p} className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.08)', color: 'var(--cosmic-gold)' }}>
              {p}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────
interface LifePredictionsProps {
  data: EvaluationResponse;
}

export default function LifePredictions({ data }: LifePredictionsProps) {
  const predictions = generatePredictions(data);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
          Life Predictions — Comprehensive Analysis
        </h3>
        <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
          Detailed narratives based on planetary positions, house lords, dignities, aspects, and formed yogas in your chart
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {predictions.map((pred) => (
          <PredictionCard key={pred.category} prediction={pred} />
        ))}
      </div>
    </div>
  );
}
