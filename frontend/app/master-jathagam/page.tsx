'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Star, LayoutGrid, Globe, Zap, BookOpen, Gem,
  ChevronRight, AlertCircle, ArrowUp
} from 'lucide-react';
import NorthIndianChart from '@/components/NorthIndianChart';
import PlanetaryTable from '@/components/PlanetaryTable';
import ShadbalaTable from '@/components/ShadbalaTable';
import AshtakavargaTable from '@/components/AshtakavargaTable';
import RemediesPanel from '@/components/RemediesPanel';
import NumerologyPanel from '@/components/NumerologyPanel';
import { ChartSkeleton } from '@/components/LoadingSkeleton';
import { api } from '@/lib/api';
import type {
  EvaluationResponse,
  ShadbalaResponse,
  AshtakavargaResponse,
  RemedyResponse,
  NumerologyResponse,
} from '@/lib/api';
import YogaInspector from '@/components/yogas/YogaInspector';
import type { YogaEvaluation } from '@/components/yogas/YogaInspector';

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
  { id: 'aspects', label: 'Aspects', icon: <Globe size={14} /> },
  { id: 'remedies', label: 'Remedies', icon: <Gem size={14} /> },
  { id: 'numerology', label: 'Numerology', icon: <Star size={14} /> },
];

// ── Planet Symbols ───────────────────────────────────────
const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};

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

// ── Overview Section ─────────────────────────────────────
function OverviewSection({ data }: { data: EvaluationResponse }) {
  const birth = data.birth_data_display;
  return (
    <SectionCard id="overview" title="Overview & Birth Details" icon="🕉️">
      <div
        className="rounded-2xl p-5"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Subject</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{data.subject}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Lagna (Ascendant)</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-gold)' }}>{data.lagna}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Moon Nakshatra</p>
            <p className="text-sm font-medium" style={{ color: 'var(--cosmic-text)' }}>{data.moon_nakshatra}</p>
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
              <div className="flex gap-2">
                {Object.entries(data.elemental_balance || {}).map(([element, count]) => (
                  <div key={element} className="text-center">
                    <div className="text-sm font-bold" style={{ color: 'var(--cosmic-text)' }}>{count}</div>
                    <div className="text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>{element}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: 'var(--cosmic-muted)' }}>Modality Balance</p>
              <div className="flex gap-2">
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
    </SectionCard>
  );
}

// ── Charts Section ───────────────────────────────────────
function ChartsSection({ data }: { data: EvaluationResponse }) {
  return (
    <SectionCard id="charts" title="Visual Charts" icon="📊">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* D1 Chart */}
        <div
          className="rounded-2xl p-4"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--glass-border)',
          }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--cosmic-gold)' }}>
            Rashi Chart (D-1)
          </h3>
          <NorthIndianChart
            lagna={data.lagna}
            planetDetails={data.planet_details}
            divisionalType="D1"
          />
        </div>

        {/* D9 Chart */}
        <div
          className="rounded-2xl p-4"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--glass-border)',
          }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--cosmic-gold)' }}>
            Navamsha Chart (D-9)
          </h3>
          <NorthIndianChart
            lagna={data.lagna}
            planetDetails={data.planet_details}
            divisionalType="D9"
          />
        </div>
      </div>
    </SectionCard>
  );
}

// ── Planets Section ──────────────────────────────────────
function PlanetsSection({ data }: { data: EvaluationResponse }) {
  return (
    <SectionCard id="planets" title="Planetary Positions" icon="🪐">
      <PlanetaryTable
        lagna={data.lagna}
        planetDetails={data.planet_details}
        dignityMap={data.dignity_map}
      />
    </SectionCard>
  );
}

// ── Strength Section ─────────────────────────────────────
function StrengthSection({
  shadbalaData,
  ashtakavargaData,
  shadbalaLoading,
  ashtakavargaLoading,
}: {
  shadbalaData: ShadbalaResponse | null;
  ashtakavargaData: AshtakavargaResponse | null;
  shadbalaLoading: boolean;
  ashtakavargaLoading: boolean;
}) {
  return (
    <SectionCard id="strength" title="Strength & Ashtakavarga" icon="💪">
      <div className="space-y-6">
        <ShadbalaTable data={shadbalaData} loading={shadbalaLoading} />
        <AshtakavargaTable data={ashtakavargaData} loading={ashtakavargaLoading} />
      </div>
    </SectionCard>
  );
}

