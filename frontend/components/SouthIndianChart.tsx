'use client';

import { useMemo } from 'react';

// ── Constants ──────────────────────────────────────────────
const SIGN_ABBREVS: Record<string, string> = {
  MESHA: 'Ar', VRISHABHA: 'Ta', MITHUNA: 'Ge', KARKA: 'Ca',
  SIMHA: 'Le', KANYA: 'Vi', TULA: 'Li', VRISHCHIKA: 'Sc',
  DHANUSHA: 'Sg', MAKARA: 'Cp', KUMBHA: 'Aq', MEENA: 'Pi',
};

const PLANET_ABBREVS: Record<string, string> = {
  SUN: 'Su', MOON: 'Mo', MARS: 'Ma', MERCURY: 'Me',
  JUPITER: 'Ju', VENUS: 'Ve', SATURN: 'Sa', RAHU: 'Ra', KETU: 'Ke',
};

const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
];

const DIVISIONAL_LABELS: Record<string, string> = {
  D1: 'Rashi (D-1)', D9: 'Navamsha (D-9)', D10: 'Dashamamsha (D-10)',
  D7: 'Saptamamsha (D-7)', D12: 'Dwadashamsha (D-12)', D16: 'Shodashamsha (D-16)',
  D24: 'Chaturvimshamsha (D-24)', D27: 'Bhamsha (D-27)', D30: 'Trishamsha (D-30)',
  D60: 'Shashtiamsha (D-60)',
};

interface PlanetInfo {
  sign: string;
  degree_in_sign: number;
}

interface SouthIndianChartProps {
  lagna: string;
  planetDetails: Record<string, PlanetInfo>;
  divisionalType?: string;
  className?: string;
}

// ── Grid layout: 4x4 with fixed sign positions ────────────
// South Indian chart has FIXED sign positions (not house-based)
// Signs go clockwise from top-left corner
const GRID_SIGNS: (string | null)[][] = [
  ['MEENA', 'MESHA', 'VRISHABHA', 'MITHUNA'],
  ['KUMBHA', null, null, 'KARKA'],
  ['MAKARA', null, null, 'SIMHA'],
  ['DHANUSHA', 'VRISHCHIKA', 'TULA', 'KANYA'],
];

const CELL_SIZE = 90;
const PADDING = 20;
const SVG_SIZE = CELL_SIZE * 4 + PADDING * 2;

export default function SouthIndianChart({
  lagna,
  planetDetails,
  divisionalType = 'D1',
  className = '',
}: SouthIndianChartProps) {
  // Group planets by sign
  const signPlanets = useMemo(() => {
    const groups: Record<string, { abbrev: string; full: string }[]> = {};
    for (const [planet, detail] of Object.entries(planetDetails)) {
      const sign = detail.sign;
      if (!sign) continue;
      const abbrev = PLANET_ABBREVS[planet] || planet.slice(0, 2);
      if (!groups[sign]) groups[sign] = [];
      groups[sign].push({ abbrev, full: planet });
    }
    return groups;
  }, [planetDetails]);

  const chartTitle = DIVISIONAL_LABELS[divisionalType] || divisionalType;

  return (
    <div className={`relative ${className}`}>
      <svg
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE + 30}`}
        className="w-full h-auto"
        style={{ maxWidth: '440px' }}
      >
        {/* Chart Title */}
        <text
          x={SVG_SIZE / 2}
          y={18}
          textAnchor="middle"
          fontSize="14"
          fontWeight="700"
          fontFamily="var(--font-playfair), Georgia, serif"
          fill="var(--cosmic-gold)"
          opacity={0.9}
        >
          {chartTitle}
        </text>

        <g transform={`translate(0, 30)`}>
          {/* Background */}
          <rect width={SVG_SIZE} height={SVG_SIZE} fill="transparent" />

          {/* Grid cells */}
          {GRID_SIGNS.flat().filter(Boolean).map((sign) => {
            if (!sign) return null;
            const rowIdx = GRID_SIGNS.findIndex(r => r.includes(sign));
            const colIdx = GRID_SIGNS[rowIdx].indexOf(sign);
            const x = PADDING + colIdx * CELL_SIZE;
            const y = PADDING + rowIdx * CELL_SIZE;
            const isLagna = sign === lagna;
            const planets = signPlanets[sign] || [];

            return (
              <g key={sign}>
                {/* Cell background */}
                <rect
                  x={x}
                  y={y}
                  width={CELL_SIZE}
                  height={CELL_SIZE}
                  fill={isLagna ? 'rgba(197, 168, 128, 0.08)' : 'transparent'}
                  stroke="var(--cosmic-gold)"
                  strokeWidth="0.8"
                  opacity={0.5}
                />

                {/* Sign name (top-left corner) */}
                <text
                  x={x + 6}
                  y={y + 12}
                  fontSize="8"
                  fontFamily="var(--font-inter), sans-serif"
                  fill="var(--cosmic-muted)"
                  opacity={0.6}
                >
                  {SIGN_ABBREVS[sign]}
                </text>

                {/* Lagna marker */}
                {isLagna && (
                  <text
                    x={x + CELL_SIZE - 6}
                    y={y + 12}
                    fontSize="8"
                    fontWeight="700"
                    fontFamily="var(--font-inter), sans-serif"
                    fill="var(--cosmic-gold)"
                    textAnchor="end"
                  >
                    ASC
                  </text>
                )}

                {/* Planets */}
                {planets.map((p, j) => (
                  <text
                    key={j}
                    x={x + CELL_SIZE / 2}
                    y={y + 35 + j * 14}
                    textAnchor="middle"
                    fontSize="11"
                    fontWeight="600"
                    fontFamily="var(--font-inter), system-ui, sans-serif"
                    fill="var(--cosmic-text)"
                  >
                    {p.abbrev}
                  </text>
                ))}
              </g>
            );
          })}

          {/* Outer border */}
          <rect
            x={PADDING}
            y={PADDING}
            width={CELL_SIZE * 4}
            height={CELL_SIZE * 4}
            fill="none"
            stroke="var(--cosmic-gold)"
            strokeWidth="1.5"
            opacity={0.7}
          />
        </g>
      </svg>
    </div>
  );
}
