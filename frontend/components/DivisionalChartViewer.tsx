'use client';

import { useState, useEffect, useCallback } from 'react';
import NorthIndianChart from '@/components/NorthIndianChart';
import { Spinner } from '@/components/LoadingSkeleton';
import { api } from '@/lib/api';
import type { DivisionalChartResponse } from '@/lib/api';

// ── Divisional Chart Options ─────────────────────────────
const DIVISIONAL_OPTIONS = [
  { value: 'D1', label: 'Rashi (D-1)', description: 'Main birth chart' },
  { value: 'D2', label: 'Hora (D-2)', description: 'Wealth & prosperity' },
  { value: 'D3', label: 'Drekkana (D-3)', description: 'Siblings & courage' },
  { value: 'D4', label: 'Chaturthamsha (D-4)', description: 'Property & fortune' },
  { value: 'D7', label: 'Saptamamsha (D-7)', description: 'Children & creativity' },
  { value: 'D9', label: 'Navamsha (D-9)', description: 'Marriage & dharma' },
  { value: 'D10', label: 'Dashamamsha (D-10)', description: 'Career & profession' },
  { value: 'D12', label: 'Dwadashamsha (D-12)', description: 'Parents & ancestry' },
  { value: 'D16', label: 'Shodashamsha (D-16)', description: 'Vehicles & comforts' },
  { value: 'D24', label: 'Chaturvimshamsha (D-24)', description: 'Education & knowledge' },
  { value: 'D27', label: 'Bhamsha (D-27)', description: 'Strengths & weaknesses' },
  { value: 'D30', label: 'Trishamsha (D-30)', description: 'Evil & misfortune' },
  { value: 'D40', label: 'Chaturashitamsha (D-40)', description: "Mother's lineage" },
  { value: 'D45', label: 'Khavedamsha (D-45)', description: 'Auspiciousness' },
  { value: 'D60', label: 'Shashtiamsha (D-60)', description: 'Past life karma' },
];

// ── Planet symbol map ────────────────────────────────────
const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};

// ── Component ────────────────────────────────────────────
interface DivisionalChartViewerProps {
  fixtureId?: string;
  initialDivision?: string;
  onDivisionChange?: (division: string) => void;
}

