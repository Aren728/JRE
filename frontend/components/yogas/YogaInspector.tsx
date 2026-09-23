'use client';

import React, { useMemo, useState } from 'react';
import type { YogaResult } from '@/lib/api';

// ── Type Definitions ──────────────────────────────────────────────────────────

export interface YogaEvaluation {
  id: string;
  name: string;
  category: 'RAJA' | 'DHANA' | 'MAHAPURUSHA' | 'NABHASA' | 'ARISHTA';
  description: string;
  participatingPlanets: string[];
  status: 'ACTIVE_DASHA' | 'ACTIVE_TRANSIT' | 'DORMANT' | 'AFFLICTED';
  strengthScore: number;
  activatingLord?: string;
  houseCombination: string;
  ruleConditions: Array<{ conditionText: string; isMet: boolean }>;
}

interface YogaInspectorProps {
  yogas: YogaEvaluation[];
  activeDashaLords: string[];
  minStrengthCutoff: number;
  onSelectYoga?: (yoga: YogaEvaluation) => void;
  /** Bodies to glow (Phase 4 scene sync); case-insensitive. */
  highlightedBodies?: string[];
}

// ── Constants ────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
  RAJA: '#f472b6',
  DHANA: '#34d399',
  MAHAPURUSHA: '#fbbf24',
  NABHASA: '#22d3ee',
  ARISHTA: '#ef4444',
};

const STATUS_LABELS: Record<string, string> = {
  ACTIVE_DASHA: 'Active (Dasha)',
  ACTIVE_TRANSIT: 'Active (Transit)',
  DORMANT: 'Dormant',
  AFFLICTED: 'Afflicted',
};

const STATUS_COLORS: Record<string, string> = {
  ACTIVE_DASHA: '#34d399',
  ACTIVE_TRANSIT: '#22d3ee',
  DORMANT: '#94a3b8',
  AFFLICTED: '#ef4444',
};

// ── Filter State ──────────────────────────────────────────────────────────────

type FilterState = {
  showActive: boolean;
  showDormant: boolean;
  showAfflicted: boolean;
  selectedCategory: string | null;
  minStrength: number;
};

const DEFAULT_FILTERS: FilterState = {
  showActive: true,
  showDormant: true,
  showAfflicted: true,
  selectedCategory: null,
  minStrength: 0,
};

// ── Filter Rail ───────────────────────────────────────────────────────────────

interface FilterRailProps {
  filters: FilterState;
  onFilterChange: (f: FilterState) => void;
  categories: string[];
  activeDashaLords: string[];
}