// ── Dasha Section ────────────────────────────────────────
function DashaSection({ data }: { data: EvaluationResponse }) {
  const dasha = data.deep_dasha;
  if (!dasha?.md) {
    return (
      <SectionCard id="dasha" title="Vimshottari Dasha" icon="⏳">
        <div
          className="rounded-2xl p-6 text-center"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <p style={{ color: 'var(--cosmic-muted)' }}>Dasha data not available.</p>
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
                {level.data.lord}
              </div>
              <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
                {level.data.duration_years?.toFixed(1)}y
              </div>
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

// ── Yogas Section (using YogaInspector) ────────────────────────────────
function YogasSection({ data }: { data: EvaluationResponse }) {
  // Convert EvaluationResponse.yogas to YogaEvaluation format
  const yogaEvaluations: YogaEvaluation[] = (data.yogas || []).map((yoga: any, idx: number) => ({
    id: yoga.yoga_name?.toLowerCase().replace(/\s+/g, '_') || `yoga-${idx}`,
    name: yoga.yoga_name || yoga.name || 'Unknown Yoga',
    category: (yoga.category as YogaEvaluation['category']) || 'NABHASA',
    description: yoga.description || yoga.provenance?.formation_evidence || 'Classical yoga formation.',
    participatingPlanets: yoga.involved_planets || [],
    status: (() => {
      if (yoga.status === 'CANCELLED') return 'AFFLICTED';
      if (yoga.status === 'WEAKENED') return 'DORMANT';
      if (yoga.dasha_activation?.present?.length) return 'ACTIVE_DASHA';
      if (yoga.dasha_activation?.future?.length) return 'ACTIVE_TRANSIT';
      return 'DORMANT';
    })(),
    strengthScore: yoga.static_strength ? yoga.static_strength / 1.0 : 1.0,
    activatingLord: yoga.dasha_activation?.present?.[0]?.lord ? `${yoga.dasha_activation.present[0].lord} (MD)` : undefined,
    houseCombination: yoga.involved_planets?.length ?
      yoga.involved_planets.slice(0, 2).join(' & ') + ' combination' :
      'Single planet configuration',
    ruleConditions: [
      { conditionText: 'Yoga formed by classical rules', isMet: yoga.status === 'FORMED' },
      { conditionText: 'Static strength ≥ 1.0', isMet: yoga.static_strength ? yoga.static_strength >= 1.0 : true },
      { conditionText: 'Dynamic strength > 0', isMet: yoga.dynamic_strength !== null && yoga.dynamic_strength !== undefined && yoga.dynamic_strength > 0 },
      { conditionText: 'No cancellation reason', isMet: !yoga.cancellation_reason },
    ],
  }));

  // Get active dasha lords from deep_dasha
  const activeDashaLords: string[] = [];
  if (data.deep_dasha?.md) activeDashaLords.push(data.deep_dasha.md.lord);
  if (data.deep_dasha?.ad) activeDashaLords.push(data.deep_dasha.ad.lord);
  if (data.deep_dasha?.pd) activeDashaLords.push(data.deep_dasha.pd.lord);

  return (
    <SectionCard id="yogas" title="Yoga Inspector" icon="🕉️">
      {yogaEvaluations.length > 0 ? (
        <YogaInspector
          yogas={yogaEvaluations}
          activeDashaLords={activeDashaLords}
          minStrengthCutoff={0.5}
          onSelectYoga={() => {}}
        />
      ) : (
        <div
          className="rounded-2xl p-6 text-center"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <p style={{ color: 'var(--cosmic-muted)' }}>No yogas evaluated yet.</p>
        </div>
      )}
    </SectionCard>
  );
}

// ── Aspects Section ──────────────────────────────────────
function AspectsSection({ data }: { data: EvaluationResponse }) {
  const aspects = data.aspect_matrix_full || data.aspect_matrix || [];

  return (
    <SectionCard id="aspects" title="Aspect Matrix (Drishti)" icon="🔭">
      <div
        className="rounded-2xl p-5"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        {aspects.length > 0 ? (
          <div className="space-y-2">
            {aspects.slice(0, 15).map((asp: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg"
                style={{ background: 'rgba(26, 20, 35, 0.3)' }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">{PLANET_SYMBOLS[asp.aspecter || asp.source] || ''}</span>
                  <span className="text-xs font-medium" style={{ color: 'var(--cosmic-text)' }}>
                    {asp.aspecter || asp.source}
                  </span>
                  <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
                    {asp.aspect_type || 'aspect'}
                  </span>
                  <span className="text-sm">{PLANET_SYMBOLS[asp.aspected || asp.target] || ''}</span>
                  <span className="text-xs font-medium" style={{ color: 'var(--cosmic-text)' }}>
                    {asp.aspected || asp.target}
                  </span>
                </div>
                {asp.orb_degrees !== undefined && (
                  <span className="text-[10px] font-mono" style={{ color: 'var(--cosmic-muted)' }}>
                    {asp.orb_degrees.toFixed(1)}°
                  </span>
                )}
              </div>
            ))}
            {aspects.length > 15 && (
              <p className="text-[10px] text-center" style={{ color: 'var(--cosmic-muted)' }}>
                + {aspects.length - 15} more aspects
              </p>
            )}
          </div>
        ) : (
          <p className="text-xs text-center py-4" style={{ color: 'var(--cosmic-muted)' }}>
            No aspect data available.
          </p>
        )}
      </div>
    </SectionCard>
  );
}

// ── Remedies Section ─────────────────────────────────────
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

// ── Numerology Section ───────────────────────────────────
function NumerologySection({
  data,
  numerologyData,
  loading,
}: {
  data: EvaluationResponse;
  numerologyData: NumerologyResponse | null;
  loading: boolean;
}) {
  // Use birth date and subject name from evaluation
  const birthDate = data.birth_data_display?.date || '';
  const name = data.subject || '';

  return (
    <SectionCard id="numerology" title="Numerology" icon="🔢">
      <NumerologyPanel
        data={numerologyData}
        loading={loading}
        showInput={!numerologyData && !birthDate}
      />
    </SectionCard>
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

export default function MasterJathagamPage() {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [shadbalaData, setShadbalaData] = useState<ShadbalaResponse | null>(null);
  const [ashtakavargaData, setAshtakavargaData] = useState<AshtakavargaResponse | null>(null);
  const [remedyData, setRemedyData] = useState<RemedyResponse | null>(null);
  const [numerologyData, setNumerologyData] = useState<NumerologyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState({
    shadbala: false,
    ashtakavarga: false,
    remedies: false,
    numerology: false,
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

  // Fetch all API data in parallel when fixtureId is available
  useEffect(() => {
    if (!fixtureId) return;

    const apiKey = localStorage.getItem('jre_api_key') || '';

    const fetchAll = async () => {
      setApiLoading({ shadbala: true, ashtakavarga: true, remedies: true, numerology: true });

      const results = await Promise.allSettled([
        api.getShadbala(fixtureId, apiKey),
        api.getAshtakavarga(fixtureId, apiKey),
        api.getRemedies(fixtureId, apiKey),
      ]);

      if (results[0].status === 'fulfilled') setShadbalaData(results[0].value.data);
      if (results[1].status === 'fulfilled') setAshtakavargaData(results[1].value.data);
      if (results[2].status === 'fulfilled') setRemedyData(results[2].value.data);

      // Fetch numerology if we have birth date
      if (data?.birth_data_display?.date && data?.subject) {
        try {
          const numResponse = await api.calculateNumerology(
            { birth_date: data.birth_data_display.date, full_name: data.subject },
            apiKey
          );
          setNumerologyData(numResponse.data);
        } catch {
          // Numerology is optional
        }
      }

      setApiLoading({ shadbala: false, ashtakavarga: false, remedies: false, numerology: false });
    };

    fetchAll();
  }, [fixtureId, data?.birth_data_display?.date, data?.subject]);

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
          Loading Master Jathagam…
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
            Please run an evaluation first to generate your Master Jathagam.
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
          <h1
            className="text-2xl sm:text-3xl font-bold"
            style={{
              color: 'var(--cosmic-text)',
              fontFamily: 'var(--font-playfair), Georgia, serif',
            }}
          >
            Master Jathagam
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            Comprehensive Vedic Astrological Reading · {data.subject}
          </p>
        </motion.div>

        {/* Sections */}
        <div className="space-y-12">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <OverviewSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <ChartsSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <PlanetsSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
            <StrengthSection
              shadbalaData={shadbalaData}
              ashtakavargaData={ashtakavargaData}
              shadbalaLoading={apiLoading.shadbala}
              ashtakavargaLoading={apiLoading.ashtakavarga}
            />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <DashaSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <YogasSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <AspectsSection data={data} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
            <RemediesSection remedyData={remedyData} loading={apiLoading.remedies} />
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
            <NumerologySection data={data} numerologyData={numerologyData} loading={apiLoading.numerology} />
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
                These are classical Vedic computational interpretations based on Parashari and Jaimini principles.
                They are provided for informational and research purposes only.
                Consult a qualified astrologer for final guidance and before making any significant life decisions.
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
