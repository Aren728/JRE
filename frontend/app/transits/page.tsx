'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Clock, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';
import type { EvaluationResponse } from '@/lib/api';

// ── Constants ────────────────────────────────────────────
const SIGN_NAMES: Record<string, string> = {
  MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer',
  SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio',
  DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces',
};

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};

const DASHA_LORDS = [
  'KETU', 'VENUS', 'SUN', 'MOON', 'MARS', 'RAHU', 'JUPITER', 'SATURN', 'MERCURY',
];

const DASHA_YEARS: Record<string, number> = {
  KETU: 7, VENUS: 20, SUN: 6, MOON: 10, MARS: 7, RAHU: 18, JUPITER: 16, SATURN: 19, MERCURY: 17,
};

const BENEFIC_PLANETS = new Set(['JUPITER', 'VENUS', 'MOON', 'MERCURY']);
const MALEFIC_PLANETS = new Set(['SATURN', 'MARS', 'RAHU', 'KETU']);

// ── Mock Dasha data ──────────────────────────────────────
function generateMockDashas(birthYear: number) {
  const dashas: { lord: string; start: number; end: number; antardashas: { lord: string; start: number; end: number }[] }[] = [];
  let currentYear = birthYear;

  for (const lord of DASHA_LORDS) {
    const duration = DASHA_YEARS[lord];
    const start = currentYear;
    const end = currentYear + duration;
    const subDuration = duration / 9;
    const antardashas: { lord: string; start: number; end: number }[] = [];

    for (const subLord of DASHA_LORDS) {
      antardashas.push({
        lord: subLord,
        start: Math.round(currentYear * 10) / 10,
        end: Math.round((currentYear + subDuration) * 10) / 10,
      });
      currentYear += subDuration;
    }

    dashas.push({ lord, start, end, antardashas });
    currentYear = end;
  }

  return dashas;
}

// ── Mock transit data ────────────────────────────────────
const MOCK_TRANSITS = [
  { planet: 'SUN', sign: 'SIMHA', impact: 'benefic', note: 'Natural house — strong placement' },
  { planet: 'MOON', sign: 'KARKA', impact: 'benefic', note: 'Exalted sign — emotionally supportive' },
  { planet: 'MARS', sign: 'VRISHCHIKA', impact: 'malefic', note: 'Own sign — high energy, potential conflicts' },
  { planet: 'MERCURY', sign: 'KANYA', impact: 'benefic', note: 'Own sign — excellent for communication' },
  { planet: 'JUPITER', sign: 'VRISHABHA', impact: 'benefic', note: 'Friendly sign — growth and expansion' },
  { planet: 'VENUS', sign: 'TULA', impact: 'benefic', note: 'Own sign — harmony in relationships' },
  { planet: 'SATURN', sign: 'KUMBHA', impact: 'malefic', note: 'Own sign — discipline and restructuring' },
  { planet: 'RAHU', sign: 'KANYA', impact: 'malefic', note: 'Karmic lessons through service and analysis' },
  { planet: 'KETU', sign: 'MEENA', impact: 'benefic', note: 'Spiritual detachment and inner growth' },
];

// ══════════════════════════════════════════════════════════
// SECTION A: DASHA TIMELINE
// ══════════════════════════════════════════════════════════