function FilterRail({ filters, onFilterChange, categories, activeDashaLords }: FilterRailProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl" style={{ background: 'rgba(26, 20, 35, 0.6)', border: '1px solid var(--glass-border)' }}>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>Status:</span>
        {(['showActive', 'showDormant', 'showAfflicted'] as const).map((key) => (
          <button key={key} type="button" onClick={() => onFilterChange({ ...filters, [key]: !filters[key] })}
            className="px-2.5 py-1 text-[10px] rounded-full font-medium transition-all"
            style={{
              background: filters[key] ? 'rgba(197,168,128,0.2)' : 'rgba(255,255,255,0.05)',
              color: filters[key] ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
              border: filters[key] ? '1px solid rgba(197,168,128,0.3)' : '1px solid transparent',
            }}
          >
            {key === 'showActive' ? 'Active' : key === 'showDormant' ? 'Dormant' : 'Afflicted'}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>Category:</span>
        <select value={filters.selectedCategory || ''} onChange={(e) => onFilterChange({ ...filters, selectedCategory: filters.selectedCategory === e.target.value ? null : e.target.value })}
          className="text-[10px] p-1.5 rounded border" style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(197,168,128,0.2)', color: 'var(--cosmic-text)' }}>
          <option value="">All Categories</option>
          {categories.map((cat) => <option key={cat} value={cat}>{cat}</option>)}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>Strength ≥ {filters.minStrength.toFixed(2)}:</span>
        <input type="range" min="0" max="2" step="0.05" value={filters.minStrength}
          onChange={(e) => onFilterChange({ ...filters, minStrength: parseFloat(e.target.value) || 0 })}
          className="w-24" style={{ accentColor: 'var(--cosmic-gold)' }} />
      </div>
      <div className="ml-auto flex items-center gap-1.5 text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
        <span>Active Dasha:</span>
        <span className="font-medium" style={{ color: 'var(--cosmic-gold)' }}>{activeDashaLords.join(', ')}</span>
      </div>
    </div>
  );
}

// ── Yoga Card ────────────────────────────────────────────────────────────────

interface YogaCardProps {
  yoga: YogaEvaluation;
  isSelected: boolean;
  onSelect: () => void;
  isHighlighted?: boolean;
}

function YogaCard({ yoga, isSelected, onSelect, isHighlighted = false }: YogaCardProps) {
  const catColor = CATEGORY_COLORS[yoga.category] || 'var(--cosmic-muted)';
  const statColor = STATUS_COLORS[yoga.status] || 'var(--cosmic-muted)';
  const sr = yoga.strengthScore;

  return (
    <div className="rounded-xl p-4 cursor-pointer transition-all duration-200"
      style={{ background: isSelected ? 'rgba(197,168,128,0.12)' : 'rgba(26,20,35,0.7)', border: isSelected ? '2px solid var(--cosmic-gold)' : '1px solid var(--glass-border)', boxShadow: isSelected ? '0 0 20px rgba(197,168,128,0.2)' : isHighlighted ? '0 0 14px rgba(34,211,238,0.3)' : 'none' }}
      data-highlighted={isHighlighted && !isSelected ? '' : undefined}
      onClick={onSelect} role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(); }}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-base font-bold truncate" style={{ color: 'var(--cosmic-text)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>{yoga.name}</h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0" style={{ background: `${catColor}20`, color: catColor }}>{yoga.category}</span>
          </div>
          <span className="inline-block text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: `${statColor}20`, color: statColor }}>{STATUS_LABELS[yoga.status]}</span>
          <div className="text-[10px] mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            Strength: <span style={{ color: sr >= 1 ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)' }}>{sr.toFixed(2)}</span>
            {sr >= 1 ? <span className="ml-1 text-green-400">✓</span> : <span className="ml-1 text-red-400">✗</span>}
          </div>
        </div>
        {yoga.activatingLord && (
          <div className="text-[10px] px-2 py-1 rounded shrink-0 text-right" style={{ background: 'rgba(197,168,128,0.15)', color: 'var(--cosmic-gold)' }}>
            <div className="font-semibold">{yoga.activatingLord}</div>
          </div>
        )}
      </div>
      <p className="text-[10px] leading-relaxed mb-3" style={{ color: 'var(--cosmic-muted)' }}>{yoga.description}</p>
      <div className="text-[10px] mb-3" style={{ color: 'var(--cosmic-muted)' }}>
        <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>Configuration:</span> {yoga.houseCombination}
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {yoga.participatingPlanets.map((p) => (
          <span key={p} className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(197,168,128,0.1)', color: 'var(--cosmic-gold)' }}>{p}</span>
        ))}
      </div>
      <details className="group">
        <summary className="text-[10px] font-semibold uppercase tracking-wider cursor-pointer hover:text-cosmic-gold transition-colors" style={{ color: 'var(--cosmic-muted)' }}>
          Rule Conditions ({yoga.ruleConditions.length})
        </summary>
        <div className="mt-2 space-y-1.5">
          {yoga.ruleConditions.map((rule, idx) => (
            <div key={idx} className="flex items-start gap-2 text-[10px] p-1.5 rounded"
              style={{ background: rule.isMet ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)' }}>
              <span className="shrink-0 mt-0.5" style={{ color: rule.isMet ? '#34d399' : '#ef4444', fontWeight: 'bold' }}>{rule.isMet ? '✓' : '✗'}</span>
              <span style={{ color: 'var(--cosmic-muted)' }}>{rule.conditionText}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="text-center py-12">
      <div className="text-4xl mb-4 opacity-50">🔍</div>
      <h3 className="text-base font-bold mb-2" style={{ color: 'var(--cosmic-text)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>No Yoga Matches</h3>
      <p className="text-sm" style={{ color: 'var(--cosmic-muted)' }}>Try adjusting your strength threshold or status filters.</p>
      <button type="button" onClick={onReset}
        className="mt-4 px-4 py-2 text-sm rounded-lg bg-blue-600/20 text-blue-400 border border-blue-600/30 hover:bg-blue-600/30 transition-colors">
        Reset Filters
      </button>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function YogaInspector({ yogas, activeDashaLords, minStrengthCutoff, onSelectYoga, highlightedBodies = [] }: YogaInspectorProps) {
  const [filters, setFilters] = useState<FilterState>({ ...DEFAULT_FILTERS, minStrength: minStrengthCutoff });
  const [selectedYogaId, setSelectedYogaId] = useState<string | null>(null);
  const highlightedSet = useMemo(() => new Set(highlightedBodies.map((b) => b.toUpperCase())), [highlightedBodies]);

  const categories = useMemo(() => Array.from(new Set(yogas.map((y) => y.category))).sort(), [yogas]);

  const filteredYogas = useMemo(() =>
    yogas.filter((y) => {
      if (y.status === 'ACTIVE_DASHA' && !filters.showActive) return false;
      if (y.status === 'DORMANT' && !filters.showDormant) return false;
      if (y.status === 'AFFLICTED' && !filters.showAfflicted) return false;
      if (y.status === 'ACTIVE_TRANSIT' && !filters.showActive) return false;
      if (filters.selectedCategory && y.category !== filters.selectedCategory) return false;
      if (y.strengthScore < filters.minStrength) return false;
      return true;
    }), [yogas, filters]);

  const sortedYogas = useMemo(() => [...filteredYogas].sort((a, b) => b.strengthScore - a.strengthScore), [filteredYogas]);

  const handleSelect = (y: YogaEvaluation) => {
    setSelectedYogaId(y.id);
    onSelectYoga?.(y);
  };

  const handleReset = () => {
    setFilters({ ...DEFAULT_FILTERS, minStrength: minStrengthCutoff });
  };

  return (
    <div className="space-y-4">
      <FilterRail filters={filters} onFilterChange={setFilters} categories={categories} activeDashaLords={activeDashaLords} />
      <div className="flex items-center justify-between text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
        <span>Showing {sortedYogas.length} of {yogas.length} yogas</span>
        {filters.minStrength > 0 && <span className="text-amber-400">Filtered by strength ≥ {filters.minStrength.toFixed(2)}</span>}
      </div>
      {sortedYogas.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {sortedYogas.map((y) => (
            <YogaCard key={y.id} yoga={y} isSelected={selectedYogaId === y.id} onSelect={() => handleSelect(y)} isHighlighted={y.participatingPlanets.some((p) => highlightedSet.has(p.toUpperCase()))} />
          ))}
        </div>
      ) : (
        <EmptyState onReset={handleReset} />
      )}
      <div className="flex flex-wrap gap-4 justify-center pt-2 border-t" style={{ borderColor: 'var(--glass-border)' }}>
        {Object.entries(STATUS_LABELS).map(([s, label]) => (
          <div key={s} className="flex items-center gap-1.5 text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_COLORS[s] || 'var(--cosmic-muted)' }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Mapper ────────────────────────────────────────────────────────────────────

export function mapYogaResultToEvaluation(
  result: YogaResult,
  activeDashaLords: string[],
  minStrengthThreshold: number = 1.0,
): YogaEvaluation {
  let status: YogaEvaluation['status'] = 'DORMANT';
  let activatingLord: string | undefined;

  if (result.dasha_activation?.present) {
    const presentLords = result.dasha_activation.present.map((p) => p.lord);
    const matchingLords = presentLords.filter((lord) =>
      result.involved_planets.some((p) => p.toUpperCase() === lord.toUpperCase()));
    if (matchingLords.length > 0) {
      status = 'ACTIVE_DASHA';
      activatingLord = `${matchingLords[0]} (MD)`;
    }
  }

  if (status === 'DORMANT') {
    const matchingLords = activeDashaLords.filter((lord) =>
      result.involved_planets.some((p) => p.toUpperCase() === lord.toUpperCase()));
    if (matchingLords.length > 0) {
      status = 'ACTIVE_DASHA';
      activatingLord = `${matchingLords[0]} (MD)`;
    }
  }

  const categoryMap: Record<string, YogaEvaluation['category']> = {
    GAJAKESARI: 'RAJA', RAJA: 'RAJA', DHANA: 'DHANA',
    BUDHADITYA: 'MAHAPURUSHA', VIPAREETA_RAJA: 'ARISHTA',
    UPAPURUSHA: 'NABHASA', NEECHA_BHANGA: 'NABHASA',
    SARASWATI: 'NABHASA', PANCHAMAHAPURUSHA: 'MAHAPURUSHA',
  };

  const ruleConditions: YogaEvaluation['ruleConditions'] = [
    { conditionText: 'Yoga formed by classical rules', isMet: result.status === 'FORMED' },
    { conditionText: `Static strength ≥ ${minStrengthThreshold}`, isMet: result.static_strength >= minStrengthThreshold },
    { conditionText: 'Dynamic strength > 0', isMet: result.dynamic_strength !== null && result.dynamic_strength > 0 },
    { conditionText: 'No cancellation reason', isMet: !result.cancellation_reason },
  ];

  return {
    id: result.yoga_name.toLowerCase().replace(/\s+/g, '_'),
    name: result.yoga_name,
    category: categoryMap[result.category] || 'NABHASA',
    description:
      (result as { provenance?: { formation_evidence?: string } }).provenance?.formation_evidence ||
      `${result.yoga_name} yoga detected`,
    participatingPlanets: result.involved_planets,
    status,
    strengthScore: result.static_strength / minStrengthThreshold,
    activatingLord,
    houseCombination: result.involved_planets.length >= 2
      ? `${result.involved_planets[0]} & ${result.involved_planets[1]} combination`
      : 'Single planet configuration',
    ruleConditions,
  };
}
