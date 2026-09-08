'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LayoutGrid, Square, AlertCircle, ChevronDown, Star, Zap, Globe, BookOpen, Gem } from 'lucide-react';
import NorthIndianChart from '@/components/NorthIndianChart';
import PlanetaryTable from '@/components/PlanetaryTable';
import ShadbalaTable from '@/components/ShadbalaTable';
import AshtakavargaTable from '@/components/AshtakavargaTable';
import DivisionalChartViewer from '@/components/DivisionalChartViewer';
import RemediesPanel from '@/components/RemediesPanel';
import { ChartSkeleton } from '@/components/LoadingSkeleton';
import { api } from '@/lib/api';
import type { EvaluationResponse, ShadbalaResponse, AshtakavargaResponse, RemedyResponse } from '@/lib/api';

// ── Mock data for testing when no evaluation exists ──────
const MOCK_DATA: EvaluationResponse = {
  evaluation_id: 'mock-001',
  subject: 'Demo Chart',
  lagna: 'VRISHABHA',
  moon_nakshatra: 'ROHINI',
  yogas: [],
  yoga_count: 0,
  formed_count: 0,
  processing_time_ms: 0,
  engine_version: '1.0.0-beta',
  disclaimer: 'Demo data for UI testing.',
  lagna_confidence: 'HIGH',
  unknown_tob: false,
  skipped_yogas: [],
  elemental_balance: { fire: 2, earth: 3, air: 2, water: 2 },
  modality_balance: { cardinal: 3, fixed: 4, mutable: 2 },
  dignity_map: {
    SUN: 'Enemy', MOON: 'Friendly', MARS: 'Debilitated',
    MERCURY: 'Own Sign', JUPITER: 'Neutral', VENUS: 'Exalted',
    SATURN: 'Friendly', RAHU: 'Neutral', KETU: 'Neutral',
  },
  aspect_matrix: [],
  planet_details: {
    SUN: { sign: 'MESHA', element: 'fire', modality: 'cardinal', dignity: 'Enemy', degree_in_sign: 15.3 },
    MOON: { sign: 'VRISHABHA', element: 'earth', modality: 'fixed', dignity: 'Friendly', degree_in_sign: 8.7 },
    MARS: { sign: 'KARKA', element: 'water', modality: 'cardinal', dignity: 'Debilitated', degree_in_sign: 12.1 },
    MERCURY: { sign: 'KANYA', element: 'earth', modality: 'mutable', dignity: 'Own Sign', degree_in_sign: 18.6 },
    JUPITER: { sign: 'VRISHABHA', element: 'earth', modality: 'fixed', dignity: 'Neutral', degree_in_sign: 5.0 },
    VENUS: { sign: 'MEENA', element: 'water', modality: 'mutable', dignity: 'Exalted', degree_in_sign: 22.4 },
    SATURN: { sign: 'TULA', element: 'air', modality: 'cardinal', dignity: 'Friendly', degree_in_sign: 10.9 },
    RAHU: { sign: 'KANYA', element: 'earth', modality: 'mutable', dignity: 'Neutral', degree_in_sign: 14.2 },
    KETU: { sign: 'MEENA', element: 'water', modality: 'mutable', dignity: 'Neutral', degree_in_sign: 14.2 },
  },
  birth_data_display: {
    date: '1990-05-15',
    time: '10:30',
    timezone: 'Asia/Kolkata',
    latitude: '28.6139',
    longitude: '77.2090',
    lagna: 'VRISHABHA',
    moon_nakshatra: 'ROHINI',
  },
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

// ── Divisional Chart Types ──────────────────────────────
const DIVISIONAL_CHARTS = [
  { key: 'D1', label: 'Rashi (D-1)', description: 'Main birth chart' },
  { key: 'D9', label: 'Navamsha (D-9)', description: 'Marriage & dharma' },
  { key: 'D2', label: 'Hora (D-2)', description: 'Wealth & prosperity' },
  { key: 'D3', label: 'Drekkana (D-3)', description: 'Siblings & courage' },
  { key: 'D4', label: 'Chaturthamsha (D-4)', description: 'Property & fortune' },
  { key: 'D7', label: 'Saptamamsha (D-7)', description: 'Children & creativity' },
  { key: 'D10', label: 'Dashamamsha (D-10)', description: 'Career & profession' },
  { key: 'D12', label: 'Dwadashamsha (D-12)', description: 'Parents & ancestry' },
  { key: 'D16', label: 'Shodashamsha (D-16)', description: 'Vehicles & comforts' },
  { key: 'D24', label: 'Chaturvimshamsha (D-24)', description: 'Education & knowledge' },
  { key: 'D27', label: 'Bhamsha (D-27)', description: 'Strengths & weaknesses' },
  { key: 'D30', label: 'Trishamsha (D-30)', description: 'Evil & misfortune' },
  { key: 'D40', label: 'Chaturashitamsha (D-40)', description: 'Mother\'s lineage' },
  { key: 'D45', label: 'Khavedamsha (D-45)', description: 'Auspiciousness' },
  { key: 'D60', label: 'Shashtiamsha (D-60)', description: 'Past life karma' },
];

// ── Tab Types ────────────────────────────────────────────
type TabKey = 'birth_chart' | 'divisional' | 'shadbala' | 'ashtakavarga' | 'yogas' | 'transits' | 'remedies';

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'birth_chart', label: 'Birth Chart', icon: <Star size={14} /> },
  { key: 'divisional', label: 'Divisional', icon: <LayoutGrid size={14} /> },
  { key: 'shadbala', label: 'Shadbala', icon: <Zap size={14} /> },
  { key: 'ashtakavarga', label: 'Ashtakavarga', icon: <Square size={14} /> },
  { key: 'yogas', label: 'Yogas', icon: <BookOpen size={14} /> },
  { key: 'transits', label: 'Transits', icon: <Globe size={14} /> },
  { key: 'remedies', label: 'Remedies', icon: <Gem size={14} /> },
];

