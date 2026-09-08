'use client';

import type { EvaluationResponse } from '@/lib/api';

// ── Dosha Types ──────────────────────────────────────────
interface DoshaResult {
  name: string;
  sanskrit_name: string;
  detected: boolean;
  severity: 'none' | 'low' | 'medium' | 'high';
  description: string;
  planets_involved: string[];
  remedy: string;
  mantra: string;
  temple: string;
  charity: string;
}

// ── Severity Colors ──────────────────────────────────────
function getSeverityColor(severity: string): { color: string; bg: string; icon: string } {
  switch (severity) {
    case 'high':
      return { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.1)', icon: '🔴' };
    case 'medium':
      return { color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)', icon: '🟡' };
    case 'low':
      return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.1)', icon: '🟢' };
    default:
      return { color: 'var(--cosmic-muted)', bg: 'rgba(138, 148, 166, 0.08)', icon: '⚪' };
  }
}

// ── Detect Doshas from Chart Data ────────────────────────
function detectDoshas(data: EvaluationResponse): DoshaResult[] {
  const pd = data.planet_details || {};
  const mars = pd.MARS;
  const saturn = pd.SATURN;
  const rahu = pd.RAHU;
  const ketu = pd.KETU;
  const moon = pd.MOON;
  const lagna = data.lagna;

  const SIGN_ORDER = [
    'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
    'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
  ];

  function getHouse(planetSign: string): number {
    const p = SIGN_ORDER.indexOf(planetSign);
    const l = SIGN_ORDER.indexOf(lagna);
    if (p < 0 || l < 0) return 0;
    return ((p - l) % 12 + 12) % 12 + 1;
  }

  // Manglik Dosha detection
  const manglikHouses = [1, 2, 4, 7, 8, 12];
  const marsHouse = mars ? getHouse(mars.sign) : 0;
  const isManglik = manglikHouses.includes(marsHouse);
  const manglikSeverity: DoshaResult['severity'] = !isManglik ? 'none' :
    marsHouse === 1 || marsHouse === 8 ? 'high' :
    marsHouse === 2 || marsHouse === 12 ? 'medium' : 'low';

  // Kaal Sarp Dosha (all planets between Rahu and Ketu)
  const rahuHouse = rahu ? getHouse(rahu.sign) : 0;
  const ketuHouse = ketu ? getHouse(ketu.sign) : 0;
  const allPlanetsBetweenRahuKetu = Object.entries(pd).every(([name, detail]) => {
    if (name === 'RAHU' || name === 'KETU') return true;
    const h = getHouse(detail.sign);
    if (rahuHouse < ketuHouse) {
      return h >= rahuHouse && h <= ketuHouse;
    } else {
      return h >= rahuHouse || h <= ketuHouse;
    }
  });
  const isKaalSarp = allPlanetsBetweenRahuKetu && rahuHouse !== 0 && ketuHouse !== 0;
  const kaalSarpSeverity: DoshaResult['severity'] = !isKaalSarp ? 'none' :
    rahuHouse === 1 || rahuHouse === 8 ? 'high' : 'medium';

  // Pitru Dosha (Sun afflicted by Rahu/Ketu or in 6th/8th/12th)
  const sunHouse = pd.SUN ? getHouse(pd.SUN.sign) : 0;
  const isPitruDosha = (sunHouse === 6 || sunHouse === 8 || sunHouse === 12) &&
    (rahuHouse === sunHouse || ketuHouse === sunHouse);
  const pitruSeverity: DoshaResult['severity'] = !isPitruDosha ? 'none' :
    sunHouse === 8 ? 'high' : 'medium';

  // Nadi Dosha (same nakshatra for both partners - simplified check)
  // This is typically checked in compatibility, but we can note it
  const isNadiDosha = false; // Requires partner data
  const nadiSeverity: DoshaResult['severity'] = 'none';

  return [
    {
      name: 'Manglik Dosha',
      sanskrit_name: 'मांगलिक दोष',
      detected: isManglik,
      severity: manglikSeverity,
      description: isManglik
        ? `Mars is placed in house ${marsHouse} (${['1st', '2nd', '4th', '7th', '8th', '12th'][manglikHouses.indexOf(marsHouse)] || `${marsHouse}th`} house from Lagna). This creates Manglik Dosha which can cause delays and challenges in marriage and relationships.`
        : 'Mars is not in a Manglik position. No Manglik Dosha detected.',
      planets_involved: isManglik ? ['MARS'] : [],
      remedy: 'Worship Lord Hanuman every Tuesday and Saturday. Chant Hanuman Chalisa daily.',
      mantra: 'Om Hanumate Namah — 108 times daily',
      temple: 'Hanuman Temple — visit every Tuesday',
      charity: 'Donate red lentils (masoor dal) on Tuesdays',
    },
    {
      name: 'Kaal Sarp Dosha',
      sanskrit_name: 'काल सर्प दोष',
      detected: isKaalSarp,
      severity: kaalSarpSeverity,
      description: isKaalSarp
        ? `All planets are positioned between Rahu and Ketu axis. Rahu in house ${rahuHouse}, Ketu in house ${ketuHouse}. This creates Kaal Sarp Dosha which can cause unexpected obstacles and karmic challenges.`
        : 'No Kaal Sarp Dosha detected — planets are not entirely between Rahu-Ketu axis.',
      planets_involved: isKaalSarp ? ['RAHU', 'KETU'] : [],
      remedy: 'Worship Lord Shiva and offer water to Shivalinga. Perform Kaal Sarp Dosha Nivaran Puja.',
      mantra: 'Om Namah Shivaya — 108 times daily',
      temple: 'Shiva Temple — visit on Mondays and during Shivaratri',
      charity: 'Donate to orphanages and feed the hungry',
    },
    {
      name: 'Pitru Dosha',
      sanskrit_name: 'पितृ दोष',
      detected: isPitruDosha,
      severity: pitruSeverity,
      description: isPitruDosha
        ? `Sun is in house ${sunHouse} and is conjoined with Rahu/Ketu. This creates Pitru Dosha which can cause obstacles in family lineage and ancestral blessings.`
        : 'No Pitru Dosha detected.',
      planets_involved: isPitruDosha ? ['SUN', rahuHouse === sunHouse ? 'RAHU' : 'KETU'] : [],
      remedy: 'Perform Tarpan (water offering) to ancestors. Offer sesame seeds and water on new moon days.',
      mantra: 'Om Pitrabhyah Swadha Namah — during Tarpan',
      temple: 'Ancestral temple or Shiva temple',
      charity: 'Feed Brahmins and donate to temples on Amavasya',
    },
    {
      name: 'Nadi Dosha',
      sanskrit_name: 'नाडी दोष',
      detected: isNadiDosha,
      severity: nadiSeverity,
      description: 'Nadi Dosha is checked during compatibility analysis when both partners have the same Nakshatra. This requires partner birth data to evaluate.',
      planets_involved: [],
      remedy: 'Perform Nadi Dosha Nivaran Puja at a specialized temple.',
      mantra: 'Chant Mahamrityunjaya Mantra 108 times daily',
      temple: 'Visit a Nadi Dosha Nivaran temple',
      charity: 'Donate to medical charities and hospitals',
    },
  ];
}

