'use client';

import { useMemo } from 'react';

// ── Sign & Planet Helpers ────────────────────────────────
const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
];

const SIGN_NAMES: Record<string, string> = {
  MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer',
  SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio',
  DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces',
};

const PLANET_ORDER = [
  'SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU',
];

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};

// ── Dignity color mapping ────────────────────────────────
function getDignityStyle(dignity: string): { color: string; bg: string } {
  const d = dignity.toLowerCase();
  if (d.includes('exalt')) {
    return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.1)' };
  }
  if (d.includes('own') || d.includes('moolatrikona') || d.includes('moola')) {
    return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.1)' };
  }
  if (d.includes('debil') || d.includes('enemy')) {
    return { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.1)' };
  }
  // Friendly, Neutral, and others
  return { color: 'var(--cosmic-muted)', bg: 'rgba(138, 148, 166, 0.08)' };
}

// ── Compute house number ─────────────────────────────────
function getHouseNumber(planetSign: string, lagnaSign: string): number {
  const pIdx = SIGN_ORDER.indexOf(planetSign);
  const lIdx = SIGN_ORDER.indexOf(lagnaSign);
  if (pIdx < 0 || lIdx < 0) return 0;
  return ((pIdx - lIdx) % 12 + 12) % 12 + 1;
}

interface PlanetInfo {
  sign: string;
  degree_in_sign: number;
  dignity?: string;
  element?: string;
  modality?: string;
}

interface PlanetaryStateInfo {
  state: string;  // "R", "D", "C", "S", etc.
  state_label: string;
  is_retrograde: boolean;
  is_combust: boolean;
  is_stationary: boolean;
  speed_class: string;
}

interface PlanetaryTableProps {
  lagna: string;
  planetDetails: Record<string, PlanetInfo>;
  dignityMap?: Record<string, string>;
  planetaryStates?: Record<string, PlanetaryStateInfo>;
  showState?: boolean;
}

interface TableRow {
  planet: string;
  symbol: string;
  sign: string;
  signName: string;
  degree: number;
  house: number;
  dignity: string;
  dignityStyle: { color: string; bg: string };
  state?: string;
  stateLabel?: string;
}

// State badge colors
function getStateBadgeStyle(state: string): { color: string; bg: string; label: string } {
  if (state.includes('R')) return { color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)', label: 'R' };
  if (state.includes('C')) return { color: '#fb923c', bg: 'rgba(249, 115, 22, 0.15)', label: 'C' };
  if (state.includes('S')) return { color: '#facc15', bg: 'rgba(250, 204, 21, 0.15)', label: 'S' };
  if (state.includes('F')) return { color: '#4ade80', bg: 'rgba(74, 222, 128, 0.15)', label: 'F' };
  if (state.includes('L')) return { color: '#a78bfa', bg: 'rgba(167, 139, 250, 0.15)', label: 'L' };
  return { color: 'var(--benefic-green)', bg: 'rgba(74, 222, 128, 0.1)', label: 'D' };
}

export default function PlanetaryTable({
  lagna,
  planetDetails,
  dignityMap = {},
  planetaryStates,
  showState = false,
}: PlanetaryTableProps) {
  const rows: TableRow[] = useMemo(() => {
    return PLANET_ORDER
      .filter((p) => planetDetails[p])
      .map((planet) => {
        const detail = planetDetails[planet];
        const sign = detail.sign;
        const signName = SIGN_NAMES[sign] || sign;
        const house = getHouseNumber(sign, lagna);
        const dignity = dignityMap[planet] || detail.dignity || 'Neutral';
        const dignityStyle = getDignityStyle(dignity);
        const stateInfo = planetaryStates?.[planet];

        return {
          planet,
          symbol: PLANET_SYMBOLS[planet] || '',
          sign,
          signName,
          degree: detail.degree_in_sign,
          house,
          dignity,
          dignityStyle,
          state: stateInfo?.state || '',
          stateLabel: stateInfo?.state_label || '',
        };
      });
  }, [lagna, planetDetails, dignityMap]);

  if (rows.length === 0) {
    return (
      <div className="text-center py-8" style={{ color: 'var(--cosmic-muted)' }}>
        <p className="text-sm">No planetary data available.</p>
        <p className="text-xs mt-1">Cast a chart to see planetary positions.</p>
      </div>
    );
  }

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: 'var(--glass-bg)',
        backdropFilter: 'blur(16px) saturate(1.2)',
        border: '1px solid var(--glass-border)',
      }}
    >
      <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--glass-border)' }}>
        <h3
          className="text-sm font-semibold tracking-wide"
          style={{ color: 'var(--cosmic-gold)' }}
        >
          PLANETARY POSITIONS
        </h3>
        <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
          Lagna: <strong style={{ color: 'var(--cosmic-gold)' }}>{SIGN_NAMES[lagna] || lagna}</strong>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr
              className="text-xs uppercase tracking-wider"
              style={{ color: 'var(--cosmic-muted)' }}
            >
              <th className="px-4 py-2.5 text-left font-medium">Planet</th>
              <th className="px-3 py-2.5 text-left font-medium">Sign</th>
              <th className="px-3 py-2.5 text-right font-medium">Degree</th>
              <th className="px-3 py-2.5 text-center font-medium">House</th>
              {showState && <th className="px-3 py-2.5 text-center font-medium">State</th>}
              <th className="px-4 py-2.5 text-left font-medium">Dignity</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.planet}
                className="transition-colors duration-150"
                style={{
                  borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.background = 'rgba(197, 168, 128, 0.04)';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.background = 'transparent';
                }}
              >
                <td className="px-4 py-2.5">
                  <span className="inline-flex items-center gap-2">
                    <span className="text-base" style={{ opacity: 0.7 }}>
                      {row.symbol}
                    </span>
                    <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>
                      {row.planet}
                    </span>
                  </span>
                </td>
                <td className="px-3 py-2.5" style={{ color: 'var(--cosmic-text)' }}>
                  {row.signName}
                </td>
                <td className="px-3 py-2.5 text-right font-mono text-xs" style={{ color: 'var(--cosmic-muted)' }}>
                  {row.degree.toFixed(2)}°
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
                    {row.house}
                  </span>
                </td>
                {showState && (
                  <td className="px-3 py-2.5 text-center">
                    {row.state ? (
                      <span
                        className="inline-flex items-center gap-1"
                      >
                        {row.state.split('/').map((s, si) => {
                          const badgeStyle = getStateBadgeStyle(s);
                          return (
                            <span
                              key={si}
                              className="inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold"
                              style={{ background: badgeStyle.bg, color: badgeStyle.color, border: `1px solid ${badgeStyle.color}30` }}
                              title={row.stateLabel}
                            >
                              {badgeStyle.label}
                            </span>
                          );
                        })}
                      </span>
                    ) : (
                      <span className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>—</span>
                    )}
                  </td>
                )}
                <td className="px-4 py-2.5">
                  <span
                    className="inline-block px-2.5 py-0.5 rounded-md text-xs font-medium"
                    style={{
                      color: row.dignityStyle.color,
                      background: row.dignityStyle.bg,
                      border: `1px solid ${row.dignityStyle.color}20`,
                    }}
                  >
                    {row.dignity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
