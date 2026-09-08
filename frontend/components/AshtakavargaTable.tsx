'use client';

import type { AshtakavargaResponse } from '@/lib/api';

// ── Constants ────────────────────────────────────────────
const PLANET_ORDER = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN'];

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄',
};

const HOUSE_NUMBERS = Array.from({ length: 12 }, (_, i) => i + 1);

// ── Bindu cell color ─────────────────────────────────────
function getBinduColor(value: number): { color: string; bg: string } {
  if (value === 0) return { color: 'var(--cosmic-muted)', bg: 'transparent' };
  if (value >= 4) return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.12)' };
  if (value >= 3) return { color: 'var(--cosmic-gold)', bg: 'rgba(197, 168, 128, 0.08)' };
  if (value >= 2) return { color: '#eab308', bg: 'rgba(234, 179, 8, 0.06)' };
  return { color: 'var(--cosmic-muted)', bg: 'transparent' };
}

// ── SAV house color ──────────────────────────────────────
function getSavColor(sav: number): { color: string; bg: string; label: string } {
  if (sav >= 30) return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.1)', label: 'Strong' };
  if (sav >= 28) return { color: 'var(--cosmic-gold)', bg: 'rgba(197, 168, 128, 0.06)', label: 'Good' };
  if (sav >= 25) return { color: '#eab308', bg: 'rgba(234, 179, 8, 0.04)', label: 'Average' };
  if (sav >= 24) return { color: 'var(--cosmic-muted)', bg: 'transparent', label: 'Below Avg' };
  return { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.06)', label: 'Weak' };
}

// ── Component ────────────────────────────────────────────
interface AshtakavargaTableProps {
  data: AshtakavargaResponse | null;
  loading?: boolean;
  error?: string | null;
}

export default function AshtakavargaTable({ data, loading, error }: AshtakavargaTableProps) {
  if (loading) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded-lg" style={{ background: 'rgba(197,168,128,0.06)' }} />
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-8 rounded-lg" style={{ background: 'rgba(197,168,128,0.04)' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{
          background: 'var(--glass-bg)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}
      >
        <p className="text-sm" style={{ color: '#fca5a5' }}>
          Failed to load Ashtakavarga data: {error}
        </p>
      </div>
    );
  }

  if (!data || !data.bav) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <p style={{ color: 'var(--cosmic-muted)' }}>No Ashtakavarga data available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Strongest House
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--benefic-green)' }}>
            House {data.strongest_house}
          </div>
          <div className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
            SAV: {data.sav[String(data.strongest_house)] || 0} bindus
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Weakest House
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--malefic-red)' }}>
            House {data.weakest_house}
          </div>
          <div className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
            SAV: {data.sav[String(data.weakest_house)] || 0} bindus
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Average SAV
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--cosmic-gold)' }}>
            {data.average_sav.toFixed(1)}
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Strong Houses
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--cosmic-text)' }}>
            {Object.values(data.sav).filter(s => (s as number) >= 28).length} / 12
          </div>
        </div>
      </div>

      {/* BAV Matrix Table */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
          <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
            BHINNA ASHTAKAVARGA (BAV) — BINDU MATRIX
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
            Each cell shows the bindu count from the row planet to the column house
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                <th className="px-3 py-2.5 text-left font-medium sticky left-0 z-10" style={{ background: 'var(--glass-bg)' }}>
                  Giver
                </th>
                {HOUSE_NUMBERS.map((h) => (
                  <th key={h} className="px-2 py-2.5 text-center font-medium min-w-[40px]">
                    {h}
                  </th>
                ))}
                <th className="px-2 py-2.5 text-center font-bold" style={{ color: 'var(--cosmic-gold)' }}>
                  Total
                </th>
              </tr>
            </thead>
            <tbody>
              {PLANET_ORDER.map((planet, i) => {
                const bav = data.bav[planet];
                if (!bav) return null;

                return (
                  <tr
                    key={planet}
                    className="transition-colors duration-150"
                    style={{
                      borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                    }}
                  >
                    <td className="px-3 py-2.5 sticky left-0 z-10" style={{ background: 'var(--glass-bg)' }}>
                      <span className="inline-flex items-center gap-1.5">
                        <span className="text-base" style={{ opacity: 0.7 }}>{PLANET_SYMBOLS[planet]}</span>
                        <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>{planet}</span>
                      </span>
                    </td>
                    {HOUSE_NUMBERS.map((h) => {
                      const bindu = bav.bindus[String(h)] || 0;
                      const colorStyle = getBinduColor(bindu);
                      return (
                        <td
                          key={h}
                          className="px-2 py-2.5 text-center font-mono font-medium"
                          style={{ color: colorStyle.color, background: colorStyle.bg }}
                        >
                          {bindu}
                        </td>
                      );
                    })}
                    <td className="px-2 py-2.5 text-center font-bold font-mono" style={{ color: 'var(--cosmic-gold)' }}>
                      {bav.total_bindus}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* SAV (Sarva Ashtakavarga) */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
          <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
            SARVA ASHTAKAVARGA (SAV) — TOTAL BINDUS PER HOUSE
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
            Strong houses: ≥28 bindus | Weak houses: &lt;24 bindus
          </p>
        </div>

        <div className="p-4">
          {/* SAV Bar Chart */}
          <div className="space-y-2">
            {HOUSE_NUMBERS.map((h) => {
              const sav = data.sav[String(h)] || 0;
              const colorStyle = getSavColor(sav);
              const maxSav = 56; // Max possible SAV
              const width = Math.min(100, (sav / maxSav) * 100);

              return (
                <div key={h} className="flex items-center gap-3">
                  <span className="w-12 text-xs font-medium text-right" style={{ color: 'var(--cosmic-text)' }}>
                    H{h}
                  </span>
                  <div className="flex-1 h-4 rounded-full overflow-hidden" style={{ background: 'rgba(26,20,35,0.5)' }}>
                    <div
                      className="h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                      style={{
                        width: `${width}%`,
                        background: colorStyle.bg || `${colorStyle.color}20`,
                        minWidth: sav > 0 ? '1.5rem' : '0',
                      }}
                    >
                      {sav > 0 && (
                        <span className="text-[10px] font-bold" style={{ color: colorStyle.color }}>
                          {sav}
                        </span>
                      )}
                    </div>
                  </div>
                  <span
                    className="w-16 text-[10px] font-medium"
                    style={{ color: colorStyle.color }}
                  >
                    {colorStyle.label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* SAV Table (alternative view) */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  {HOUSE_NUMBERS.map((h) => (
                    <th key={h} className="px-2 py-1.5 text-center font-medium">
                      H{h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  {HOUSE_NUMBERS.map((h) => {
                    const sav = data.sav[String(h)] || 0;
                    const colorStyle = getSavColor(sav);
                    return (
                      <td
                        key={h}
                        className="px-2 py-2 text-center font-mono font-bold"
                        style={{ color: colorStyle.color, background: colorStyle.bg }}
                      >
                        {sav}
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