// ── Dosha Card Component ─────────────────────────────────
function DoshaCard({ dosha }: { dosha: DoshaResult }) {
  const severityStyle = getSeverityColor(dosha.severity);

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{ border: `1px solid ${severityStyle.color}30` }}
    >
      {/* Header */}
      <div className="px-4 py-3" style={{ background: severityStyle.bg }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{severityStyle.icon}</span>
            <div>
              <h4 className="font-bold text-sm" style={{ color: 'var(--cosmic-text)' }}>
                {dosha.name}
              </h4>
              <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
                {dosha.sanskrit_name}
              </p>
            </div>
          </div>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{ background: `${severityStyle.color}20`, color: severityStyle.color }}
          >
            {dosha.detected ? dosha.severity.toUpperCase() : 'NOT DETECTED'}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-3">
        <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
          {dosha.description}
        </p>

        {dosha.planets_involved.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {dosha.planets_involved.map((p) => (
              <span key={p} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>
                {p}
              </span>
            ))}
          </div>
        )}

        {dosha.detected && (
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="p-2 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <span style={{ color: 'var(--cosmic-muted)' }}>Mantra: </span>
              <span style={{ color: 'var(--cosmic-text)' }}>{dosha.mantra}</span>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <span style={{ color: 'var(--cosmic-muted)' }}>Temple: </span>
              <span style={{ color: 'var(--cosmic-text)' }}>{dosha.temple}</span>
            </div>
            <div className="p-2 rounded-lg col-span-2" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <span style={{ color: 'var(--cosmic-muted)' }}>Charity: </span>
              <span style={{ color: 'var(--cosmic-text)' }}>{dosha.charity}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────
interface DoshaAnalysisProps {
  data: EvaluationResponse;
}

export default function DoshaAnalysis({ data }: DoshaAnalysisProps) {
  const doshas = detectDoshas(data);
  const detectedDoshas = doshas.filter((d) => d.detected);

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
              Dosha Analysis
            </h3>
            <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
              {detectedDoshas.length > 0
                ? `${detectedDoshas.length} dosha(s) detected — remedies recommended`
                : 'No major doshas detected — chart is well-balanced'}
            </p>
          </div>
          <div className="text-2xl">
            {detectedDoshas.length === 0 ? '✅' : '⚠️'}
          </div>
        </div>
      </div>

      {/* Dosha Cards */}
      <div className="space-y-3">
        {doshas.map((dosha) => (
          <DoshaCard key={dosha.name} dosha={dosha} />
        ))}
      </div>
    </div>
  );
}
