'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Star, LayoutGrid, Globe, Zap, BookOpen, Gem,
  ChevronRight, AlertCircle, ArrowUp, AlertTriangle,
} from 'lucide-react';
import NorthIndianChart from '@/components/NorthIndianChart';
import PlanetaryTable from '@/components/PlanetaryTable';
import ShadbalaTable from '@/components/ShadbalaTable';
import AshtakavargaTable from '@/components/AshtakavargaTable';
import RemediesPanel from '@/components/RemediesPanel';
import NumerologyPanel from '@/components/NumerologyPanel';
import SouthIndianChart from '@/components/SouthIndianChart';
import DoshaAnalysis from '@/components/DoshaAnalysis';
import LifePredictions from '@/components/LifePredictions';
import { ChartSkeleton, ErrorBanner } from '@/components/LoadingSkeleton';
import { api } from '@/lib/api';
import type {
  EvaluationResponse,
  ShadbalaResponse,
  AshtakavargaResponse,
  RemedyResponse,
  DivisionalChartResponse,
  AspectMatrixResult,
  GocharTransitResult,
  RelationshipAnalysisResult,
  PlanetaryStateInfo,
  NakshatraExchangeResult,
  DailyTransitAspect,
  DeepDashaResult,
} from '@/lib/api';
import yogaDescriptions from '@/lib/yoga_descriptions.json';
import houseEffects from '@/lib/house_effects.json';

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
const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};
const HOUSE_NAMES: Record<number, string> = {
  1: 'Personality & Self', 2: 'Wealth & Family', 3: 'Communication & Courage',
  4: 'Home & Happiness', 5: 'Children & Creativity', 6: 'Health & Service',
  7: 'Partnerships & Marriage', 8: 'Obstacles & Transformation',
  9: 'Fortune & Dharma', 10: 'Career & Status', 11: 'Gains & Aspirations',
  12: 'Loss & Liberation',
};

function getHouse(planetSign: string, lagna: string): number {
  const p = SIGN_ORDER.indexOf(planetSign);
  const l = SIGN_ORDER.indexOf(lagna);
  if (p < 0 || l < 0) return 0;
  return ((p - l) % 12 + 12) % 12 + 1;
}

// ── Layman interpretations for yogas ─────────────────────
const LAYMAN_YOGA: Record<string, string> = {
  'Gajakesari': 'A powerful prosperity yoga — Jupiter and Moon together bring wisdom, wealth, and lasting reputation.',
  'Raja': 'A career-defining yoga — indicates leadership, authority, and rise to prominence.',
  'Dhana': 'A wealth yoga — promises financial abundance through effort and good fortune.',
  'Budhaditya': 'Intellectual brilliance — Sun and Mercury together sharpen communication and analytical mind.',
  'Vipareeta Raja': 'Success through adversity — challenges transform into unexpected victories.',
  'Malavya': 'Artistic and relational harmony — Venus in strength brings beauty, love, and luxury.',
  'Ruchaka': 'Mars-powered leadership — courage, military or entrepreneurial success.',
  'Bhadra': 'Mercury-powered intellect — excellent for business, communication, and teaching.',
  'Hamsa': 'Jupiter-powered wisdom — spiritual depth, teaching ability, and moral authority.',
  'Sasa': 'Saturn-powered discipline — political power, organizational leadership, longevity.',
  'Sunapha': 'Mental strength and social status from Moon\'s neighboring planet.',
  'Anapha': 'Wealth and prestige through one\'s own effort.',
  'Dhudhara': 'Double prosperity — planets on both sides of Moon amplify wealth.',
  'Amala': 'Clean karma — a benefic in the 10th house ensures a virtuous career.',
  'Neecha Bhanga': 'Debilitation cancelled — a weakened planet gets a second chance to shine.',
  'Saraswati': 'Scholarship and artistic mastery — Jupiter, Mercury, and Venus bless learning.',
};

