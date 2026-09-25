'use client';

// ── SAVViewer — Phase 5B Ashtakavarga report visualizer ──────────────────
// Pure presentation over the deterministic report emitted by
// jrs.calculations.ashtakavarga (BAV 0-8 Rekhas, SAV 0-56, Shodhita SAV,
// Shodhita Pinda). No data fetching, no state dependence (Phase 5 exit
// criterion: no calculation module depends on frontend state).

import { useMemo, useState } from 'react';

export const SIGN_ORDER = [
  'MESHA',
  'VRISHABHA',
  'MITHUNA',
  'KARKA',
  'SIMHA',
  'KANYA',
  'TULA',
  'VRISHCHIKA',
  'DHANUSHA',
  'MAKARA',
  'KUMBHA',
  'MEENA',
] as const;

export const ANCHOR_ORDER = [
  'SUN',
  'MOON',
  'MARS',
  'MERCURY',
  'JUPITER',
  'VENUS',
  'SATURN',
  'LAGNA',
] as const;

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉',
  MOON: '☽',
  MARS: '♂',
  MERCURY: '☿',
  JUPITER: '♃',
  VENUS: '♀',
  SATURN: '♄',
  LAGNA: 'Λ',
};

/** Report shape serialized by ashtakavarga_to_dict(). */
export interface AshtakavargaReport {
  version: string;
  anchor_signs: Record<string, string>;
  fact_ids: string[];
  bav: Record<string, number[]>;
  sav: number[];
  shodhita_bav: Record<string, number[]>;
  shodhita_sav: number[];
  pinda: Record<
    string,
    { rashi_pinda: number; graha_pinda: number; shodhya_pinda: number }
  >;
}

export interface SAVViewerProps {
  report: AshtakavargaReport | null;
  /** Optional fixture label (header). */
  subject?: string;
  /** Show the Shodhita (reduced) SAV row instead of raw SAV. Default false. */
  showShodhita?: boolean;
  /** Hide the Pinda table for compact layouts. Default false. */
  hidePinda?: boolean;
}

/** Classical SAV banding: strong >= 30, good >= 28, average >= 25, weak < 25. */
export function savBand(value: number): {
  color: string;
  bg: string;
  label: string;
} {
  if (value >= 30)
    return {
      color: 'var(--benefic-green, #10b981)',
      bg: 'rgba(16, 185, 129, 0.10)',
      label: 'Strong',
    };
  if (value >= 28)
    return {
      color: 'var(--cosmic-gold, #c5a880)',
      bg: 'rgba(197, 168, 128, 0.08)',
      label: 'Good',
    };
  if (value >= 25)
    return {
      color: '#eab308',
      bg: 'rgba(234, 179, 8, 0.05)',
      label: 'Average',
    };
  return {
    color: 'var(--malefic-red, #ef4444)',
    bg: 'rgba(239, 68, 68, 0.06)',
    label: 'Weak',
  };
}

/** BAV cell tint: 7-8 excellent, 5-6 favourable, 4 neutral, 2-3 low, 0-1 weak. */
export function bavCellColor(value: number): {
  color: string;
  bg: string;
} {
  if (value === 0)
    return { color: 'var(--cosmic-muted, #6b7280)', bg: 'transparent' };
  if (value >= 7)
    return {
      color: 'var(--benefic-green, #10b981)',
      bg: 'rgba(16, 185, 129, 0.16)',
    };
  if (value >= 5)
    return {
      color: 'var(--benefic-green, #10b981)',
      bg: 'rgba(16, 185, 129, 0.10)',
    };
  if (value === 4)
    return {
      color: 'var(--cosmic-gold, #c5a880)',
      bg: 'rgba(197, 168, 128, 0.07)',
    };
  if (value >= 2)
    return { color: '#eab308', bg: 'rgba(234, 179, 8, 0.05)' };
  return {
    color: 'var(--malefic-red, #ef4444)',
    bg: 'rgba(239, 68, 68, 0.05)',
  };
}

const glassStyle: React.CSSProperties = {
  background: 'var(--glass-bg, rgba(17, 24, 39, 0.6))',
  border: '1px solid var(--glass-border, rgba(197, 168, 128, 0.18))',
};