export default function DivisionalChartViewer({
  fixtureId,
  initialDivision = 'D9',
  onDivisionChange,
}: DivisionalChartViewerProps) {
  const [selectedDivision, setSelectedDivision] = useState(initialDivision);
  const [chartData, setChartData] = useState<DivisionalChartResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChart = useCallback(async (division: string) => {
    if (!fixtureId) {
      setError('No fixture ID available. Run an evaluation first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.getDivisionalChart(fixtureId, division, getApiKey());
      setChartData(response.data);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to fetch chart';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [fixtureId]);

  useEffect(() => {
    fetchChart(selectedDivision);
  }, [selectedDivision, fetchChart]);

  const handleDivisionChange = (division: string) => {
    setSelectedDivision(division);
    onDivisionChange?.(division);
  };

  return (
    <div className="space-y-4">
      {/* Division Selector */}
      <div className="flex flex-wrap gap-2">
        {/* Quick access buttons for common divisions */}
        {['D1', 'D9', 'D10'].map((div) => (
          <button
            key={div}
            type="button"
            onClick={() => handleDivisionChange(div)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all"
            style={{
              background: selectedDivision === div ? 'rgba(197, 168, 128, 0.15)' : 'var(--glass-bg)',
              border: `1px solid ${selectedDivision === div ? 'var(--cosmic-gold)' : 'var(--glass-border)'}`,
              color: selectedDivision === div ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
            }}
          >
            {div}
          </button>
        ))}

        {/* Dropdown for other divisions */}
        <select
          value={selectedDivision}
          onChange={(e) => handleDivisionChange(e.target.value)}
          className="px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer transition-all appearance-none"
          style={{
            background: !['D1', 'D9', 'D10'].includes(selectedDivision)
              ? 'rgba(197, 168, 128, 0.15)'
              : 'var(--glass-bg)',
            border: `1px solid ${!['D1', 'D9', 'D10'].includes(selectedDivision) ? 'var(--cosmic-gold)' : 'var(--glass-border)'}`,
            color: !['D1', 'D9', 'D10'].includes(selectedDivision) ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
          }}
        >
          {DIVISIONAL_OPTIONS.filter((d) => !['D1', 'D9', 'D10'].includes(d.value)).map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label} — {opt.description}
            </option>
          ))}
        </select>
      </div>

      {/* Chart Content */}
      {loading ? (
        <div
          className="rounded-2xl p-8"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <Spinner size={24} label={`Loading ${selectedDivision} chart...`} />
        </div>
      ) : error ? (
        <div
          className="rounded-2xl p-6"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}
        >
          <p className="text-sm" style={{ color: '#fca5a5' }}>
            {error}
          </p>
          <button
            type="button"
            onClick={() => fetchChart(selectedDivision)}
            className="mt-2 text-xs px-3 py-1 rounded-lg"
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              color: '#fca5a5',
            }}
          >
            Retry
          </button>
        </div>
      ) : chartData ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div
            className="rounded-2xl p-4"
            style={{
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(16px) saturate(1.2)',
              border: '1px solid var(--glass-border)',
            }}
          >
            <NorthIndianChart
              lagna={chartData.lagna}
              planetDetails={Object.fromEntries(
                Object.entries(chartData.planets).map(([name, p]) => [
                  name,
                  { sign: p.rashi, degree_in_sign: p.degree_in_sign },
                ])
              )}
              divisionalType={selectedDivision}
            />
          </div>

          {/* Planet Positions Table */}
          <div
            className="rounded-2xl overflow-hidden"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
          >
            <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
              <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
                {chartData.name}
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                {chartData.description}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                    <th className="px-3 py-2.5 text-left font-medium">Planet</th>
                    <th className="px-3 py-2.5 text-left font-medium">Sign</th>
                    <th className="px-3 py-2.5 text-right font-medium">Degree</th>
                    <th className="px-3 py-2.5 text-center font-medium">House</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(chartData.planets).map(([name, planet], i) => (
                    <tr
                      key={name}
                      className="transition-colors duration-150"
                      style={{
                        borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                      }}
                    >
                      <td className="px-3 py-2.5">
                        <span className="inline-flex items-center gap-1.5">
                          <span className="text-base" style={{ opacity: 0.7 }}>
                            {PLANET_SYMBOLS[name] || ''}
                          </span>
                          <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>
                            {name}
                          </span>
                        </span>
                      </td>
                      <td className="px-3 py-2.5" style={{ color: 'var(--cosmic-text)' }}>
                        {planet.rashi_name}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono text-xs" style={{ color: 'var(--cosmic-muted)' }}>
                        {planet.degree_in_sign.toFixed(2)}°
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <span
                          className="inline-flex items-center justify-center w-7 h-7 rounded-md text-xs font-semibold"
                          style={{
                            background: 'rgba(197, 168, 128, 0.1)',
                            color: 'var(--cosmic-gold)',
                            border: '1px solid rgba(197, 168, 128, 0.15)',
                          }}
                        >
                          {planet.house}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Vargottama Planets */}
            {chartData.vargottama_planets && chartData.vargottama_planets.length > 0 && (
              <div className="px-4 py-3 border-t" style={{ borderColor: 'var(--glass-border)' }}>
                <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--cosmic-muted)' }}>
                  Vargottama Planets
                </h4>
                <div className="flex flex-wrap gap-2">
                  {chartData.vargottama_planets.map((planet) => (
                    <span
                      key={planet}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium"
                      style={{
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        color: 'var(--benefic-green)',
                      }}
                    >
                      {PLANET_SYMBOLS[planet] || ''} {planet}
                    </span>
                  ))}
                </div>
                <p className="text-[10px] mt-2" style={{ color: 'var(--cosmic-muted)' }}>
                  Vargottama planets (same sign in D1 and {selectedDivision}) are especially powerful.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

// ── Get API key from localStorage ────────────────────────
function getApiKey(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('jre_api_key') || '';
}