// ── View Toggle Component ────────────────────────────────
function ViewToggle({
  active,
  onChange,
}: {
  active: 'north' | 'south';
  onChange: (v: 'north' | 'south') => void;
}) {
  return (
    <div
      className="inline-flex rounded-lg overflow-hidden"
      style={{
        background: 'var(--glass-bg)',
        border: '1px solid var(--glass-border)',
      }}
    >
      <button
        type="button"
        onClick={() => onChange('north')}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-200"
        style={{
          background: active === 'north' ? 'rgba(197, 168, 128, 0.15)' : 'transparent',
          color: active === 'north' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
          borderRight: '1px solid var(--glass-border)',
        }}
      >
        <LayoutGrid size={13} />
        North Indian
      </button>
      <button
        type="button"
        onClick={() => onChange('south')}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-200"
        style={{
          background: active === 'south' ? 'rgba(197, 168, 128, 0.15)' : 'transparent',
          color: active === 'south' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
        }}
      >
        <Square size={13} />
        South Indian
      </button>
    </div>
  );
}

// ── Divisional Chart Selector ────────────────────────────
function DivisionalChartSelector({
  selected,
  onChange,
}: {
  selected: string;
  onChange: (key: string) => void;
}) {
  return (
    <div className="relative">
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none w-full px-4 py-2 pr-8 text-sm font-medium rounded-lg cursor-pointer transition-all"
        style={{
          background: 'var(--glass-bg)',
          border: '1px solid var(--glass-border)',
          color: 'var(--cosmic-text)',
          backdropFilter: 'blur(16px)',
        }}
      >
        {DIVISIONAL_CHARTS.map((dc) => (
          <option key={dc.key} value={dc.key}>
            {dc.label} — {dc.description}
          </option>
        ))}
      </select>
      <ChevronDown
        size={14}
        className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
        style={{ color: 'var(--cosmic-muted)' }}
      />
    </div>
  );
}