// ── Navigation Sections ──────────────────────────────────
interface NavSection {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_SECTIONS: NavSection[] = [
  { id: 'overview', label: 'Overview', icon: <Star size={14} /> },
  { id: 'charts', label: 'Charts', icon: <LayoutGrid size={14} /> },
  { id: 'planets', label: 'Planets', icon: <Globe size={14} /> },
  { id: 'strength', label: 'Strength', icon: <Zap size={14} /> },
  { id: 'dasha', label: 'Dasha', icon: <BookOpen size={14} /> },
  { id: 'yogas', label: 'Yogas', icon: <Gem size={14} /> },
  { id: 'doshas', label: 'Doshas', icon: <AlertCircle size={14} /> },
  { id: 'aspects', label: 'Aspects', icon: <Globe size={14} /> },
  { id: 'gochar', label: 'Gochar', icon: <Star size={14} /> },
  { id: 'daily-transits', label: 'Transits', icon: <Star size={14} /> },
  { id: 'nakshatra', label: 'Nakshatra', icon: <Star size={14} /> },
  { id: 'predictions', label: 'Predictions', icon: <Star size={14} /> },
  { id: 'remedies', label: 'Remedies', icon: <Gem size={14} /> },
  { id: 'numerology', label: 'Numerology', icon: <Star size={14} /> },
  { id: 'intimacy', label: 'Intimacy', icon: <Star size={14} /> },
];

// ══════════════════════════════════════════════════════════
// SECTION COMPONENTS
// ══════════════════════════════════════════════════════════

// ── Section Card Wrapper ─────────────────────────────────
function SectionCard({
  id,
  title,
  icon,
  children,
}: {
  id: string;
  title: string;
  icon?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-20">
      <div className="mb-4 flex items-center gap-2">
        {icon && <span className="text-lg">{icon}</span>}
        <h2
          className="text-xl font-bold"
          style={{
            color: 'var(--cosmic-text)',
            fontFamily: 'var(--font-playfair), Georgia, serif',
          }}
        >
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

// ── Section 1: Overview ──────────────────────────────────
function OverviewSection({ data }: { data: EvaluationResponse }) {
  const birth = data.birth_data_display;
  const lagnaSign = SIGN_NAMES[data.lagna] || data.lagna;
  const moonNakshatra = data.moon_nakshatra || '—';

  // Big Three
  const bigThree = [
    {
      icon: '🌌',
      label: 'Lagna (Ascendant)',
      sign: lagnaSign,
      interp: 'Your rising sign shapes your physical constitution, personality, and life direction.',
    },
    {
      icon: '☉',
      label: 'Sun (Soul)',
      sign: SIGN_NAMES[data.planet_details?.SUN?.sign] || data.planet_details?.SUN?.sign || '—',
      interp: 'Your Sun sign reveals your core purpose, vitality, and how you shine in the world.',
    },
    {
      icon: '☽',
      label: 'Moon (Mind)',
      sign: SIGN_NAMES[data.planet_details?.MOON?.sign] || data.planet_details?.MOON?.sign || '—',
      interp: 'Your Moon sign reflects your emotional nature, intuition, and inner world.',
    },
  ];

  const eb = data.elemental_balance || {};

  return (
    <SectionCard id="overview" title="Overview & Birth Details" icon="🕉️">
      {/* Birth Details */}
      <div
        className="rounded-2xl p-5 mb-4"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Subject</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{data.subject}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Lagna</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-gold)' }}>{lagnaSign}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Moon Nakshatra</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{moonNakshatra}</p>
          </div>
          {birth?.date && (
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Date of Birth</p>
              <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{birth.date}</p>
            </div>
          )}
          {birth?.time && (
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Time of Birth</p>
              <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{birth.time}</p>
            </div>
          )}
          {birth?.timezone && (
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Timezone</p>
              <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{birth.timezone}</p>
            </div>
          )}
          {birth?.latitude && (
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Latitude</p>
              <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{birth.latitude}</p>
            </div>
          )}
          {birth?.longitude && (
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Longitude</p>
              <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{birth.longitude}</p>
            </div>
          )}
        </div>

        {/* Elemental & Modality Balance */}
        <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--glass-border)' }}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--cosmic-muted)' }}>Elemental Balance</p>
              <div className="flex gap-3">
                {[
                  { key: 'fire', label: '🔥', color: '#ef4444' },
                  { key: 'earth', label: '🌍', color: '#22c55e' },
                  { key: 'air', label: '💨', color: '#3b82f6' },
                  { key: 'water', label: '💧', color: '#8b5cf6' },
                ].map(({ key, label, color }) => (
                  <div key={key} className="text-center">
                    <div className="text-lg font-bold" style={{ color }}>{eb[key] || 0}</div>
                    <div className="text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>{label} {key}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--cosmic-muted)' }}>Modality Balance</p>
              <div className="flex gap-3">
                {Object.entries(data.modality_balance || {}).map(([modality, count]) => (
                  <div key={modality} className="text-center">
                    <div className="text-sm font-bold" style={{ color: 'var(--cosmic-text)' }}>{count}</div>
                    <div className="text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>{modality}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Big Three */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {bigThree.map((b) => (
          <div
            key={b.label}
            className="rounded-2xl p-5 text-center"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
          >
            <div className="text-3xl mb-2">{b.icon}</div>
            <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: 'var(--cosmic-muted)' }}>{b.label}</p>
            <p className="text-xl font-bold mb-1" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>{b.sign}</p>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{b.interp}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

// ── Section 2: Visual Charts ─────────────────────────────
function ChartsSection({ data, d9Data, d9Loading }: { data: EvaluationResponse; d9Data: DivisionalChartResponse | null; d9Loading: boolean }) {
  const [chartType, setChartType] = useState<'north' | 'south'>('north');

  // Convert D9 API response to planetDetails format for chart rendering
  const d9PlanetDetails = useMemo(() => {
    if (!d9Data?.planets) return data.planet_details;
    const result: Record<string, { sign: string; degree_in_sign: number }> = {};
    for (const [planet, pd] of Object.entries(d9Data.planets)) {
      result[planet] = {
        sign: pd.rashi,
        degree_in_sign: pd.degree_in_sign,
      };
    }
    return result;
  }, [d9Data, data.planet_details]);

  const d9Lagna = d9Data?.lagna || data.lagna;

  return (
    <SectionCard id="charts" title="Visual Charts" icon="📊">
      {/* Chart Type Toggle */}
      <div className="flex gap-2 mb-4">
        <button
          type="button"
          onClick={() => setChartType('north')}
          className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all"
          style={{
            background: chartType === 'north' ? 'rgba(197, 168, 128, 0.15)' : 'var(--glass-bg)',
            border: `1px solid ${chartType === 'north' ? 'var(--cosmic-gold)' : 'var(--glass-border)'}`,
            color: chartType === 'north' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
          }}
        >
          North Indian (Diamond)
        </button>
        <button
          type="button"
          onClick={() => setChartType('south')}
          className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all"
          style={{
            background: chartType === 'south' ? 'rgba(197, 168, 128, 0.15)' : 'var(--glass-bg)',
            border: `1px solid ${chartType === 'south' ? 'var(--cosmic-gold)' : 'var(--glass-border)'}`,
            color: chartType === 'south' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
          }}
        >
          South Indian (Square)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* D1 Chart */}
        <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--cosmic-gold)' }}>
            Rashi Chart (D-1)
          </h3>
          {chartType === 'north' ? (
            <NorthIndianChart lagna={data.lagna} planetDetails={data.planet_details} divisionalType="D1" />
          ) : (
            <SouthIndianChart lagna={data.lagna} planetDetails={data.planet_details} divisionalType="D1" />
          )}
        </div>

        {/* D9 Chart */}
        <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--cosmic-gold)' }}>
            Navamsha Chart (D-9)
          </h3>
          {d9Loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
              <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Loading D9 chart…</span>
            </div>
          ) : chartType === 'north' ? (
            <NorthIndianChart lagna={d9Lagna} planetDetails={d9PlanetDetails} divisionalType="D9" />
          ) : (
            <SouthIndianChart lagna={d9Lagna} planetDetails={d9PlanetDetails} divisionalType="D9" />
          )}

          {/* D9 Planetary Positions Table */}
          {d9Data?.planets && Object.keys(d9Data.planets).length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--cosmic-gold)' }}>
                D9 Planetary Positions
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                      <th className="px-2 py-1.5 text-left">Planet</th>
                      <th className="px-2 py-1.5 text-left">Sign</th>
                      <th className="px-2 py-1.5 text-right">Degree</th>
                      <th className="px-2 py-1.5 text-center">House</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(d9Data.planets).map(([planet, pd]) => {
                      const signName = { MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer', SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio', DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces' }[pd.rashi] || pd.rashi;
                      const lagnaIdx = ['MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA', 'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA'].indexOf(d9Lagna);
                      const planetIdx = ['MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA', 'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA'].indexOf(pd.rashi);
                      const house = lagnaIdx >= 0 && planetIdx >= 0 ? ((planetIdx - lagnaIdx) % 12 + 12) % 12 + 1 : 0;
                      return (
                        <tr key={planet} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                          <td className="px-2 py-1.5 font-medium" style={{ color: 'var(--cosmic-text)' }}>{planet}</td>
                          <td className="px-2 py-1.5" style={{ color: 'var(--cosmic-text)' }}>{signName}</td>
                          <td className="px-2 py-1.5 text-right font-mono" style={{ color: 'var(--cosmic-muted)' }}>{pd.degree_in_sign.toFixed(2)}°</td>
                          <td className="px-2 py-1.5 text-center">
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded text-xs font-semibold" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>{house}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </SectionCard>
  );
}

// ── Conjunction Effects ──────────────────────────────────
function getConjunctionEffects(data: EvaluationResponse): { planets: string[]; effect: string }[] {
  const pd = data.planet_details || {};
  const lagna = data.lagna;
  const SIGN_ORDER = ['MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA', 'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA'];
  function getHouse(sign: string): number {
    const p = SIGN_ORDER.indexOf(sign);
    const l = SIGN_ORDER.indexOf(lagna);
    if (p < 0 || l < 0) return 0;
    return ((p - l) % 12 + 12) % 12 + 1;
  }

  // Group planets by house
  const housePlanets: Record<number, string[]> = {};
  for (const [planet, detail] of Object.entries(pd)) {
    const h = getHouse(detail.sign);
    if (h >= 1 && h <= 12) {
      if (!housePlanets[h]) housePlanets[h] = [];
      housePlanets[h].push(planet);
    }
  }

  const conjunctionEffects: Record<string, string> = {
    'SUN-MOON': 'Amavasya birth — strong emotional duality, powerful intuition, spiritual depth.',
    'SUN-MARS': 'Fiery personality, courageous leadership, strong willpower, prone to anger.',
    'SUN-MERCURY': 'Budhaditya Yoga — intellectual brilliance, sharp communication, analytical mind.',
    'SUN-JUPITER': 'Spiritual authority, philosophical mind, teaching ability, moral strength.',
    'SUN-VENUS': 'Artistic leadership, creative authority, charm with power.',
    'SUN-SATURN': 'Disciplined authority, responsible leadership, patience with power.',
    'MOON-MARS': 'Emotional courage, passionate nature, protective instincts, intensity.',
    'MOON-MERCURY': 'Communicative emotions, witty mind, artistic expression, emotional intelligence.',
    'MOON-JUPITER': 'Gajakesari Yoga — wisdom, wealth, lasting reputation, philosophical mind.',
    'MOON-VENUS': 'Romantic emotions, artistic sensitivity, emotional beauty, creative love.',
    'MOON-SATURN': 'Emotional discipline, serious nature, patient emotions, deep feelings.',
    'MARS-MERCURY': 'Sharp communication, competitive intellect, technological mind, athletic intelligence.',
    'MARS-JUPITER': 'Spiritual courage, philosophical warrior, righteous action, moral strength.',
    'MARS-VENUS': 'Passionate creativity, artistic courage, romantic intensity, physical attraction.',
    'MARS-SATURN': 'Disciplined courage, patient action, strategic thinking, enduring strength.',
    'MERCURY-JUPITER': 'Wise communication, philosophical intellect, teaching ability, analytical wisdom.',
    'MERCURY-VENUS': 'Artistic intellect, creative communication, beautiful expression, musical talent.',
    'MERCURY-SATURN': 'Disciplined thinking, patient analysis, strategic mind, practical wisdom.',
    'JUPITER-VENUS': 'Saraswati Yoga — scholarship, artistic mastery, wisdom with beauty.',
    'JUPITER-SATURN': 'Philosophical discipline, spiritual patience, wise action, balanced growth.',
    'VENUS-SATURN': 'Disciplined love, patient relationships, artistic discipline, enduring beauty.',
  };

  const results: { planets: string[]; effect: string }[] = [];
  for (const [, planets] of Object.entries(housePlanets)) {
    if (planets.length >= 2) {
      // Check all pairs
      for (let i = 0; i < planets.length; i++) {
        for (let j = i + 1; j < planets.length; j++) {
          const key1 = `${planets[i]}-${planets[j]}`;
          const key2 = `${planets[j]}-${planets[i]}`;
          const effect = conjunctionEffects[key1] || conjunctionEffects[key2];
          if (effect) {
            results.push({ planets: [planets[i], planets[j]], effect });
          }
        }
      }
    }
  }
  return results;
}

// ── Section 3: Planetary Positions ───────────────────────
function PlanetsSection({ data, planetaryStates }: { data: EvaluationResponse; planetaryStates?: Record<string, PlanetaryStateInfo> }) {
  const conjunctions = getConjunctionEffects(data);
  const pd = data.planet_details || {};
  const lagna = data.lagna;
  const SIGN_ORDER = ['MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA', 'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA'];
  function getHouse(sign: string): number {
    const p = SIGN_ORDER.indexOf(sign);
    const l = SIGN_ORDER.indexOf(lagna);
    if (p < 0 || l < 0) return 0;
    return ((p - l) % 12 + 12) % 12 + 1;
  }

  return (
    <SectionCard id="planets" title="Planetary Positions & Effects" icon="🪐">
      <div className="space-y-6">
        <PlanetaryTable lagna={data.lagna} planetDetails={data.planet_details} dignityMap={data.dignity_map} planetaryStates={planetaryStates || undefined} showState={true} />

        {/* Planet-in-House Effects */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)' }}>Planet-in-House Effects</h3>
          <div className="space-y-2">
            {Object.entries(pd).map(([planet, detail]) => {
              const house = getHouse(detail.sign);
              const effects = (houseEffects as Record<string, Record<string, any>>)[planet];
              const effect = effects?.[String(house)]?.effect;
              if (!effect) return null;
              return (
                <div key={planet} className="p-2 rounded-lg" style={{ background: 'rgba(26, 20, 35, 0.3)' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">{PLANET_SYMBOLS[planet] || ''}</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{planet}</span>
                    <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>in House {house}</span>
                  </div>
                  <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{effect}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Conjunction Effects */}
        {conjunctions.length > 0 && (
          <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)' }}>Conjunction Effects</h3>
            <div className="space-y-2">
              {conjunctions.map((conj, idx) => (
                <div key={idx} className="p-2 rounded-lg" style={{ background: 'rgba(197, 168, 128, 0.04)' }}>
                  <div className="flex items-center gap-2 mb-1">
                    {conj.planets.map((p) => (
                      <span key={p} className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>
                        {PLANET_SYMBOLS[p] || ''} {p}
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{conj.effect}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </SectionCard>
  );
}

// ── Section 4: Strengths ─────────────────────────────────
function StrengthSection({
  shadbalaData,
  ashtakavargaData,
  shadbalaLoading,
  ashtakavargaLoading,
  shadbalaError,
  ashtakavargaError,
}: {
  shadbalaData: ShadbalaResponse | null;
  ashtakavargaData: AshtakavargaResponse | null;
  shadbalaLoading: boolean;
  ashtakavargaLoading: boolean;
  shadbalaError: string | null;
  ashtakavargaError: string | null;
}) {
  return (
    <SectionCard id="strength" title="Strength & Ashtakavarga" icon="💪">
      <div className="space-y-6">
        <ShadbalaTable data={shadbalaData} loading={shadbalaLoading} error={shadbalaError} />
        <AshtakavargaTable data={ashtakavargaData} loading={ashtakavargaLoading} error={ashtakavargaError} />
      </div>
    </SectionCard>
  );
}

// ── Section 5: Dasha ────────────────────────────────────
function DashaSection({ data, dashaData, dashaLoading, dashaError }: {
  data: EvaluationResponse;
  dashaData: DeepDashaResult | null;
  dashaLoading: boolean;
  dashaError?: string | null;
}) {
  // Prefer dedicated API data, fall back to evaluation response
  const dasha = dashaData || data.deep_dasha;

  if (dashaLoading && !dasha?.md) {
    return (
      <SectionCard id="dasha" title="Vimshottari Dasha" icon="⏳">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin w-5 h-5 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing Dasha periods…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  if (!dasha?.md) {
    return (
      <SectionCard id="dasha" title="Vimshottari Dasha" icon="⏳">
        <div
          className="rounded-2xl p-6 text-center"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <p style={{ color: '#ef4444' }}>{dashaError ? `Failed to load Dasha: ${dashaError}` : 'Dasha calculation pending — ensure birth data is complete.'}</p>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard id="dasha" title="Vimshottari Dasha" icon="⏳">
      <div
        className="rounded-2xl p-5"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        {/* Current Dasha Hierarchy */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Mahadasha', data: dasha.md, color: 'var(--cosmic-gold)' },
            { label: 'Antardasha', data: dasha.ad, color: 'var(--benefic-green)' },
            { label: 'Pratyantardasha', data: dasha.pd, color: '#60a5fa' },
            { label: 'Sookshma', data: dasha.sd, color: '#c084fc' },
          ].map((level) => (
            <div
              key={level.label}
              className="rounded-xl p-3"
              style={{ background: 'rgba(26, 20, 35, 0.5)', border: `1px solid ${level.color}30` }}
            >
              <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: level.color }}>
                {level.label}
              </div>
              <div className="text-sm font-bold" style={{ color: 'var(--cosmic-text)' }}>
                {PLANET_SYMBOLS[level.data.lord] || ''} {level.data.lord}
              </div>
              <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
                {level.data.duration_years?.toFixed(1)}y
              </div>
              {level.data.start_utc && (
                <div className="text-[9px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                  {new Date(level.data.start_utc).toLocaleDateString()} → {new Date(level.data.end_utc).toLocaleDateString()}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* AD Timeline */}
        {dasha.ad_timeline && dasha.ad_timeline.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--cosmic-muted)' }}>
              ANTARDASHA TIMELINE
            </h4>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {dasha.ad_timeline.map((period: any, idx: number) => {
                const isActive = period.lord === dasha.md.lord;
                return (
                  <div
                    key={idx}
                    className="flex-shrink-0 rounded-lg p-2 text-center min-w-[80px]"
                    style={{
                      background: isActive ? 'rgba(197, 168, 128, 0.15)' : 'rgba(26, 20, 35, 0.4)',
                      border: isActive ? '1px solid var(--cosmic-gold)' : '1px solid var(--glass-border)',
                    }}
                  >
                    <div className="text-[10px] font-bold" style={{ color: isActive ? 'var(--cosmic-gold)' : 'var(--cosmic-text)' }}>
                      {period.lord}
                    </div>
                    <div className="text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>
                      {period.duration_years?.toFixed(1)}y
                    </div>
                    {isActive && <div className="text-[8px] mt-0.5 text-green-400">ACTIVE</div>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Activation Multiplier */}
        <div className="mt-4 p-3 rounded-xl" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>Activation Multiplier</span>
            <span className="text-sm font-bold" style={{ color: 'var(--cosmic-gold)' }}>
              {dasha.activation_multiplier?.toFixed(2)}x
            </span>
          </div>
          <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            {dasha.activation_multiplier >= 1.5 ? 'Peak activation — MD lord is a yoga planet' :
             dasha.activation_multiplier >= 1.25 ? 'Strong activation — AD lord is a yoga planet' :
             dasha.activation_multiplier >= 1.1 ? 'Moderate activation — PD lord is a yoga planet' :
             'Dormant period — no direct yoga planet activation'}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

// ── Yoga Detail Card ─────────────────────────────────────
function YogaDetailCard({ yoga, idx }: { yoga: EvaluationResponse['yogas'][0]; idx: number }) {
  const status = yoga.status || 'FORMED';
  const statusColor =
    status === 'FORMED' ? 'var(--benefic-green)' :
    status === 'CANCELLED' ? 'var(--malefic-red)' : '#eab308';
  const desc = (yogaDescriptions as Record<string, any>)[yoga.yoga_name];

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: 'var(--glass-bg)', border: `1px solid ${statusColor}30` }}
    >
      {/* Header */}
      <div className="px-4 py-3" style={{ background: `${statusColor}10` }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold" style={{ color: 'var(--cosmic-text)' }}>
              {yoga.yoga_name} Yoga
            </span>
            {desc?.sanskrit_name && (
              <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
                {desc.sanskrit_name}
              </span>
            )}
          </div>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{ background: `${statusColor}20`, color: statusColor }}
          >
            {status}
          </span>
        </div>
        {desc?.classical_reference && (
          <p className="text-[9px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            📖 {desc.classical_reference}
          </p>
        )}
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-3">
        {/* Description */}
        <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
          {desc?.description || LAYMAN_YOGA[yoga.yoga_name] || `Involves ${yoga.involved_planets.join(' and ')}.`}
        </p>

        {/* Planets & Domains */}
        <div className="flex flex-wrap gap-2">
          {yoga.involved_planets.map((p) => (
            <span key={p} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>
              {PLANET_SYMBOLS[p] || ''} {p}
            </span>
          ))}
          {yoga.domains?.map((d) => (
            <span key={d} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--cosmic-muted)' }}>
              {d}
            </span>
          ))}
        </div>

        {/* Positive Effects */}
        {desc?.positive_effects && desc.positive_effects.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--benefic-green)' }}>
              ✨ Positive Effects
            </p>
            <ul className="space-y-0.5">
              {desc.positive_effects.slice(0, 3).map((effect: string, i: number) => (
                <li key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: 'var(--cosmic-muted)' }}>
                  <span style={{ color: 'var(--benefic-green)' }}>•</span>
                  {effect}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Challenges */}
        {desc?.challenges && desc.challenges.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#eab308' }}>
              ⚠️ Challenges
            </p>
            <ul className="space-y-0.5">
              {desc.challenges.slice(0, 2).map((ch: string, i: number) => (
                <li key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: 'var(--cosmic-muted)' }}>
                  <span style={{ color: '#eab308' }}>•</span>
                  {ch}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Remedies */}
        {desc?.remedies && desc.remedies.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: '#c084fc' }}>
              🙏 Remedies
            </p>
            <ul className="space-y-0.5">
              {desc.remedies.slice(0, 2).map((rem: string, i: number) => (
                <li key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: 'var(--cosmic-muted)' }}>
                  <span style={{ color: '#c084fc' }}>•</span>
                  {rem}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Cancellation Reason */}
        {yoga.cancellation_reason && (
          <p className="text-[10px] p-2 rounded-lg" style={{ background: status === 'CANCELLED' ? 'rgba(239,68,68,0.08)' : 'rgba(234,179,8,0.08)', color: status === 'CANCELLED' ? '#f87171' : '#facc15' }}>
            ⚠ {yoga.cancellation_reason}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Section 6: Yogas & Doshas ────────────────────────────
function YogasSection({ data }: { data: EvaluationResponse }) {
  const yogas = data.yogas || [];
  const parivartanas = data.parivartana_yogas || [];
  const formed = yogas.filter((y) => y.status === 'FORMED');
  const weakened = yogas.filter((y) => y.status === 'WEAKENED');
  const cancelled = yogas.filter((y) => y.status === 'CANCELLED');

  return (
    <SectionCard id="yogas" title="Yogas, Doshas & Parivartana" icon="🕉️">
      <div className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div className="text-lg font-bold" style={{ color: 'var(--benefic-green)' }}>{formed.length}</div>
            <div className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>Formed</div>
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(234, 179, 8, 0.06)', border: '1px solid rgba(234, 179, 8, 0.2)' }}>
            <div className="text-lg font-bold" style={{ color: '#eab308' }}>{weakened.length}</div>
            <div className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>Weakened</div>
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <div className="text-lg font-bold" style={{ color: 'var(--malefic-red)' }}>{cancelled.length}</div>
            <div className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>Cancelled</div>
          </div>
        </div>

        {/* Classical Yogas with Full Details */}
        {yogas.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)' }}>
              Classical Yogas ({yogas.length})
            </h3>
            <div className="space-y-3">
              {yogas.map((yoga, idx: number) => (
                <YogaDetailCard key={idx} yoga={yoga} idx={idx} />
              ))}
            </div>
          </div>
        )}

        {/* Parivartana Yogas */}
        {parivartanas.length > 0 && (
          <div
            className="rounded-2xl p-5"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
          >
            <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)' }}>
              Parivartana Yogas ({parivartanas.length})
            </h3>
            <div className="space-y-2">
              {parivartanas.map((pv: any, idx: number) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg"
                  style={{ background: 'rgba(26, 20, 35, 0.3)' }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium" style={{ color: 'var(--cosmic-text)' }}>
                      {pv.planet_a} ↔ {pv.planet_b}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>
                      {pv.exchange_type}
                    </span>
                  </div>
                  {pv.narrative && (
                    <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
                      {pv.narrative}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {yogas.length === 0 && parivartanas.length === 0 && (
          <div
            className="rounded-2xl p-6 text-center"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
          >
            <p style={{ color: 'var(--cosmic-muted)' }}>No yogas evaluated yet.</p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}

// ── Section 7: Aspects ──────────────────────────────────
function AspectsSection({ data, aspectsData, aspectsLoading, aspectsError }: {
  data: EvaluationResponse;
  aspectsData: AspectMatrixResult | null;
  aspectsLoading: boolean;
  aspectsError: string | null;
}) {
  // Prefer dedicated API data, fall back to evaluation response
  const aspects = aspectsData?.all_aspects || (data as any).aspect_matrix_full || (data as any).aspect_matrix || [];
  const planetSummaries = aspectsData?.planet_summaries || [];

  // Group aspects by type
  const seventhAspects = aspects.filter((a: any) => (a.aspect_type || '').includes('7th'));
  const specialAspects = aspects.filter((a: any) => !(a.aspect_type || '').includes('7th'));

  if (aspectsLoading) {
    return (
      <SectionCard id="aspects" title="Aspect Matrix (Drishti)" icon="🔭">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing aspects…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard id="aspects" title="Aspect Matrix (Drishti)" icon="🔭">
      <div className="space-y-4">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div className="rounded-xl p-3" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
            <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>Total Aspects</div>
            <div className="text-lg font-bold mt-1" style={{ color: 'var(--cosmic-gold)' }}>{aspects.length}</div>
          </div>
          <div className="rounded-xl p-3" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
            <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>7th (Universal)</div>
            <div className="text-lg font-bold mt-1" style={{ color: 'var(--benefic-green)' }}>{seventhAspects.length}</div>
          </div>
          <div className="rounded-xl p-3" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
            <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>Special Aspects</div>
            <div className="text-lg font-bold mt-1" style={{ color: '#60a5fa' }}>{specialAspects.length}</div>
          </div>
        </div>

        {/* Error state */}
        {aspectsError && (
          <div className="rounded-xl p-3" style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <p className="text-xs" style={{ color: '#fca5a5' }}>Aspect computation issue: {aspectsError}</p>
          </div>
        )}

        {/* Full Aspect List — Srirangam style */}
        {aspects.length > 0 ? (
          <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
              <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
                ALL PLANETARY ASPECTS
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                Every planet aspects the 7th house from its position. Mars, Jupiter, and Saturn have additional special aspects.
              </p>
            </div>

            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {aspects.map((asp: any, idx: number) => {
                const srcPlanet = asp.source_planet || asp.aspecter || '';
                const tgtPlanet = asp.target_planet || asp.aspected || '';
                const srcHouse = asp.source_house || 0;
                const tgtHouse = asp.target_house || 0;
                const aspectType = asp.aspect_type || '7th';
                const isSpecial = aspectType !== '7th';
                const quality = asp.orb_quality || '';
                const orb = asp.orb_degrees ?? 0;
                const strength = asp.strength ?? 0;

                // Readable sentence format
                const aspectLabel = isSpecial
                  ? `gives special ${aspectType} aspect to`
                  : 'aspects';
                const sentence = `${srcPlanet} from ${srcHouse > 0 ? `${srcHouse}${getOrdinalSuffix(srcHouse)}` : '?'} house ${aspectLabel} ${tgtPlanet} in ${tgtHouse > 0 ? `${tgtHouse}${getOrdinalSuffix(tgtHouse)}` : '?'} house with its ${aspectType} aspect.`;

                return (
                  <div
                    key={idx}
                    className="px-4 py-3 transition-colors duration-150"
                    style={{ background: isSpecial ? 'rgba(96, 165, 250, 0.03)' : 'transparent' }}
                  >
                    <div className="flex items-start gap-3">
                      {/* Planet symbols */}
                      <div className="flex items-center gap-1 shrink-0">
                        <span className="text-base">{PLANET_SYMBOLS[srcPlanet] || '●'}</span>
                        <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>→</span>
                        <span className="text-base">{PLANET_SYMBOLS[tgtPlanet] || '●'}</span>
                      </div>

                      {/* Sentence */}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>
                          <span className="font-semibold">{srcPlanet}</span>
                          {srcHouse > 0 && <span style={{ color: 'var(--cosmic-muted)' }}> ({srcHouse}{getOrdinalSuffix(srcHouse)} house)</span>}
                          {' '}<span style={{ color: 'var(--cosmic-gold)' }}>{aspectLabel}</span>{' '}
                          <span className="font-semibold">{tgtPlanet}</span>
                          {tgtHouse > 0 && <span style={{ color: 'var(--cosmic-muted)' }}> ({tgtHouse}{getOrdinalSuffix(tgtHouse)} house)</span>}
                        </p>
                      </div>

                      {/* Tags */}
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                          style={{
                            background: isSpecial ? 'rgba(96, 165, 250, 0.1)' : 'rgba(197, 168, 128, 0.08)',
                            color: isSpecial ? '#60a5fa' : 'var(--cosmic-gold)',
                          }}
                        >
                          {aspectType}
                        </span>
                        {quality && (
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded"
                            style={{
                              background: quality === 'EXACT' ? 'rgba(16, 185, 129, 0.1)' : quality === 'APPLYING' ? 'rgba(234, 179, 8, 0.08)' : 'rgba(138, 148, 166, 0.06)',
                              color: quality === 'EXACT' ? 'var(--benefic-green)' : quality === 'APPLYING' ? '#eab308' : 'var(--cosmic-muted)',
                            }}
                          >
                            {quality}
                          </span>
                        )}
                        {orb > 0 && (
                          <span className="text-[10px] font-mono" style={{ color: 'var(--cosmic-muted)' }}>
                            {orb.toFixed(1)}°
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div
            className="rounded-2xl p-6 text-center"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
          >
            <p style={{ color: 'var(--cosmic-muted)' }}>No aspect data computed. Ensure birth data is complete.</p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}

// ── Ordinal suffix helper ───────────────────────────────
function getOrdinalSuffix(n: number): string {
  if (n >= 11 && n <= 13) return 'th';
  switch (n % 10) {
    case 1: return 'st';
    case 2: return 'nd';
    case 3: return 'rd';
    default: return 'th';
  }
}

// ── Section 8: Remedies ──────────────────────────────────
function RemediesSection({
  remedyData,
  loading,
}: {
  remedyData: RemedyResponse | null;
  loading: boolean;
}) {
  return (
    <SectionCard id="remedies" title="Parihara & Remedies" icon="📿">
      <RemediesPanel data={remedyData} loading={loading} />
    </SectionCard>
  );
}

// ── Section 9: Numerology ────────────────────────────────
function NumerologySection({
  data,
}: {
  data: EvaluationResponse;
}) {
  const birthDate = data.birth_data_display?.date || '';
  const name = data.subject || '';

  return (
    <SectionCard id="numerology" title="Numerology" icon="🔢">
      <NumerologyPanel
        showInput={true}
        initialBirthDate={birthDate}
        initialName={name}
      />
    </SectionCard>
  );
}

// ── Section: Gochar Transit Predictions ─────────────────
function GocharTransitSection({
  gocharData,
  gocharLoading,
  gocharError,
}: {
  gocharData: GocharTransitResult | null;
  gocharLoading: boolean;
  gocharError: string | null;
}) {
  if (gocharLoading) {
    return (
      <SectionCard id="gochar" title="Gochar Transit Predictions" icon="🌍">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing transit predictions…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  if (!gocharData) {
    return (
      <SectionCard id="gochar" title="Gochar Transit Predictions" icon="🌍">
        <div className="rounded-2xl p-6 text-center" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <p style={{ color: 'var(--cosmic-muted)' }}>Transit predictions not available.</p>
        </div>
      </SectionCard>
    );
  }

  const predictions = gocharData.predictions || [];
  const transitAspects = gocharData.transit_to_transit_aspects || [];

  // Group predictions by transit planet
  const byPlanet: Record<string, typeof predictions> = {};
  for (const pred of predictions) {
    if (!byPlanet[pred.transit_planet]) byPlanet[pred.transit_planet] = [];
    byPlanet[pred.transit_planet].push(pred);
  }

  const SEVERITY_COLORS: Record<string, { color: string; bg: string }> = {
    positive: { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.06)' },
    negative: { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.06)' },
    mixed: { color: '#eab308', bg: 'rgba(234, 179, 8, 0.06)' },
    neutral: { color: 'var(--cosmic-muted)', bg: 'transparent' },
  };

  return (
    <SectionCard id="gochar" title="Gochar Transit Predictions" icon="🌍">
      <div className="space-y-4">
        {/* Overall Assessment */}
        <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--cosmic-gold)' }}>Current Transit Assessment</h3>
          <div className="space-y-2">
            {gocharData.overall_assessment.split('. ').filter(Boolean).map((sentence, i) => (
              <p key={i} className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>
                {sentence.endsWith('.') ? sentence : sentence + '.'}
              </p>
            ))}
          </div>
        </div>

        {/* Error */}
        {gocharError && (
          <div className="rounded-xl p-3" style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <p className="text-xs" style={{ color: '#fca5a5' }}>Transit calculation issue: {gocharError}</p>
          </div>
        )}

        {/* Transit-to-Transit Aspects (primary section) */}
        {transitAspects.length > 0 && (
          <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid rgba(197, 168, 128, 0.3)' }}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)', background: 'rgba(197, 168, 128, 0.06)' }}>
              <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
                ⭐ COSMIC WEATHER — TRANSIT-TO-TRANSIT ASPECTS ({transitAspects.length})
              </h3>
              <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                Current planetary geometries and their combined influence on life areas
              </p>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {transitAspects.map((asp, idx) => {
                const sev = SEVERITY_COLORS[asp.severity] || SEVERITY_COLORS.neutral;
                return (
                  <div key={idx} className="px-4 py-3" style={{ background: sev.bg }}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{PLANET_SYMBOLS[asp.transit_planet] || ''}</span>
                      <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{asp.transit_planet}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>{asp.aspect_type}</span>
                      {asp.target_planet && (
                        <>
                          <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>→</span>
                          <span className="text-sm">{PLANET_SYMBOLS[asp.target_planet] || ''}</span>
                          <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{asp.target_planet}</span>
                        </>
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{asp.prediction}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Predictions by Planet */}
        {Object.entries(byPlanet).map(([planet, preds]) => (
          <div key={planet} className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
              <div className="flex items-center gap-2">
                <span className="text-lg">{PLANET_SYMBOLS[planet] || ''}</span>
                <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
                  {planet} Transit Effects
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>
                  {preds.length} effects
                </span>
              </div>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {preds.map((pred, idx) => {
                const sev = SEVERITY_COLORS[pred.severity] || SEVERITY_COLORS.neutral;
                return (
                  <div key={idx} className="px-4 py-3" style={{ background: sev.bg }}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ background: `${sev.color}20`, color: sev.color }}>
                          House {pred.transit_house}
                        </span>
                        <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>{pred.category}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${sev.color}15`, color: sev.color }}>
                        {pred.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{pred.prediction}</p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}


      </div>
    </SectionCard>
  );
}

// ── Section: Nakshatra Parivartana (Exchanges) ─────────
function NakshatraSection({
  nakshatraData,
  nakshatraLoading,
}: {
  nakshatraData: NakshatraExchangeResult | null;
  nakshatraLoading: boolean;
}) {
  if (nakshatraLoading) {
    return (
      <SectionCard id="nakshatra" title="Nakshatra Parivartana (Exchanges)" icon="⭐">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin w-5 h-5 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing Nakshatra exchanges…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  if (!nakshatraData) return null;

  const natalExchanges = nakshatraData.natal_exchanges || [];
  const transitExchanges = nakshatraData.transit_exchanges || [];
  const natalNakshatras = nakshatraData.natal_nakshatras || {};

  return (
    <SectionCard id="nakshatra" title="Nakshatra Parivartana (Exchanges)" icon="⭐">
      <div className="space-y-4">
        {/* Natal Nakshatra Positions */}
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>Natal Nakshatra Positions</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  <th className="px-3 py-2 text-left">Planet</th>
                  <th className="px-3 py-2 text-left">Nakshatra</th>
                  <th className="px-3 py-2 text-center">Pada</th>
                  <th className="px-3 py-2 text-left">Lord</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(natalNakshatras).map((nk) => (
                  <tr key={nk.planet} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    <td className="px-3 py-2 font-medium" style={{ color: 'var(--cosmic-text)' }}>{nk.planet}</td>
                    <td className="px-3 py-2" style={{ color: 'var(--cosmic-text)' }}>{nk.nakshatra_name}</td>
                    <td className="px-3 py-2 text-center" style={{ color: 'var(--cosmic-gold)' }}>{nk.pada}</td>
                    <td className="px-3 py-2" style={{ color: 'var(--cosmic-muted)' }}>{nk.nakshatra_lord}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Natal Exchanges */}
        {natalExchanges.length > 0 && (
          <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid rgba(197, 168, 128, 0.3)' }}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)', background: 'rgba(197, 168, 128, 0.06)' }}>
              <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
                ⚡ Natal Nakshatra Exchanges ({natalExchanges.length})
              </h3>
              <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>Lifelong patterns from birth chart</p>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {natalExchanges.map((ex, idx) => (
                <div key={idx} className="px-4 py-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{ex.planet_a}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>↔</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{ex.planet_b}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(16,185,129,0.1)', color: 'var(--benefic-green)' }}>{ex.strength}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{ex.reading}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Transit Exchanges */}
        {transitExchanges.length > 0 && (
          <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid rgba(96, 165, 250, 0.3)' }}>
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)', background: 'rgba(96, 165, 250, 0.06)' }}>
              <h3 className="text-sm font-semibold" style={{ color: '#60a5fa' }}>
                🌍 Transit Nakshatra Exchanges ({transitExchanges.length})
              </h3>
              <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>Temporary triggers from current transits</p>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {transitExchanges.map((ex, idx) => (
                <div key={idx} className="px-4 py-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{ex.planet_a}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(96,165,250,0.1)', color: '#60a5fa' }}>↔</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{ex.planet_b}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{ex.reading}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {natalExchanges.length === 0 && transitExchanges.length === 0 && (
          <div className="rounded-2xl p-6 text-center" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <p style={{ color: 'var(--cosmic-muted)' }}>No Nakshatra exchanges detected in natal or transit charts.</p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}

// ── Section: Day-by-Day Transit Aspects ─────────────────
function DailyTransitSection({
  dailyTransits,
  dailyTransitsLoading,
}: {
  dailyTransits: DailyTransitAspect[] | null;
  dailyTransitsLoading: boolean;
}) {
  if (dailyTransitsLoading) {
    return (
      <SectionCard id="daily-transits" title="Day-by-Day Transit Aspects" icon="📅">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin w-5 h-5 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing day-by-day transits…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  if (!dailyTransits || dailyTransits.length === 0) return null;

  // Group by date
  const byDate: Record<string, DailyTransitAspect[]> = {};
  for (const dt of dailyTransits) {
    if (!byDate[dt.date]) byDate[dt.date] = [];
    byDate[dt.date].push(dt);
  }

  const SEVERITY_COLORS: Record<string, { color: string; bg: string }> = {
    positive: { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.04)' },
    negative: { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.04)' },
    mixed: { color: '#eab308', bg: 'rgba(234, 179, 8, 0.04)' },
    neutral: { color: 'var(--cosmic-muted)', bg: 'transparent' },
  };

  return (
    <SectionCard id="daily-transits" title="Day-by-Day Transit Aspects" icon="📅">
      <div className="space-y-3">
        <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
          Major transit aspects for the next {Object.keys(byDate).length} days, with planetary states.
        </p>
        {Object.entries(byDate).map(([date, aspects]) => (
          <div key={date} className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <div className="px-4 py-2 border-b" style={{ borderColor: 'var(--glass-border)' }}>
              <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-gold)' }}>{date}</span>
              <span className="text-[10px] ml-2" style={{ color: 'var(--cosmic-muted)' }}>({aspects.length} aspects)</span>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {aspects.slice(0, 5).map((asp, idx) => {
                const sev = SEVERITY_COLORS[asp.severity] || SEVERITY_COLORS.neutral;
                return (
                  <div key={idx} className="px-4 py-2" style={{ background: sev.bg }}>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold" style={{ color: sev.color }}>{asp.transit_planet}</span>
                      <span className="text-[10px] px-1 py-0.5 rounded" style={{ background: asp.transit_state.includes('R') ? 'rgba(239,68,68,0.1)' : asp.transit_state.includes('C') ? 'rgba(249,115,22,0.1)' : 'rgba(16,185,129,0.1)', color: asp.transit_state.includes('R') ? '#f87171' : asp.transit_state.includes('C') ? '#fb923c' : 'var(--benefic-green)' }}>
                        {asp.transit_state}
                      </span>
                      <span className="text-[10px]" style={{ color: 'var(--cosmic-gold)' }}>{asp.aspect_type}</span>
                      <span className="text-[10px] font-semibold" style={{ color: 'var(--cosmic-text)' }}>{asp.target}</span>
                    </div>
                  </div>
                );
              })}
              {aspects.length > 5 && (
                <p className="text-[10px] text-center py-2" style={{ color: 'var(--cosmic-muted)' }}>+ {aspects.length - 5} more</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

// ── Section 10: Intimacy & Relationship Dynamics ────────
function IntimacySection({ data, relationshipData, relationshipLoading }: {
  data: EvaluationResponse;
  relationshipData: RelationshipAnalysisResult | null;
  relationshipLoading: boolean;
}) {
  const [showSensitive, setShowSensitive] = useState(false);

  if (relationshipLoading) {
    return (
      <SectionCard id="intimacy" title="Intimacy & Relationship Dynamics" icon="💕">
        <div className="rounded-2xl p-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing relationship analysis…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  // Loading state
  if (!relationshipData) {
    return (
      <SectionCard id="intimacy" title="Intimacy & Relationship Dynamics" icon="💕">
        <div className="rounded-2xl p-6 text-center" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin w-4 h-4 border-2 border-t-transparent rounded-full" style={{ borderColor: 'var(--cosmic-gold)', borderTopColor: 'transparent' }} />
            <span className="ml-2 text-xs" style={{ color: 'var(--cosmic-muted)' }}>Computing relationship analysis…</span>
          </div>
        </div>
      </SectionCard>
    );
  }

  const allInsights = [
    ...relationshipData.venus_analysis,
    ...relationshipData.mars_analysis,
    ...relationshipData.seventh_lord_analysis,
    ...relationshipData.rahu_ketu_analysis,
  ];
  const combinations = relationshipData.classical_combinations || [];
  const hasSensitiveIndicators = combinations.some(c => c.analysis_type === 'affair_indicator');

  const STRENGTH_COLORS: Record<string, { color: string; bg: string }> = {
    strong: { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.06)' },
    moderate: { color: 'var(--cosmic-gold)', bg: 'rgba(197, 168, 128, 0.06)' },
    challenging: { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.06)' },
  };

  return (
    <div className="space-y-4">
      {/* Overall Assessment */}
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>Relationship Profile</h3>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
            style={{
              background: STRENGTH_COLORS[relationshipData.relationship_strength]?.bg || 'transparent',
              color: STRENGTH_COLORS[relationshipData.relationship_strength]?.color || 'var(--cosmic-muted)',
            }}
          >
            {relationshipData.relationship_strength.toUpperCase()}
          </span>
        </div>
        {/* Render the 4-part structured assessment */}
        {relationshipData.overall_assessment.split('PSYCHOLOGICAL FOUNDATION: ').length > 1 ? (
          <div className="space-y-3 mt-3">
            {(() => {
              const full = relationshipData.overall_assessment;
              const parts: { title: string; icon: string; color: string; text: string }[] = [];
              const psychMatch = full.match(/PSYCHOLOGICAL FOUNDATION:\s*([\s\S]*?)(?=\s*RISK FACTORS:|$)/);
              const riskMatch = full.match(/RISK FACTORS:\s*([\s\S]*?)(?=\s*TIMING:|$)/);
              const timingMatch = full.match(/TIMING:\s*([\s\S]*?)(?=\s*PROTECTIVE LAYER:|$)/);
              const protectiveMatch = full.match(/PROTECTIVE LAYER:\s*([\s\S]*$)/);
              if (psychMatch) parts.push({ title: 'Psychological Foundation & Desire Nature', icon: '🧠', color: '#8b5cf6', text: psychMatch[1].trim() });
              if (riskMatch) parts.push({ title: 'Behavioral Risk Factors & Triggers', icon: '⚠️', color: riskMatch[1].includes('No severe') ? 'var(--benefic-green)' : '#eab308', text: riskMatch[1].trim() });
              if (timingMatch) parts.push({ title: 'Timing Windows & Vulnerability Cycles', icon: '📅', color: timingMatch[1].includes('No major') ? 'var(--benefic-green)' : '#fb923c', text: timingMatch[1].trim() });
              if (protectiveMatch) parts.push({ title: 'Protective Layer & Mitigation', icon: '🛡️', color: 'var(--benefic-green)', text: protectiveMatch[1].trim() });
              return parts.map((part, i) => (
                <div key={i} className="rounded-xl p-3" style={{ background: `${part.color}08`, border: `1px solid ${part.color}25` }}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">{part.icon}</span>
                    <h4 className="text-xs font-semibold" style={{ color: part.color }}>{part.title}</h4>
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{part.text}</p>
                </div>
              ));
            })()}
          </div>
        ) : (
          <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{relationshipData.overall_assessment}</p>
        )}
      </div>

      {/* Detailed Insights from Backend Engine */}
      <div className="space-y-3">
        {allInsights.map((insight, idx) => {
          const strengthStyle = STRENGTH_COLORS[insight.strength_indicator] || STRENGTH_COLORS.moderate;
          return (
            <div
              key={idx}
              className="rounded-2xl overflow-hidden"
              style={{ background: 'var(--glass-bg)', border: `1px solid ${strengthStyle.color}30` }}
            >
              <div className="px-4 py-3" style={{ background: strengthStyle.bg }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{insight.planet === 'VENUS' ? '♀' : insight.planet === 'MARS' ? '♂' : insight.planet === 'RAHU-KETU' ? '☊☋' : '💍'}</span>
                    <h4 className="text-sm font-semibold" style={{ color: 'var(--cosmic-text)' }}>{insight.title}</h4>
                  </div>
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                    style={{ background: `${strengthStyle.color}20`, color: strengthStyle.color }}
                  >
                    {insight.strength_indicator.toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="px-4 py-3 space-y-2">
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{insight.description}</p>
                {insight.specific_combinations.map((combo, ci) => (
                  <p key={ci} className="text-[10px] leading-relaxed pl-3" style={{ color: 'var(--cosmic-muted)', borderLeft: '2px solid rgba(197,168,128,0.2)' }}>
                    • {combo}
                  </p>
                ))}
                {insight.classical_reference && (
                  <p className="text-[9px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>📖 {insight.classical_reference}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Classical Combinations */}
      {combinations.length > 0 && (
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>Classical Combinations Detected</h3>
          </div>
          <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
            {combinations.map((combo, idx) => (
              <div key={idx} className="px-4 py-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold" style={{ color: 'var(--cosmic-text)' }}>{combo.title}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(197,168,128,0.08)', color: 'var(--cosmic-gold)' }}>{combo.category}</span>
                </div>
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{combo.description}</p>
                {combo.specific_combinations.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {combo.specific_combinations.map((sc, si) => (
                      <p key={si} className="text-[10px] pl-3" style={{ color: 'var(--cosmic-muted)', borderLeft: '2px solid rgba(197,168,128,0.2)' }}>
                        • {sc}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sensitive Analysis Toggle */}
      {hasSensitiveIndicators && (
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--glass-bg)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <button
            type="button"
            onClick={() => setShowSensitive(!showSensitive)}
            className="w-full px-4 py-3 text-left flex items-center justify-between"
            style={{ borderBottom: showSensitive ? '1px solid var(--glass-border)' : 'none' }}
          >
            <div className="flex items-center gap-2">
              <span className="text-sm">⚠️</span>
              <h3 className="text-sm font-semibold" style={{ color: '#fca5a5' }}>Sensitive Analysis</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#fca5a5' }}>
                Private
              </span>
            </div>
            <span className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>{showSensitive ? '▲ Hide' : '▼ Show'}</span>
          </button>
          {showSensitive && (
            <div className="px-4 py-3 space-y-3">
              <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
                The following indicators are based on classical Vedic combination analysis. They reflect probabilistic tendencies, not certainties.
              </p>
              {combinations.filter(c => c.analysis_type === 'affair_indicator').map((combo, idx) => (
                <div key={idx} className="p-3 rounded-lg" style={{ background: 'rgba(239, 68, 68, 0.04)', border: '1px solid rgba(239, 68, 68, 0.15)' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold" style={{ color: '#fca5a5' }}>{combo.title}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--cosmic-text)' }}>{combo.description}</p>
                  {combo.specific_combinations.map((sc, si) => (
                    <p key={si} className="text-[10px] pl-3 mt-1" style={{ color: 'var(--cosmic-muted)', borderLeft: '2px solid rgba(239,68,68,0.2)' }}>
                      • {sc}
                    </p>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sticky Navigation ────────────────────────────────────
function StickyNav({ activeSection }: { activeSection: string }) {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav
      className="sticky top-0 z-40 py-2 px-4 overflow-x-auto"
      style={{
        background: 'rgba(13, 10, 20, 0.9)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--glass-border)',
      }}
    >
      <div className="flex gap-1 max-w-5xl mx-auto">
        {NAV_SECTIONS.map((section) => (
          <button
            key={section.id}
            type="button"
            onClick={() => scrollTo(section.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all whitespace-nowrap"
            style={{
              background: activeSection === section.id ? 'rgba(197, 168, 128, 0.15)' : 'transparent',
              color: activeSection === section.id ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
            }}
          >
            {section.icon}
            {section.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN PAGE
// ══════════════════════════════════════════════════════════
export default function ReportPage() {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [shadbalaData, setShadbalaData] = useState<ShadbalaResponse | null>(null);
  const [ashtakavargaData, setAshtakavargaData] = useState<AshtakavargaResponse | null>(null);
  const [remedyData, setRemedyData] = useState<RemedyResponse | null>(null);
  const [d9Data, setD9Data] = useState<DivisionalChartResponse | null>(null);
  const [aspectsData, setAspectsData] = useState<AspectMatrixResult | null>(null);
  const [gocharData, setGocharData] = useState<GocharTransitResult | null>(null);
  const [relationshipData, setRelationshipData] = useState<RelationshipAnalysisResult | null>(null);
  const [planetaryStates, setPlanetaryStates] = useState<Record<string, PlanetaryStateInfo> | null>(null);
  const [nakshatraData, setNakshatraData] = useState<NakshatraExchangeResult | null>(null);
  const [dailyTransits, setDailyTransits] = useState<DailyTransitAspect[] | null>(null);
  const [dashaData, setDashaData] = useState<DeepDashaResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState({
    shadbala: false,
    ashtakavarga: false,
    remedies: false,
    divisional: false,
    aspects: false,
    gochar: false,
    relationship: false,
    planetaryStates: false,
    nakshatra: false,
    dailyTransits: false,
    dasha: false,
  });
  const [apiErrors, setApiErrors] = useState({
    shadbala: null as string | null,
    ashtakavarga: null as string | null,
    remedies: null as string | null,
    divisional: null as string | null,
    aspects: null as string | null,
    gochar: null as string | null,
    relationship: null as string | null,
    planetaryStates: null as string | null,
    nakshatra: null as string | null,
    dailyTransits: null as string | null,
    dasha: null as string | null,
  });
  const [activeSection, setActiveSection] = useState('overview');
  const [fixtureId, setFixtureId] = useState<string | null>(null);

  // Load evaluation data from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('jre_last_evaluation');
      if (stored) {
        const parsed = JSON.parse(stored) as EvaluationResponse;
        if (parsed.lagna && parsed.planet_details) {
          setData(parsed);
          const storedFixture = localStorage.getItem('jre_fixture_id');
          if (storedFixture) {
            setFixtureId(storedFixture);
          }
        }
      }
    } catch {
      // ignore
    }
    setLoading(false);
  }, []);

  // Fetch all API data in parallel when data is available
  useEffect(() => {
    if (!data) return;

    const abortController = new AbortController();
    let isCancelled = false;

    const apiKey = localStorage.getItem('jre_api_key') || '';
    
    // Get birth data from localStorage (stored by evaluate page)
    let birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string } | null = null;
    try {
      const stored = localStorage.getItem('jre_birth_data');
      if (stored) birthData = JSON.parse(stored);
    } catch { /* ignore */ }

    // Also try to get from evaluation data
    if (!birthData && data.birth_data_display) {
      birthData = {
        date: data.birth_data_display.date || '',
        time: data.birth_data_display.time || '12:00:00',
        latitude: parseFloat(data.birth_data_display.latitude || '0'),
        longitude: parseFloat(data.birth_data_display.longitude || '0'),
        timezone: data.birth_data_display.timezone || 'Asia/Kolkata',
      };
    }

    if (!fixtureId && !birthData) return;

    const fetchAll = async () => {
      setApiLoading({ shadbala: true, ashtakavarga: true, remedies: true, divisional: true, aspects: true, gochar: true, relationship: true, planetaryStates: true, nakshatra: true, dailyTransits: true, dasha: true });
      setApiErrors({ shadbala: null, ashtakavarga: null, remedies: null, divisional: null, aspects: null, gochar: null, relationship: null, planetaryStates: null, nakshatra: null, dailyTransits: null, dasha: null });

      // Build API calls - use fixture_id if available, otherwise use birth data
      const shadbalaCall = fixtureId
        ? api.getShadbala(fixtureId, apiKey)
        : api.getShadbalaByBirthData(birthData!, apiKey);
      const ashtakavargaCall = fixtureId
        ? api.getAshtakavarga(fixtureId, apiKey)
        : api.getAshtakavargaByBirthData(birthData!, apiKey);
      const remediesCall = fixtureId
        ? api.getRemedies(fixtureId, apiKey)
        : api.getRemediesByBirthData(birthData!, apiKey);
      const d9Call = fixtureId
        ? api.getDivisionalChart(fixtureId, 'D9', apiKey)
        : api.getDivisionalChartByBirthData(birthData!, 'D9', apiKey);
      const aspectsCall = fixtureId
        ? api.getAspects(fixtureId, apiKey)
        : api.getAspectsByBirthData(birthData!, apiKey);
      const gocharCall = fixtureId
        ? api.getGocharTransits(fixtureId, apiKey)
        : api.getGocharTransitsByBirthData(birthData!, apiKey);
      const relationshipCall = fixtureId
        ? api.getRelationshipAnalysis(fixtureId, apiKey)
        : api.getRelationshipAnalysisByBirthData(birthData!, apiKey);
      const planetaryStatesCall = birthData
        ? api.getPlanetaryStatesByBirthData(birthData, apiKey)
        : api.getPlanetaryStates(apiKey);
      const nakshatraCall = fixtureId
        ? api.getNakshatraExchanges(fixtureId, apiKey)
        : api.getNakshatraExchangesByBirthData(birthData!, apiKey);
      const dailyTransitsCall = birthData
        ? api.getDayByDayTransitsByBirthData(birthData, 14, apiKey)
        : null;
      const dashaCall = fixtureId
        ? api.getDeepDasha(fixtureId, apiKey)
        : api.getDeepDashaByBirthData(birthData!, apiKey);

      const results = await Promise.allSettled([
        shadbalaCall,
        ashtakavargaCall,
        remediesCall,
        d9Call,
        aspectsCall,
        gocharCall,
        relationshipCall,
        planetaryStatesCall,
        nakshatraCall,
        ...(dailyTransitsCall ? [dailyTransitsCall] : []),
        dashaCall,
      ]);

      if (results[0].status === 'fulfilled') {
        setShadbalaData(results[0].value.data);
      } else if (results[0].status === 'rejected') {
        const msg = results[0].reason?.response?.data?.detail || results[0].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, shadbala: msg }));
      }

      if (results[1].status === 'fulfilled') {
        setAshtakavargaData(results[1].value.data);
      } else if (results[1].status === 'rejected') {
        const msg = results[1].reason?.response?.data?.detail || results[1].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, ashtakavarga: msg }));
      }

      if (results[2].status === 'fulfilled') {
        setRemedyData(results[2].value.data);
      } else if (results[2].status === 'rejected') {
        const msg = results[2].reason?.response?.data?.detail || results[2].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, remedies: msg }));
      }

      if (results[3].status === 'fulfilled') {
        setD9Data(results[3].value.data);
      } else if (results[3].status === 'rejected') {
        const msg = results[3].reason?.response?.data?.detail || results[3].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, divisional: msg }));
      }

      if (results[4].status === 'fulfilled') {
        setAspectsData(results[4].value.data);
      } else if (results[4].status === 'rejected') {
        const msg = results[4].reason?.response?.data?.detail || results[4].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, aspects: msg }));
      }

      if (results[5].status === 'fulfilled') {
        setGocharData(results[5].value.data);
      } else if (results[5].status === 'rejected') {
        const msg = results[5].reason?.response?.data?.detail || results[5].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, gochar: msg }));
      }

      if (results[6].status === 'fulfilled') {
        setRelationshipData(results[6].value.data);
      } else if (results[6].status === 'rejected') {
        const msg = results[6].reason?.response?.data?.detail || results[6].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, relationship: msg }));
      }

      if (results[7].status === 'fulfilled') {
        setPlanetaryStates(results[7].value.data as Record<string, PlanetaryStateInfo>);
      } else if (results[7].status === 'rejected') {
        const msg = results[7].reason?.response?.data?.detail || results[7].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, planetaryStates: msg }));
      }

      if (results[8].status === 'fulfilled') {
        setNakshatraData(results[8].value.data as NakshatraExchangeResult);
      } else if (results[8].status === 'rejected') {
        const msg = results[8].reason?.response?.data?.detail || results[8].reason?.message || 'Failed to load';
        setApiErrors((prev) => ({ ...prev, nakshatra: msg }));
      }

      const dtIdx = dailyTransitsCall ? 9 : -1;
      if (dailyTransitsCall && dtIdx >= 0 && results[dtIdx] && results[dtIdx].status === 'fulfilled') {
        setDailyTransits((results[dtIdx] as any).value.data?.daily_aspects || []);
      }

      // Dasha is always the last element (index 10)
      const dashaIdx = 10;
      if (results[dashaIdx]) {
        if (results[dashaIdx].status === 'fulfilled') {
          setDashaData((results[dashaIdx] as any).value.data as DeepDashaResult);
        } else {
          const msg = results[dashaIdx].reason?.response?.data?.detail || results[dashaIdx].reason?.message || 'Failed to load Dasha';
          setApiErrors((prev) => ({ ...prev, dasha: msg }));
        }
      }

      setApiLoading({ shadbala: false, ashtakavarga: false, remedies: false, divisional: false, aspects: false, gochar: false, relationship: false, planetaryStates: false, nakshatra: false, dailyTransits: false, dasha: false });
    };

    fetchAll();

    return () => {
      isCancelled = true;
      abortController.abort();
    };
  }, [fixtureId, data]);

  // Track active section on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-100px 0px -70% 0px' }
    );

    NAV_SECTIONS.forEach((section) => {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [data]);

  // Loading state
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12">
        <ChartSkeleton />
        <p className="text-center text-sm mt-6" style={{ color: 'var(--cosmic-muted)' }}>
          Loading comprehensive report…
        </p>
      </div>
    );
  }

  // No data state
  if (!data) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div
          className="rounded-2xl p-8 text-center"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <AlertCircle size={48} className="mx-auto mb-4 opacity-30" style={{ color: 'var(--cosmic-muted)' }} />
          <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--cosmic-text)' }}>
            No Chart Data Available
          </h2>
          <p className="text-sm mb-4" style={{ color: 'var(--cosmic-muted)' }}>
            Please run an evaluation first to generate your comprehensive report.
          </p>
          <a
            href="/evaluate"
            className="cosmic-btn inline-flex items-center gap-2 text-sm"
          >
            Go to Evaluation
            <ChevronRight size={14} />
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Sticky Navigation */}
      <StickyNav activeSection={activeSection} />

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 py-8 sm:py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-medium mb-3"
            style={{ background: 'rgba(197,168,128,0.1)', border: '1px solid rgba(197,168,128,0.2)', color: 'var(--cosmic-gold)' }}
          >
            <Star size={11} />
            Srirangam-Style Comprehensive Report
          </div>
          <h1
            className="text-2xl sm:text-3xl font-bold"
            style={{
              color: 'var(--cosmic-text)',
              fontFamily: 'var(--font-playfair), Georgia, serif',
            }}
          >
            {data.subject || 'Jatakam Report'}
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            Lagna: <strong style={{ color: 'var(--cosmic-gold)' }}>{SIGN_NAMES[data.lagna] || data.lagna}</strong>
            {' · '}Moon Nakshatra: <strong style={{ color: 'var(--cosmic-gold)' }}>{data.moon_nakshatra || '—'}</strong>
          </p>
        </motion.div>

        {/* Sections */}
        <div className="space-y-12">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <OverviewSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <ChartsSection data={data} d9Data={d9Data} d9Loading={apiLoading.divisional} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <PlanetsSection data={data} planetaryStates={planetaryStates || undefined} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
            <StrengthSection
              shadbalaData={shadbalaData}
              ashtakavargaData={ashtakavargaData}
              shadbalaLoading={apiLoading.shadbala}
              ashtakavargaLoading={apiLoading.ashtakavarga}
              shadbalaError={apiErrors.shadbala}
              ashtakavargaError={apiErrors.ashtakavarga}
            />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <DashaSection data={data} dashaData={dashaData} dashaLoading={apiLoading.dasha} dashaError={apiErrors.dasha} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <YogasSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.38 }}>
            <SectionCard id="doshas" title="Dosha Analysis" icon="⚠️">
              <DoshaAnalysis data={data} />
            </SectionCard>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <AspectsSection data={data} aspectsData={aspectsData} aspectsLoading={apiLoading.aspects} aspectsError={apiErrors.aspects} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.42 }}>
            <GocharTransitSection gocharData={gocharData} gocharLoading={apiLoading.gochar} gocharError={apiErrors.gochar} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.43 }}>
            <DailyTransitSection dailyTransits={dailyTransits} dailyTransitsLoading={apiLoading.dailyTransits} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.44 }}>
            <NakshatraSection nakshatraData={nakshatraData} nakshatraLoading={apiLoading.nakshatra} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
            <SectionCard id="predictions" title="Life Predictions" icon="🔮">
              <LifePredictions data={data} />
            </SectionCard>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.46 }}>
            <RemediesSection remedyData={remedyData} loading={apiLoading.remedies} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.48 }}>
            <NumerologySection data={data} />
          </motion.div>

          {/* Intimacy & Relationship Dynamics Section */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
            <SectionCard id="intimacy" title="Intimacy & Relationship Dynamics" icon="💕">
              <IntimacySection data={data} relationshipData={relationshipData} relationshipLoading={apiLoading.relationship} />
            </SectionCard>
          </motion.div>
        </div>

        {/* Disclaimer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 mb-8"
        >
          <div
            className="rounded-xl p-4 text-xs"
            style={{
              background: 'rgba(234, 179, 8, 0.06)',
              border: '1px solid rgba(234, 179, 8, 0.15)',
              color: 'var(--cosmic-muted)',
            }}
          >
            <p className="flex items-start gap-2">
              <span className="text-base">⚠️</span>
              <span>
                {data.disclaimer || 'These are classical Vedic computational interpretations based on Parashari and Jaimini principles. They are provided for informational and research purposes only. Consult a qualified astrologer for final guidance.'}
              </span>
            </p>
          </div>
        </motion.div>

        {/* Back to Top */}
        <div className="flex justify-center mb-8">
          <button
            type="button"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="cosmic-btn-outline flex items-center gap-2 text-xs"
          >
            <ArrowUp size={12} />
            Back to Top
          </button>
        </div>
      </div>
    </div>
  );
}