function DashaTimeline({ dashas, currentYear }: { dashas: ReturnType<typeof generateMockDashas>; currentYear: number }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const totalSpan = dashas.length > 0 ? dashas[dashas.length - 1].end - dashas[0].start : 1;

  // Find currently active mahadasha
  const activeIdx = dashas.findIndex((d) => currentYear >= d.start && currentYear < d.end);

  const scroll = (dir: number) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir * 300, behavior: 'smooth' });
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--cosmic-muted)' }}>
          Mahadasha (Major Period)
        </h3>
        <div className="flex gap-1.5">
          <button onClick={() => scroll(-1)} className="w-7 h-7 rounded-md flex items-center justify-center transition-colors"
            style={{ background: 'rgba(197,168,128,0.08)', border: '1px solid rgba(197,168,128,0.15)', color: 'var(--cosmic-muted)' }}>
            <ChevronLeft size={14} />
          </button>
          <button onClick={() => scroll(1)} className="w-7 h-7 rounded-md flex items-center justify-center transition-colors"
            style={{ background: 'rgba(197,168,128,0.08)', border: '1px solid rgba(197,168,128,0.15)', color: 'var(--cosmic-muted)' }}>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Scrollable timeline */}
      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto pb-3 snap-x snap-mandatory"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(197,168,128,0.3) transparent' }}
      >
        {dashas.map((d, i) => {
          const isActive = i === activeIdx;
          const widthPct = ((d.end - d.start) / totalSpan) * 100;
          return (
            <motion.div
              key={d.lord}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="snap-start shrink-0 rounded-xl p-3 transition-all duration-300"
              style={{
                minWidth: `${Math.max(widthPct * 3, 120)}px`,
                background: isActive ? 'rgba(197,168,128,0.1)' : 'var(--glass-bg)',
                border: isActive ? '2px solid var(--cosmic-gold)' : '1px solid var(--glass-border)',
                boxShadow: isActive ? '0 0 20px rgba(197,168,128,0.2)' : 'none',
              }}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-base">{PLANET_SYMBOLS[d.lord]}</span>
                <span className="text-xs font-bold" style={{ color: isActive ? 'var(--cosmic-gold)' : 'var(--cosmic-text)' }}>
                  {d.lord}
                </span>
                {isActive && (
                  <span className="ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded"
                    style={{ background: 'rgba(197,168,128,0.2)', color: 'var(--cosmic-gold)' }}>
                    ACTIVE
                  </span>
                )}
              </div>
              <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
                {Math.floor(d.start)}–{Math.floor(d.end)}
              </p>
              <p className="text-[9px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                {DASHA_YEARS[d.lord]} years
              </p>

              {/* Mini antardasha bar */}
              <div className="mt-2 flex gap-px rounded overflow-hidden" style={{ height: '4px' }}>
                {d.antardashas.map((ad, j) => {
                  const w = ((ad.end - ad.start) / (d.end - d.start)) * 100;
                  const adActive = currentYear >= ad.start && currentYear < ad.end;
                  return (
                    <div
                      key={j}
                      style={{
                        width: `${w}%`,
                        background: adActive ? 'var(--cosmic-gold)' : 'rgba(197,168,128,0.15)',
                        borderRadius: j === d.antardashas.length - 1 ? '0 2px 2px 0' : 0,
                      }}
                    />
                  );
                })}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// SECTION B: CURRENT TRANSITS
// ══════════════════════════════════════════════════════════

function CurrentTransits({ transits }: { transits: typeof MOCK_TRANSITS }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--cosmic-muted)' }}>
        Current Planetary Transits
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {transits.map((t, i) => {
          const isBenefic = t.impact === 'benefic';
          return (
            <motion.div
              key={t.planet}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-xl p-3.5"
              style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
              }}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-lg">{PLANET_SYMBOLS[t.planet]}</span>
                <span className="text-sm font-semibold" style={{ color: 'var(--cosmic-text)' }}>{t.planet}</span>
                <span
                  className="ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded"
                  style={{
                    background: isBenefic ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                    color: isBenefic ? '#34d399' : '#f87171',
                  }}
                >
                  {isBenefic ? '🟢 Benefic' : '🔴 Malefic'}
                </span>
              </div>
              <p className="text-xs mb-1" style={{ color: 'var(--cosmic-text)' }}>
                in <strong>{SIGN_NAMES[t.sign] || t.sign}</strong>
              </p>
              <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
                {t.note}
              </p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN PAGE
// ══════════════════════════════════════════════════════════

const MOCK_EVAL: EvaluationResponse = {
  evaluation_id: 'mock-transits', subject: 'Demo Subject', lagna: 'VRISHABHA',
  moon_nakshatra: 'ROHINI', yogas: [], yoga_count: 0, formed_count: 0,
  processing_time_ms: 0, engine_version: '1.0.0-beta', disclaimer: '',
  lagna_confidence: 'HIGH', unknown_tob: false, skipped_yogas: [],
  elemental_balance: {}, modality_balance: {}, dignity_map: {}, aspect_matrix: [],
  planet_details: {
    SUN: { sign: 'MESHA', element: 'fire', modality: 'cardinal', dignity: 'Friendly', degree_in_sign: 15.3 },
    MOON: { sign: 'VRISHABHA', element: 'earth', modality: 'fixed', dignity: 'Friendly', degree_in_sign: 8.7 },
  },
  birth_data_display: { date: '1990-05-15', time: '10:30', timezone: 'IST', latitude: '28.61', longitude: '77.21', lagna: 'VRISHABHA', moon_nakshatra: 'ROHINI' },
  parivartana_yogas: [],
  parivartana_synthesis: {},
  deep_dasha: {
    md: { lord: 'MOON', level: 'MD', start_utc: '1990-05-15T00:00:00', end_utc: '2000-05-15T00:00:00', duration_years: 10, fraction_of_parent: 0 },
    ad: { lord: 'MARS', level: 'AD', start_utc: '1990-05-15T00:00:00', end_utc: '1992-04-01T00:00:00', duration_years: 1.94, fraction_of_parent: 0.07 },
    pd: { lord: 'RAHU', level: 'PD', start_utc: '1990-05-15T00:00:00', end_utc: '1990-11-20T00:00:00', duration_years: 0.55, fraction_of_parent: 0.1 },
    sd: { lord: 'JUPITER', start_utc: '1990-05-15T00:00:00', end_utc: '1990-06-20T00:00:00', duration_years: 0.13, parent_pd_lord: 'RAHU', parent_md_lord: 'MOON' },
    ad_timeline: [],
    pd_timeline: [],
    sd_timeline: [],
    activation_multiplier: 1.5,
  },
  aspect_matrix_full: [],
};

export default function TransitsPage() {
  const [data, setData] = useState<EvaluationResponse>(MOCK_EVAL);
  const [source, setSource] = useState<'live' | 'mock'>('mock');
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    try {
      const stored = localStorage.getItem('jre_last_evaluation');
      if (stored) {
        const parsed = JSON.parse(stored) as EvaluationResponse;
        if (parsed.lagna) { setData(parsed); setSource('live'); return; }
      }
    } catch { /* ignore */ }
    setData(MOCK_EVAL);
    setSource('mock');
  }, []);

  const birthYear = parseInt(data.birth_data_display?.date?.split('-')[0] || '1990', 10);
  const dashas = generateMockDashas(birthYear);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-medium mb-3"
          style={{ background: 'rgba(197,168,128,0.1)', border: '1px solid rgba(197,168,128,0.2)', color: 'var(--cosmic-gold)' }}>
          <Clock size={11} />
          Predictive Timelines
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold"
          style={{ color: 'var(--cosmic-text)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
          Transits & Dasha
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
          Vimshottari Dasha periods and current planetary transits for{' '}
          <strong style={{ color: 'var(--cosmic-gold)' }}>{data.subject}</strong>
        </p>
      </motion.div>

      {/* Mock banner */}
      {source === 'mock' && (
        <div className="mb-6 p-3 rounded-xl flex items-start gap-2.5 text-xs"
          style={{ background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.2)', color: 'var(--cosmic-muted)' }}>
          <AlertCircle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
          <p>Showing <strong style={{ color: 'var(--cosmic-gold)' }}>demo data</strong>.{' '}
            Run an evaluation from <a href="/evaluate" style={{ color: 'var(--cosmic-gold)', textDecoration: 'underline' }}>Evaluate</a> for live data.</p>
        </div>
      )}

      <div className="space-y-10">
        {/* Section A: Dasha Timeline */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <div className="flex items-center gap-2.5 mb-5">
            <span className="text-xl">⏳</span>
            <h2 className="text-lg font-bold" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
              Vimshottari Dasha Timeline
            </h2>
            <div className="flex-1 h-px ml-2" style={{ background: 'linear-gradient(90deg, var(--glass-border), transparent)' }} />
          </div>
          <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <DashaTimeline dashas={dashas} currentYear={currentYear} />
            <p className="text-[10px] mt-3" style={{ color: 'var(--cosmic-muted)' }}>
              Birth year: {birthYear} · Current year: {currentYear} · Active Mahadasha:{' '}
              <strong style={{ color: 'var(--cosmic-gold)' }}>
                {dashas[activeIdx(dashas, currentYear)]?.lord || '—'}
              </strong>
            </p>
          </div>
        </motion.section>

        {/* Section B: Current Transits */}
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <div className="flex items-center gap-2.5 mb-5">
            <span className="text-xl">🌍</span>
            <h2 className="text-lg font-bold" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
              Current Transits
            </h2>
            <div className="flex-1 h-px ml-2" style={{ background: 'linear-gradient(90deg, var(--glass-border), transparent)' }} />
          </div>
          <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <CurrentTransits transits={MOCK_TRANSITS} />
          </div>
        </motion.section>
      </div>
    </div>
  );
}

function activeIdx(dashas: ReturnType<typeof generateMockDashas>, year: number): number {
  return dashas.findIndex((d) => year >= d.start && year < d.end);
}