// ── Tab Bar Component ────────────────────────────────────
function TabBar({
  active,
  onChange,
}: {
  active: TabKey;
  onChange: (tab: TabKey) => void;
}) {
  return (
    <div
      className="flex gap-1 p-1 rounded-xl overflow-x-auto"
      style={{
        background: 'var(--glass-bg)',
        border: '1px solid var(--glass-border)',
      }}
    >
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition-all duration-200 whitespace-nowrap"
          style={{
            background: active === tab.key ? 'rgba(197, 168, 128, 0.15)' : 'transparent',
            color: active === tab.key ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
          }}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// ── Shadbala Tab (with API data) ──────────────────────
function ShadbalaTab({ fixtureId }: { fixtureId?: string }) {
  const [shadbalaData, setShadbalaData] = useState<ShadbalaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fixtureId) return;

    const fetchShadbala = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiKey = localStorage.getItem('jre_api_key') || '';
        const response = await api.getShadbala(fixtureId, apiKey);
        setShadbalaData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load Shadbala data');
      } finally {
        setLoading(false);
      }
    };

    fetchShadbala();
  }, [fixtureId]);

  return <ShadbalaTable data={shadbalaData} loading={loading} error={error} />;
}

// ── Ashtakavarga Tab (with API data) ────────────────────
function AshtakavargaTab({ fixtureId }: { fixtureId?: string }) {
  const [avData, setAvData] = useState<AshtakavargaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fixtureId) return;

    const fetchAshtakavarga = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiKey = localStorage.getItem('jre_api_key') || '';
        const response = await api.getAshtakavarga(fixtureId, apiKey);
        setAvData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load Ashtakavarga data');
      } finally {
        setLoading(false);
      }
    };

    fetchAshtakavarga();
  }, [fixtureId]);

  return <AshtakavargaTable data={avData} loading={loading} error={error} />;
}

// ── Divisional Tab (with API data) ──────────────────────
function DivisionalTab({ fixtureId }: { fixtureId?: string }) {
  return <DivisionalChartViewer fixtureId={fixtureId} initialDivision="D9" />;
}

// ── Remedies Tab (with API data) ────────────────────────
function RemediesApiTab({ fixtureId }: { fixtureId?: string }) {
  const [remedyData, setRemedyData] = useState<RemedyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fixtureId) return;

    const fetchRemedies = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiKey = localStorage.getItem('jre_api_key') || '';
        const response = await api.getRemedies(fixtureId, apiKey);
        setRemedyData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load remedies data');
      } finally {
        setLoading(false);
      }
    };

    fetchRemedies();
  }, [fixtureId]);

  return <RemediesPanel data={remedyData} loading={loading} error={error} />;
}

