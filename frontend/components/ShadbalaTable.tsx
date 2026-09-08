'use client';

import type { ShadbalaResponse } from '@/lib/api';

// ── Planet display order and symbols ──────────────────────
const PLANET_ORDER = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN'];

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄',
};

const STRENGTH_LABELS: { key: keyof ShadbalaResponse['planets']['SUN']; label: string; short: string }[] = [
  { key: 'sthana_bala', label: 'Sthana Bala', short: 'Sthana' },
  { key: 'dig_bala', label: 'Dig Bala', short: 'Dig' },
  { key: 'kala_bala', label: 'Kala Bala', short: 'Kala' },
  { key: 'chesta_bala', label: 'Chesta Bala', short: 'Chesta' },
  { key: 'naisargika_bala', label: 'Naisargika Bala', short: 'Naisargika' },
  { key: 'drik_bala', label: 'Drik Bala', short: 'Drik' },
];

// ── Strength value color ─────────────────────────────────
function getStrengthColor(value: number, max: number = 60): string {
  const ratio = value / max;
  if (ratio >= 0.8) return 'var(--benefic-green)';
  if (ratio >= 0.5) return 'var(--cosmic-gold)';
  if (ratio >= 0.25) return '#eab308';
  return 'var(--malefic-red)';
}

// ── Component ────────────────────────────────────────────
interface ShadbalaTableProps {
  data: ShadbalaResponse | null;
  loading?: boolean;
  error?: string | null;
}

export default function ShadbalaTable({ data, loading, error }: ShadbalaTableProps) {
  if (loading) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded-lg" style={{ background: 'rgba(197,168,128,0.06)' }} />
          <div className="space-y-2">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-10 rounded-lg" style={{ background: 'rgba(197,168,128,0.04)' }} />
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
          Failed to load Shadbala data: {error}
        </p>
      </div>
    );
  }

  if (!data || !data.planets) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <p style={{ color: 'var(--cosmic-muted)' }}>No Shadbala data available.</p>
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
            Strongest
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--benefic-green)' }}>
            {PLANET_SYMBOLS[data.strongest_planet]} {data.strongest_planet}
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Weakest
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--malefic-red)' }}>
            {PLANET_SYMBOLS[data.weakest_planet]} {data.weakest_planet}
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Average
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--cosmic-gold)' }}>
            {data.average_strength.toFixed(1)}V
          </div>
        </div>
        <div
          className="rounded-xl p-3"
          style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
            Strong Planets
          </div>
          <div className="text-lg font-bold mt-1" style={{ color: 'var(--cosmic-text)' }}>
            {Object.values(data.planets).filter(p => p.is_strong).length} / {PLANET_ORDER.length}
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
          <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-gold)' }}>
            SHADBALA — SIXFOLD STRENGTH
          </h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
            Values in Virupas (1 Rupa = 60 Virupas). Minimum required: 395V
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-xs uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                <th className="px-3 py-2.5 text-left font-medium sticky left-0 z-10" style={{ background: 'var(--glass-bg)' }}>
                  Planet
                </th>
                {STRENGTH_LABELS.map((s) => (
                  <th key={s.key} className="px-2 py-2.5 text-center font-medium min-w-[70px]">
                    <span className="hidden sm:inline">{s.label}</span>
                    <span className="sm:hidden">{s.short}</span>
                  </th>
                ))}
                <th className="px-3 py-2.5 text-center font-bold" style={{ color: 'var(--cosmic-gold)' }}>
                  Total (V)
                </th>
                <th className="px-3 py-2.5 text-center font-bold" style={{ color: 'var(--cosmic-gold)' }}>
                  Total (R)
                </th>
                <th className="px-3 py-2.5 text-center font-medium">Strong?</th>
              </tr>
            </thead>
            <tbody>
              {PLANET_ORDER.map((planet, i) => {
                const ps = data.planets[planet];
                if (!ps) return null;
                const isStrongest = planet === data.strongest_planet;
                const isWeakest = planet === data.weakest_planet;

                return (
                  <tr
                    key={planet}
                    className="transition-colors duration-150"
                    style={{
                      borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                      background: isStrongest
                        ? 'rgba(16, 185, 129, 0.04)'
                        : isWeakest
                        ? 'rgba(239, 68, 68, 0.04)'
                        : 'transparent',
                    }}
                  >
                    <td className="px-3 py-2.5 sticky left-0 z-10" style={{ background: isStrongest ? 'rgba(16,185,129,0.04)' : isWeakest ? 'rgba(239,68,68,0.04)' : 'var(--glass-bg)' }}>
                      <span className="inline-flex items-center gap-1.5">
                        <span className="text-base" style={{ opacity: 0.7 }}>{PLANET_SYMBOLS[planet]}</span>
                        <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>{planet}</span>
                      </span>
                    </td>
                    {STRENGTH_LABELS.map((s) => {
                      const value = ps[s.key] as number;
                      return (
                        <td key={s.key} className="px-2 py-2.5 text-center font-mono">
                          <span style={{ color: getStrengthColor(value) }}>
                            {typeof value === 'number' ? value.toFixed(1) : '—'}
                          </span>
                        </td>
                      );
                    })}
                    <td className="px-3 py-2.5 text-center font-bold font-mono" style={{ color: 'var(--cosmic-gold)' }}>
                      {ps.total_virupas.toFixed(1)}
                    </td>
                    <td className="px-3 py-2.5 text-center font-mono" style={{ color: 'var(--cosmic-text)' }}>
                      {ps.total_rupas.toFixed(2)}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      {ps.is_strong ? (
                        <span
                          className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold"
                          style={{ background: 'rgba(16,185,129,0.15)', color: 'var(--benefic-green)' }}
                        >
                          YES
                        </span>
                      ) : (
                        <span
                          className="inline-block px-2 py-0.5 rounded-full text-[10px]"
                          style={{ background: 'rgba(138,148,166,0.08)', color: 'var(--cosmic-muted)' }}
                        >
                          NO
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Strength Bar Visualization */}
      <div
        className="rounded-2xl p-4"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--cosmic-muted)' }}>
          STRENGTH COMPARISON
        </h4>
        <div className="space-y-2">
          {PLANET_ORDER.map((planet) => {
            const ps = data.planets[planet];
            if (!ps) return null;
            const maxTotal = 400; // Max possible shadbala
            const width = Math.min(100, (ps.total_virupas / maxTotal) * 100);

            return (
              <div key={planet} className="flex items-center gap-3">
                <span className="w-16 text-xs font-medium text-right" style={{ color: 'var(--cosmic-text)' }}>
                  {PLANET_SYMBOLS[planet]} {planet}
                </span>
                <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'rgba(26,20,35,0.5)' }}>
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${width}%`,
                      background: ps.is_strong
                        ? 'var(--benefic-green)'
                        : ps.total_virupas >= 300
                        ? 'var(--cosmic-gold)'
                        : ps.total_virupas >= 200
                        ? '#eab308'
                        : 'var(--malefic-red)',
                    }}
                  />
                </div>
                <span className="w-14 text-xs font-mono text-right" style={{ color: 'var(--cosmic-muted)' }}>
                  {ps.total_virupas.toFixed(0)}V
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
