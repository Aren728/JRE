'use client';

import { useMemo } from 'react';

// ── Sign name abbreviations ──────────────────────────────
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
  D1: 'Rashi (D-1)',
  D2: 'Hora (D-2)',
  D3: 'Drekkana (D-3)',
  D4: 'Chaturthamsha (D-4)',
  D7: 'Saptamamsha (D-7)',
  D9: 'Navamsha (D-9)',
  D10: 'Dashamamsha (D-10)',
  D12: 'Dwadashamsha (D-12)',
  D16: 'Shodashamsha (D-16)',
  D24: 'Chaturvimshamsha (D-24)',
  D27: 'Bhamsha (D-27)',
  D30: 'Trishamsha (D-30)',
  D40: 'Chaturashitamsha (D-40)',
  D45: 'Khavedamsha (D-45)',
  D60: 'Shashtiamsha (D-60)',
};

interface PlanetInfo {
  sign: string;
  degree_in_sign: number;
}

interface NorthIndianChartProps {
  lagna: string;
  planetDetails: Record<string, PlanetInfo>;
  divisionalType?: string;
  className?: string;
}

// ── Compute house number from sign and lagna ──────────────
function getHouseNumber(planetSign: string, lagnaSign: string): number {
  const pIdx = SIGN_ORDER.indexOf(planetSign);
  const lIdx = SIGN_ORDER.indexOf(lagnaSign);
  if (pIdx < 0 || lIdx < 0) return 0;
  return ((pIdx - lIdx) % 12 + 12) % 12 + 1;
}

// ── Chart geometry constants ─────────────────────────────
const SIZE = 400;
const CX = SIZE / 2;
const CY = SIZE / 2;
const R = 185; // half-diagonal of the diamond

// Boundary points at 30° intervals (counter-clockwise from top)
function boundaryPoint(angleDeg: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180;
  const sinA = Math.abs(Math.sin(rad));
  const cosA = Math.abs(Math.cos(rad));
  const denom = Math.max(sinA, cosA);
  const r = denom > 0 ? R / denom : R;
  return [CX + r * Math.sin(rad), CY - r * Math.cos(rad)];
}

// 12 boundary points
const BOUNDARY_POINTS: [number, number][] = Array.from({ length: 12 }, (_, i) =>
  boundaryPoint(i * 30)
);

// Center of each house section (centroid of triangle)
function houseCenter(houseIdx: number): [number, number] {
  const p1 = BOUNDARY_POINTS[(houseIdx + 11) % 12];
  const p2 = BOUNDARY_POINTS[houseIdx];
  return [(CX + p1[0] + p2[0]) / 3, (CY + p1[1] + p2[1]) / 3];
}

// House centers precomputed
const HOUSE_CENTERS = Array.from({ length: 12 }, (_, i) => houseCenter(i));

// ── SVG Component ────────────────────────────────────────
export default function NorthIndianChart({
  lagna,
  planetDetails,
  divisionalType = 'D1',
  className = '',
}: NorthIndianChartProps) {
  // Group planets by house number
  const housePlanets = useMemo(() => {
    const groups: Record<number, { abbrev: string; full: string }[]> = {};
    for (const [planet, detail] of Object.entries(planetDetails)) {
      const house = getHouseNumber(detail.sign, lagna);
      if (house < 1 || house > 12) continue;
      const abbrev = PLANET_ABBREVS[planet] || planet.slice(0, 2);
      if (!groups[house]) groups[house] = [];
      groups[house].push({ abbrev, full: planet });
    }
    return groups;
  }, [lagna, planetDetails]);

  // Lagna house number (always 1)
  const lagnaHouse = 1;

  // Build the 12 house polygons (paths from center to boundary arc)
  const housePolygons = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const p1 = BOUNDARY_POINTS[(i + 11) % 12];
      const p2 = BOUNDARY_POINTS[i];
      return `M ${CX} ${CY} L ${p1[0]} ${p1[1]} L ${p2[0]} ${p2[1]} Z`;
    });
  }, []);

  const chartTitle = DIVISIONAL_LABELS[divisionalType] || divisionalType;

  return (
    <div className={`relative ${className}`}>
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE + 30}`}
        className="w-full h-auto"
        style={{ maxWidth: '440px' }}
      >
        {/* Chart Title */}
        <text
          x={CX}
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

        {/* Offset drawing area down to make room for title */}
        <g transform="translate(0, 30)">
          {/* Background */}
          <rect width={SIZE} height={SIZE} fill="transparent" />

          {/* House sections */}
          {housePolygons.map((d, i) => {
            const isLagna = i + 1 === lagnaHouse;
            return (
              <path
                key={`house-${i}`}
                d={d}
                fill={isLagna ? 'rgba(197, 168, 128, 0.06)' : 'transparent'}
                stroke="var(--cosmic-gold)"
                strokeWidth="0.8"
                opacity={0.5}
              />
            );
          })}

          {/* Outer diamond border */}
          <polygon
            points={BOUNDARY_POINTS.map((p) => p.join(',')).join(' ')}
            fill="none"
            stroke="var(--cosmic-gold)"
            strokeWidth="1.5"
            opacity={0.7}
          />

          {/* House numbers */}
          {Array.from({ length: 12 }, (_, i) => {
            const [cx, cy] = HOUSE_CENTERS[i];
            const houseNum = i + 1;
            const isLagna = houseNum === lagnaHouse;
            return (
              <text
                key={`hnum-${i}`}
                x={cx}
                y={cy - (housePlanets[houseNum]?.length ? 8 : 0)}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={isLagna ? '11' : '9'}
                fontWeight={isLagna ? '700' : '400'}
                fontFamily="var(--font-playfair), Georgia, serif"
                fill={isLagna ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)'}
                opacity={isLagna ? 0.9 : 0.5}
              >
                {isLagna ? `${houseNum} ASC` : houseNum}
              </text>
            );
          })}

          {/* Planet labels */}
          {Object.entries(housePlanets).map(([houseStr, planets]) => {
            const houseNum = parseInt(houseStr);
            const [cx, cy] = HOUSE_CENTERS[houseNum - 1];
            return planets.map((p, j) => (
              <text
                key={`planet-${houseNum}-${j}`}
                x={cx}
                y={cy + 4 + j * 13}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="11"
                fontWeight="600"
                fill="var(--cosmic-text)"
                fontFamily="var(--font-inter), system-ui, sans-serif"
              >
                {p.abbrev}
              </text>
            ));
          })}

          {/* Center dot */}
          <circle cx={CX} cy={CY} r="2" fill="var(--cosmic-gold)" opacity={0.6} />
        </g>
      </svg>
    </div>
  );
}