export default function SAVViewer({
  report,
  subject,
  showShodhita = false,
  hidePinda = false,
}: SAVViewerProps) {
  const [showShodhitaState, setShowShodhitaState] = useState(showShodhita);

  const savRow = useMemo(
    () => (showShodhitaState ? report?.shodhita_sav : report?.sav),
    [report, showShodhitaState],
  );
  const savTotal = useMemo(
    () => (savRow ? savRow.reduce((a, b) => a + b, 0) : 0),
    [savRow],
  );

  if (!report || !report.bav) {
    return (
      <div
        data-testid="sav-viewer-empty"
        className="rounded-2xl p-8 text-center"
        style={glassStyle}
      >
        <p className="text-sm" style={{ color: 'var(--cosmic-muted, #9ca3af)' }}>
          No Ashtakavarga report available (compute via
          jrs.calculations.ashtakavarga or enable ashta_scoring_enabled).
        </p>
      </div>
    );
  }

  return (
    <section
      data-testid="sav-viewer"
      aria-label="Sarvashtakavarga matrix"
      className="rounded-2xl p-6 space-y-4"
      style={glassStyle}
    >
      <header className="flex items-baseline justify-between">
        <h3 className="text-lg font-semibold">
          Ashtakavarga
          {subject ? (
            <span
              className="ml-2 text-sm font-normal"
              style={{ color: 'var(--cosmic-muted, #9ca3af)' }}
            >
              {subject} · v{report.version}
            </span>
          ) : null}
        </h3>
        <button
          type="button"
          data-testid="sav-toggle-shodhita"
          aria-pressed={showShodhitaState}
          onClick={() => setShowShodhitaState((v) => !v)}
          className="rounded-lg px-3 py-1 text-xs"
          style={{
            border: '1px solid var(--glass-border, rgba(197,168,128,0.3))',
            color: showShodhitaState
              ? 'var(--cosmic-gold, #c5a880)'
              : 'var(--cosmic-muted, #9ca3af)',
          }}
        >
          {showShodhitaState ? 'Shodhita SAV' : 'Raw SAV'}
        </button>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="sav-matrix">
          <thead>
            <tr>
              <th className="text-left px-2 py-1">Sign</th>
              {ANCHOR_ORDER.map((anchor) => (
                <th key={anchor} className="px-2 py-1" title={anchor}>
                  {PLANET_SYMBOLS[anchor] ?? anchor}
                </th>
              ))}
              <th className="px-2 py-1">SAV</th>
            </tr>
          </thead>
          <tbody>
            {SIGN_ORDER.map((sign, idx) => {
              const savValue = savRow ? savRow[idx] : 0;
              const band = savBand(savValue);
              return (
                <tr key={sign} data-sign={sign}>
                  <td
                    className="text-left px-2 py-1 whitespace-nowrap"
                    style={{ color: 'var(--cosmic-muted, #9ca3af)' }}
                  >
                    {sign}
                  </td>
                  {ANCHOR_ORDER.map((anchor) => {
                    const bindus = report.bav[anchor]?.[idx] ?? 0;
                    const cell = bavCellColor(bindus);
                    return (
                      <td
                        key={anchor}
                        data-testid={`bav-${anchor}-${sign}`}
                        className="text-center px-2 py-1 rounded-md"
                        style={{ color: cell.color, background: cell.bg }}
                        title={`${anchor} in ${sign}: ${bindus} bindus (BAV 0-8)`}
                      >
                        {bindus}
                      </td>
                    );
                  })}
                  <td
                    data-testid={`sav-${sign}`}
                    className="text-center px-2 py-1 rounded-md font-semibold"
                    style={{
                      color: band.color,
                      background: band.bg,
                    }}
                    title={`${sign}: SAV ${savValue} (${band.label}) — total ${savTotal}`}
                  >
                    {savValue}
                  </td>
                </tr>
              );
            })}
            <tr data-testid="sav-total-row">
              <td
                className="text-left px-2 py-1 font-semibold"
                style={{ color: 'var(--cosmic-gold, #c5a880)' }}
              >
                TOTAL
              </td>
              {ANCHOR_ORDER.map((anchor) => {
                const row = report.bav[anchor] ?? [];
                const total = row.reduce((a, b) => a + b, 0);
                return (
                  <td key={anchor} className="text-center px-2 py-1 font-semibold">
                    {total}
                  </td>
                );
              })}
              <td className="text-center px-2 py-1 font-semibold">{savTotal}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {!hidePinda && report.pinda ? (
        <div data-testid="sav-pinda" className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {ANCHOR_ORDER.map((anchor) => {
            const p = report.pinda[anchor];
            if (!p) return null;
            return (
              <div
                key={anchor}
                className="rounded-xl px-3 py-2"
                style={{
                  background: 'rgba(197, 168, 128, 0.04)',
                  border: '1px solid var(--glass-border, rgba(197,168,128,0.12))',
                }}
                title={`${anchor}: Rashi ${p.rashi_pinda} + Graha ${p.graha_pinda} = Shodhya ${p.shodhya_pinda}`}
              >
                <div
                  className="text-xs"
                  style={{ color: 'var(--cosmic-muted, #9ca3af)' }}
                >
                  {anchor}
                </div>
                <div className="font-mono text-sm">
                  {p.rashi_pinda} + {p.graha_pinda} ={' '}
                  <span style={{ color: 'var(--cosmic-gold, #c5a880)' }}>
                    {p.shodhya_pinda}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