// ── Yogas Tab ────────────────────────────────────────────
function YogasTab({ data }: { data: EvaluationResponse }) {
  const yogas = data.yogas || [];
  const parivartanas = data.parivartana_yogas || [];

  const hasAny = yogas.length > 0 || parivartanas.length > 0;
  if (!hasAny) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{
          background: 'var(--glass-bg)',
          border: '1px solid var(--glass-border)',
        }}
      >
        <BookOpen size={32} className="mx-auto mb-3 opacity-30" style={{ color: 'var(--cosmic-muted)' }} />
        <p style={{ color: 'var(--cosmic-muted)' }}>No yogas evaluated yet.</p>
        <p className="text-xs mt-1" style={{ color: 'var(--cosmic-muted)' }}>
          Run an evaluation to see yoga analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Classical Yogas */}
      {yogas.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
            Classical Yogas ({yogas.length})
          </h4>
          <div className="space-y-3">
            {yogas.map((yoga: any, idx: number) => {
              const status = yoga.status || 'FORMED';
              const statusColor =
                status === 'FORMED'
                  ? 'var(--benefic-green)'
                  : status === 'CANCELLED'
                  ? 'var(--malefic-red)'
                  : '#eab308';
              const borderColor =
                status === 'FORMED'
                  ? 'rgba(16, 185, 129, 0.3)'
                  : status === 'CANCELLED'
                  ? 'rgba(239, 68, 68, 0.3)'
                  : 'rgba(234, 179, 8, 0.3)';

              return (
                <div
                  key={idx}
                  className="rounded-xl p-4"
                  style={{
                    background: 'var(--glass-bg)',
                    border: `1px solid ${borderColor}`,
                    backdropFilter: 'blur(16px)',
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm" style={{ color: 'var(--cosmic-text)' }}>
                      {yoga.yoga_name || yoga.name}
                    </h4>
                    <span
                      className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                      style={{
                        background: `${statusColor}20`,
                        color: statusColor,
                      }}
                    >
                      {status}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
                    {yoga.description || yoga.narrative || 'Classical yoga formation.'}
                  </p>
                  {yoga.dynamic_strength !== undefined && yoga.dynamic_strength !== null && (
                    <p className="text-[10px] mt-2 font-mono" style={{ color: 'var(--cosmic-muted)' }}>
                      Strength: {yoga.dynamic_strength.toFixed(4)}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Parivartana Yogas (Mutual Exchange) */}
      {parivartanas.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
            Parivartana Yogas ({parivartanas.length})
          </h4>
          <div className="space-y-3">
            {parivartanas.map((pv: any, idx: number) => {
              const typeColors: Record<string, string> = {
                MAHA: 'var(--benefic-green)',
                KHALA: '#eab308',
                DAINYA: 'var(--malefic-red)',
                ORDINARY: 'var(--cosmic-muted)',
              };
              const color = typeColors[pv.exchange_type] || 'var(--cosmic-muted)';

              return (
                <div
                  key={`pv-${idx}`}
                  className="rounded-xl p-4"
                  style={{
                    background: 'var(--glass-bg)',
                    border: `1px solid ${color}30`,
                    backdropFilter: 'blur(16px)',
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm" style={{ color: 'var(--cosmic-text)' }}>
                      {pv.planet_a} ↔ {pv.planet_b}
                    </h4>
                    <span
                      className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                      style={{ background: `${color}20`, color }}
                    >
                      {pv.exchange_type}
                    </span>
                  </div>
                  <p className="text-xs mb-1" style={{ color: 'var(--cosmic-muted)' }}>
                    {pv.planet_a} in {pv.sign_a} (House {pv.house_a}) ↔ {pv.planet_b} in {pv.sign_b} (House {pv.house_b})
                  </p>
                  <p className="text-xs" style={{ color: 'var(--cosmic-text)' }}>
                    {pv.narrative}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
                    <span>Strength: {pv.strength.toFixed(2)}</span>
                    {pv.neecha_bhanga && <span className="text-green-400">✦ Neecha-bhanga</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Transits Tab ─────────────────────────────────────────
function TransitsTab({ data }: { data: EvaluationResponse }) {
  const planets = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU'];
  const emojis: Record<string, string> = {
    SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
    JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
  };

  const deepDasha = data.deep_dasha;
  const hasDasha = deepDasha && deepDasha.md;

  return (
    <div className="space-y-4">
      {/* Current Planetary Positions */}
      <div
        className="rounded-2xl p-5"
        style={{
          background: 'var(--glass-bg)',
          border: '1px solid var(--glass-border)',
          backdropFilter: 'blur(16px)',
        }}
      >
        <h3
          className="text-lg font-bold mb-4"
          style={{
            color: 'var(--cosmic-gold)',
            fontFamily: 'var(--font-playfair), Georgia, serif',
          }}
        >
          Current Planetary Positions
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {planets.map((planet) => {
            const detail = data.planet_details?.[planet];
            return (
              <div
                key={planet}
                className="rounded-xl p-3 text-center"
                style={{
                  background: 'rgba(26, 20, 35, 0.4)',
                  border: '1px solid var(--glass-border)',
                }}
              >
                <div className="text-xl mb-1">{emojis[planet]}</div>
                <div className="text-xs font-medium" style={{ color: 'var(--cosmic-text)' }}>
                  {planet}
                </div>
                <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
                  {detail?.sign || '—'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Deep Vimshottari Dasha Hierarchy */}
      {hasDasha && (
        <div
          className="rounded-2xl p-5"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--glass-border)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <h3
            className="text-lg font-bold mb-4"
            style={{
              color: 'var(--cosmic-gold)',
              fontFamily: 'var(--font-playfair), Georgia, serif',
            }}
          >
            Vimshottari Dasha Hierarchy
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {[
              { label: 'Mahadasha', data: deepDasha.md, color: 'var(--cosmic-gold)' },
              { label: 'Antardasha', data: deepDasha.ad, color: 'var(--benefic-green)' },
              { label: 'Pratyantardasha', data: deepDasha.pd, color: '#60a5fa' },
              { label: 'Sookshma', data: deepDasha.sd, color: '#c084fc' },
            ].map((level) => (
              <div
                key={level.label}
                className="rounded-xl p-3"
                style={{
                  background: 'rgba(26, 20, 35, 0.5)',
                  border: `1px solid ${level.color}30`,
                }}
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

          {/* Dasha Timeline (MD periods) */}
          <div>
            <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--cosmic-muted)' }}>
              MAHADASHA TIMELINE
            </h4>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {deepDasha.ad_timeline?.map((period: any, idx: number) => {
                const isActive = period.lord === deepDasha.md.lord;
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

          {/* Activation Multiplier */}
          <div className="mt-4 p-3 rounded-xl" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
            <div className="flex items-center justify-between">
              <span className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>Activation Multiplier</span>
              <span className="text-sm font-bold" style={{ color: 'var(--cosmic-gold)' }}>
                {deepDasha.activation_multiplier?.toFixed(2)}x
              </span>
            </div>
            <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
              {deepDasha.activation_multiplier >= 1.5 ? 'Peak activation — MD lord is a yoga planet' :
               deepDasha.activation_multiplier >= 1.25 ? 'Strong activation — AD lord is a yoga planet' :
               deepDasha.activation_multiplier >= 1.1 ? 'Moderate activation — PD lord is a yoga planet' :
               'Dormant period — no direct yoga planet activation'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Remedies Tab ─────────────────────────────────────────
function RemediesTab({ data }: { data: EvaluationResponse }) {
  const malefics = Object.entries(data.dignity_map || {})
    .filter(([_, d]) => ['Debilitated', 'Enemy'].includes(d as string))
    .map(([p]) => p);

  const remedies: Record<string, { mantra: string; gem: string; deity: string; color: string }> = {
    SUN: { mantra: 'Om Suryaya Namaha', gem: 'Ruby', deity: 'Surya', color: 'Red' },
    MOON: { mantra: 'Om Chandraya Namaha', gem: 'Pearl', deity: 'Chandra', color: 'White' },
    MARS: { mantra: 'Om Angarakaya Namaha', gem: 'Red Coral', deity: 'Hanuman', color: 'Red' },
    MERCURY: { mantra: 'Om Budhaya Namaha', gem: 'Emerald', deity: 'Vishnu', color: 'Green' },
    JUPITER: { mantra: 'Om Gurave Namaha', gem: 'Yellow Sapphire', deity: 'Brihaspati', color: 'Yellow' },
    VENUS: { mantra: 'Om Shukraya Namaha', gem: 'Diamond', deity: 'Lakshmi', color: 'White' },
    SATURN: { mantra: 'Om Shanicharaya Namaha', gem: 'Blue Sapphire', deity: 'Shani', color: 'Blue' },
  };

  return (
    <div className="space-y-4">
      {malefics.length === 0 ? (
        <div
          className="rounded-2xl p-8 text-center"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--glass-border)',
          }}
        >
          <Gem size={32} className="mx-auto mb-3 opacity-30" style={{ color: 'var(--cosmic-muted)' }} />
          <p style={{ color: 'var(--cosmic-muted)' }}>No major afflictions detected.</p>
          <p className="text-xs mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            Your chart shows balanced planetary influences.
          </p>
        </div>
      ) : (
        malefics.map((planet) => {
          const r = remedies[planet] || remedies.SUN;
          return (
            <div
              key={planet}
              className="rounded-xl p-4"
              style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(16px)',
              }}
            >
              <h4 className="font-semibold text-sm mb-3" style={{ color: 'var(--cosmic-gold)' }}>
                Remedies for {planet} ({data.dignity_map[planet]})
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span style={{ color: 'var(--cosmic-muted)' }}>Mantra: </span>
                  <span style={{ color: 'var(--cosmic-text)' }}>{r.mantra}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--cosmic-muted)' }}>Gemstone: </span>
                  <span style={{ color: 'var(--cosmic-text)' }}>{r.gem}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--cosmic-muted)' }}>Deity: </span>
                  <span style={{ color: 'var(--cosmic-text)' }}>{r.deity}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--cosmic-muted)' }}>Favorable Color: </span>
                  <span style={{ color: 'var(--cosmic-text)' }}>{r.color}</span>
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────
export default function ChartPage() {
  const [view, setView] = useState<'north' | 'south'>('north');
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [source, setSource] = useState<'live' | 'mock'>('mock');
  const [activeTab, setActiveTab] = useState<TabKey>('birth_chart');
  const [divisionalType, setDivisionalType] = useState('D1');
  const [fixtureId, setFixtureId] = useState<string | undefined>(undefined);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('jre_last_evaluation');
      if (stored) {
        const parsed = JSON.parse(stored) as EvaluationResponse;
        if (parsed.lagna && parsed.planet_details) {
          setData(parsed);
          setSource('live');
          // Extract fixture_id from evaluation data or localStorage
          const storedFixture = localStorage.getItem('jre_fixture_id');
          if (storedFixture) {
            setFixtureId(storedFixture);
          }
          return;
        }
      }
    } catch {
      // ignore
    }
    // Fallback to mock data
    setData(MOCK_DATA);
    setSource('mock');
  }, []);

  if (!data) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12">
        <ChartSkeleton />
        <p className="text-center text-sm mt-6" style={{ color: 'var(--cosmic-muted)' }}>Loading chart data…</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:py-12">
      {/* ── Header ──────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6"
      >
        <div>
          <h1
            className="text-2xl sm:text-3xl font-bold"
            style={{
              color: 'var(--cosmic-text)',
              fontFamily: 'var(--font-playfair), Georgia, serif',
            }}
          >
            Birth Chart
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            {data.subject} · Lagna:{' '}
            <strong style={{ color: 'var(--cosmic-gold)' }}>{data.lagna}</strong>
          </p>
        </div>
        <ViewToggle active={view} onChange={setView} />
      </motion.div>

      {/* ── Mock data banner ─────────────────────────── */}
      {source === 'mock' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-3 rounded-xl flex items-start gap-2.5 text-xs"
          style={{
            background: 'rgba(234, 179, 8, 0.08)',
            border: '1px solid rgba(234, 179, 8, 0.2)',
            color: 'var(--cosmic-muted)',
          }}
        >
          <AlertCircle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
          <p>
            Showing <strong style={{ color: 'var(--cosmic-gold)' }}>demo data</strong> for UI preview.{' '}
            Run an evaluation from the{' '}
            <a href="/evaluate" style={{ color: 'var(--cosmic-gold)', textDecoration: 'underline' }}>
              Birth Chart page
            </a>{' '}
            to see your actual chart.
          </p>
        </motion.div>
      )}

      {/* ── Tab Bar ──────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="mb-6"
      >
        <TabBar active={activeTab} onChange={setActiveTab} />
      </motion.div>

      {/* ── Birth Chart Tab ──────────────────────────── */}
      {activeTab === 'birth_chart' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Divisional Chart Selector */}
          <div className="mb-6 max-w-sm">
            <DivisionalChartSelector selected={divisionalType} onChange={setDivisionalType} />
          </div>

          {/* Split Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Chart (left / top) */}
            <div className="lg:col-span-2 flex items-start justify-center">
              <div
                className="w-full max-w-md rounded-2xl p-4"
                style={{
                  background: 'var(--glass-bg)',
                  backdropFilter: 'blur(16px) saturate(1.2)',
                  border: '1px solid var(--glass-border)',
                }}
              >
                {view === 'north' ? (
                  <NorthIndianChart
                    lagna={data.lagna}
                    planetDetails={data.planet_details}
                    divisionalType={divisionalType}
                  />
                ) : (
                  <div
                    className="flex items-center justify-center py-16 text-sm"
                    style={{ color: 'var(--cosmic-muted)' }}
                  >
                    <div className="text-center">
                      <Square size={32} className="mx-auto mb-3 opacity-30" />
                      <p>South Indian view coming soon.</p>
                      <p className="text-xs mt-1">Switch to North Indian for now.</p>
                    </div>
                  </div>
                )}

                {/* Chart legend */}
                <div
                  className="mt-3 pt-3 flex flex-wrap gap-3 justify-center text-[10px]"
                  style={{
                    borderTop: '1px solid var(--glass-border)',
                    color: 'var(--cosmic-muted)',
                  }}
                >
                  <span>Su=Sun</span>
                  <span>Mo=Moon</span>
                  <span>Ma=Mars</span>
                  <span>Me=Mercury</span>
                  <span>Ju=Jupiter</span>
                  <span>Ve=Venus</span>
                  <span>Sa=Saturn</span>
                  <span>Ra=Rahu</span>
                  <span>Ke=Ketu</span>
                </div>
              </div>
            </div>

            {/* Table (right / bottom) */}
            <div className="lg:col-span-3">
              <PlanetaryTable
                lagna={data.lagna}
                planetDetails={data.planet_details}
                dignityMap={data.dignity_map}
              />

              {/* Birth data summary */}
              {data.birth_data_display && (
                <div
                  className="mt-4 rounded-2xl p-4"
                  style={{
                    background: 'var(--glass-bg)',
                    backdropFilter: 'blur(16px) saturate(1.2)',
                    border: '1px solid var(--glass-border)',
                  }}
                >
                  <h3
                    className="text-xs font-semibold uppercase tracking-widest mb-3"
                    style={{ color: 'var(--cosmic-muted)' }}
                  >
                    BIRTH DATA
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    {[
                      ['Date', data.birth_data_display.date],
                      ['Time', data.birth_data_display.time],
                      ['Timezone', data.birth_data_display.timezone],
                      ['Latitude', data.birth_data_display.latitude],
                      ['Longitude', data.birth_data_display.longitude],
                      ['Moon Nakshatra', data.birth_data_display.moon_nakshatra],
                    ].map(([label, value]) => (
                      <div key={label}>
                        <span style={{ color: 'var(--cosmic-muted)' }}>{label}:</span>{' '}
                        <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>
                          {value || '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Divisional Tab ───────────────────────────── */}
      {activeTab === 'divisional' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <DivisionalTab fixtureId={fixtureId} />
        </motion.div>
      )}

      {/* ── Shadbala Tab ─────────────────────────────── */}
      {activeTab === 'shadbala' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <ShadbalaTab fixtureId={fixtureId} />
        </motion.div>
      )}

      {/* ── Ashtakavarga Tab ─────────────────────────── */}
      {activeTab === 'ashtakavarga' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <AshtakavargaTab fixtureId={fixtureId} />
        </motion.div>
      )}

      {/* ── Yogas Tab ────────────────────────────────── */}
      {activeTab === 'yogas' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <YogasTab data={data} />
        </motion.div>
      )}

      {/* ── Transits Tab ─────────────────────────────── */}
      {activeTab === 'transits' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <TransitsTab data={data} />
        </motion.div>
      )}

      {/* ── Remedies Tab ─────────────────────────────── */}
      {activeTab === 'remedies' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <RemediesApiTab fixtureId={fixtureId} />
        </motion.div>
      )}
    </div>
  );
}
