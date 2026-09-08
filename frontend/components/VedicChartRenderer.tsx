'use client';

import { useState } from 'react';

// ── Types ──────────────────────────────────────────────────
interface PlanetPosition {
  planet: string;
  sign: string;
  house: number;
  degree?: number;
  retrograde?: boolean;
}

interface VedicChartProps {
  planets: PlanetPosition[];
  lagna?: string;
  title?: string;
  style?: 'north' | 'south';
}

// ── Constants ──────────────────────────────────────────────
const SIGN_NAMES: Record<string, string> = {
  MESHA: 'Ari', VRISHABHA: 'Tau', MITHUNA: 'Gem', KARKA: 'Can',
  SIMHA: 'Leo', KANYA: 'Vir', TULA: 'Lib', VRISHCHIKA: 'Sco',
  DHANUSHA: 'Sag', MAKARA: 'Cap', KUMBHA: 'Aqu', MEENA: 'Pis',
};

const SIGN_FULL_NAMES: Record<string, string> = {
  MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer',
  SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio',
  DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces',
};

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: '☉', MOON: '☽', MARS: '♂', MERCURY: '☿',
  JUPITER: '♃', VENUS: '♀', SATURN: '♄', RAHU: '☊', KETU: '☋',
};

const PLANET_COLORS: Record<string, string> = {
  SUN: '#fbbf24', MOON: '#93c5fd', MARS: '#ef4444', MERCURY: '#22d3ee',
  JUPITER: '#34d399', VENUS: '#f472b6', SATURN: '#94a3b8', RAHU: '#a78bfa', KETU: '#c084fc',
};

const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
];

// ── North Indian (Diamond) Chart ──────────────────────────
// Layout: 12 houses in a diamond pattern
// House positions (SVG coordinates for a 400x400 chart):
//  1 (Asc) at top center, then clockwise
const NORTH_INDIAN_HOUSES = [
  { x: 200, y: 40, w: 80, h: 40 },    // House 1 (top)
  { x: 280, y: 80, w: 80, h: 40 },    // House 2
  { x: 320, y: 120, w: 80, h: 40 },   // House 3
  { x: 320, y: 200, w: 80, h: 40 },   // House 4 (right)
  { x: 320, y: 280, w: 80, h: 40 },   // House 5
  { x: 280, y: 320, w: 80, h: 40 },   // House 6
  { x: 200, y: 360, w: 80, h: 40 },   // House 7 (bottom)
  { x: 120, y: 320, w: 80, h: 40 },   // House 8
  { x: 80, y: 280, w: 80, h: 40 },    // House 9
  { x: 80, y: 200, w: 80, h: 40 },    // House 10 (left)
  { x: 80, y: 120, w: 80, h: 40 },    // House 11
  { x: 120, y: 80, w: 80, h: 40 },    // House 12
];

// Sign positions for North Indian (houses rotate based on lagna)
function getNorthIndianSignPosition(house: number): { x: number; y: number } {
  const pos = NORTH_INDIAN_HOUSES[(house - 1) % 12];
  return { x: pos.x, y: pos.y };
}

function NorthIndianChart({ planets, lagna }: { planets: PlanetPosition[]; lagna?: string }) {
  // Group planets by house
  const housePlanets: Record<number, PlanetPosition[]> = {};
  for (const p of planets) {
    if (!housePlanets[p.house]) housePlanets[p.house] = [];
    housePlanets[p.house].push(p);
  }

  // Get lagna sign index
  const lagnaIdx = lagna ? SIGN_ORDER.indexOf(lagna) : 0;

  return (
    <svg viewBox="0 0 400 400" className="w-full max-w-[400px] mx-auto">
      {/* Background */}
      <rect x="0" y="0" width="400" height="400" fill="rgba(26,20,35,0.8)" rx="12" />

      {/* Diamond shape */}
      <polygon
        points="200,20 380,200 200,380 20,200"
        fill="none"
        stroke="rgba(197,168,128,0.3)"
        strokeWidth="2"
      />

      {/* Cross lines */}
      <line x1="200" y1="20" x2="200" y2="380" stroke="rgba(197,168,128,0.15)" strokeWidth="1" />
      <line x1="20" y1="200" x2="380" y2="200" stroke="rgba(197,168,128,0.15)" strokeWidth="1" />

      {/* Diagonal lines */}
      <line x1="110" y1="110" x2="290" y2="290" stroke="rgba(197,168,128,0.1)" strokeWidth="1" />
      <line x1="290" y1="110" x2="110" y2="290" stroke="rgba(197,168,128,0.1)" strokeWidth="1" />

      {/* House labels and planets */}
      {Array.from({ length: 12 }, (_, i) => {
        const house = i + 1;
        const signIdx = (lagnaIdx + i) % 12;
        const sign = SIGN_ORDER[signIdx];
        const pos = NORTH_INDIAN_HOUSES[i];
        const hPlanets = housePlanets[house] || [];
        const isLagna = house === 1;

        return (
          <g key={house}>
            {/* House box */}
            <rect
              x={pos.x - 35}
              y={pos.y - 15}
              width="70"
              height="30"
              fill={isLagna ? 'rgba(197,168,128,0.15)' : 'rgba(26,20,35,0.6)'}
              stroke={isLagna ? 'rgba(197,168,128,0.4)' : 'rgba(197,168,128,0.15)'}
              strokeWidth="1"
              rx="4"
            />

            {/* Sign name */}
            <text
              x={pos.x}
              y={pos.y - 4}
              textAnchor="middle"
              fontSize="8"
              fill="rgba(197,168,128,0.6)"
              fontFamily="var(--font-inter), sans-serif"
            >
              {SIGN_NAMES[sign]}
            </text>

            {/* Planets */}
            {hPlanets.map((p, pi) => (
              <text
                key={pi}
                x={pos.x}
                y={pos.y + 8 + pi * 10}
                textAnchor="middle"
                fontSize="9"
                fill={PLANET_COLORS[p.planet] || '#fff'}
                fontFamily="var(--font-inter), sans-serif"
                fontWeight="bold"
              >
                {PLANET_SYMBOLS[p.planet] || p.planet}
                {p.retrograde ? '℃' : ''}
              </text>
            ))}

            {/* Lagna marker */}
            {isLagna && (
              <text
                x={pos.x}
                y={pos.y - 20}
                textAnchor="middle"
                fontSize="8"
                fill="var(--cosmic-gold)"
                fontFamily="var(--font-inter), sans-serif"
                fontWeight="bold"
              >
                ASC
              </text>
            )}
          </g>
        );
      })}

      {/* Center label */}
      <text x="200" y="195" textAnchor="middle" fontSize="10" fill="rgba(197,168,128,0.4)" fontFamily="var(--font-inter), sans-serif">
        North Indian
      </text>
      <text x="200" y="210" textAnchor="middle" fontSize="8" fill="rgba(197,168,128,0.3)" fontFamily="var(--font-inter), sans-serif">
        (Diamond Style)
      </text>
    </svg>
  );
}

// ── South Indian (Square) Chart ───────────────────────────
// Layout: 4x4 grid with fixed sign positions
// Signs go clockwise from top-left: Pisces, Aries, Taurus, Gemini...
const SOUTH_INDIAN_GRID = [
  // Row 0: Houses 12, 1, 2, 3
  [
    { sign: 'MEENA', row: 0, col: 0 },
    { sign: 'MESHA', row: 0, col: 1 },
    { sign: 'VRISHABHA', row: 0, col: 2 },
    { sign: 'MITHUNA', row: 0, col: 3 },
  ],
  // Row 1: Houses 11, (center), (center), 4
  [
    { sign: 'KUMBHA', row: 1, col: 0 },
    { sign: '', row: 1, col: 1 }, // Center
    { sign: '', row: 1, col: 2 }, // Center
    { sign: 'KARKA', row: 1, col: 3 },
  ],
  // Row 2: Houses 10, (center), (center), 5
  [
    { sign: 'MAKARA', row: 2, col: 0 },
    { sign: '', row: 2, col: 1 }, // Center
    { sign: '', row: 2, col: 2 }, // Center
    { sign: 'SIMHA', row: 2, col: 3 },
  ],
  // Row 3: Houses 9, 8, 7, 6
  [
    { sign: 'DHANUSHA', row: 3, col: 0 },
    { sign: 'VRISHCHIKA', row: 3, col: 1 },
    { sign: 'TULA', row: 3, col: 2 },
    { sign: 'KANYA', row: 3, col: 3 },
  ],
];

function SouthIndianChart({ planets, lagna }: { planets: PlanetPosition[]; lagna?: string }) {
  // Group planets by sign
  const signPlanets: Record<string, PlanetPosition[]> = {};
  for (const p of planets) {
    if (!signPlanets[p.sign]) signPlanets[p.sign] = [];
    signPlanets[p.sign].push(p);
  }

  const cellSize = 90;
  const padding = 10;

  return (
    <svg viewBox="0 0 400 400" className="w-full max-w-[400px] mx-auto">
      {/* Background */}
      <rect x="0" y="0" width="400" height="400" fill="rgba(26,20,35,0.8)" rx="12" />

      {/* Grid cells */}
      {SOUTH_INDIAN_GRID.flat().filter(c => c.sign).map((cell) => {
        const x = padding + cell.col * cellSize;
        const y = padding + cell.row * cellSize;
        const sPlanets = signPlanets[cell.sign] || [];
        const isLagna = cell.sign === lagna;

        return (
          <g key={cell.sign}>
            <rect
              x={x}
              y={y}
              width={cellSize}
              height={cellSize}
              fill={isLagna ? 'rgba(197,168,128,0.15)' : 'rgba(26,20,35,0.6)'}
              stroke={isLagna ? 'rgba(197,168,128,0.4)' : 'rgba(197,168,128,0.15)'}
              strokeWidth="1"
              rx="4"
            />

            {/* Sign name */}
            <text
              x={x + cellSize / 2}
              y={y + 14}
              textAnchor="middle"
              fontSize="9"
              fill="rgba(197,168,128,0.6)"
              fontFamily="var(--font-inter), sans-serif"
            >
              {SIGN_NAMES[cell.sign]}
            </text>

            {/* Planets */}
            {sPlanets.map((p, pi) => (
              <text
                key={pi}
                x={x + cellSize / 2}
                y={y + 30 + pi * 14}
                textAnchor="middle"
                fontSize="11"
                fill={PLANET_COLORS[p.planet] || '#fff'}
                fontFamily="var(--font-inter), sans-serif"
                fontWeight="bold"
              >
                {PLANET_SYMBOLS[p.planet] || p.planet}
                {p.retrograde ? '℃' : ''}
              </text>
            ))}

            {/* Lagna marker */}
            {isLagna && (
              <text
                x={x + 8}
                y={y + cellSize - 6}
                fontSize="8"
                fill="var(--cosmic-gold)"
                fontFamily="var(--font-inter), sans-serif"
                fontWeight="bold"
              >
                ASC
              </text>
            )}
          </g>
        );
      })}

      {/* Center area */}
      <rect
        x={padding + cellSize}
        y={padding + cellSize}
        width={cellSize * 2}
        height={cellSize * 2}
        fill="rgba(26,20,35,0.4)"
        stroke="rgba(197,168,128,0.1)"
        strokeWidth="1"
        rx="8"
      />

      {/* Center label */}
      <text x="200" y="195" textAnchor="middle" fontSize="10" fill="rgba(197,168,128,0.4)" fontFamily="var(--font-inter), sans-serif">
        South Indian
      </text>
      <text x="200" y="210" textAnchor="middle" fontSize="8" fill="rgba(197,168,128,0.3)" fontFamily="var(--font-inter), sans-serif">
        (Square Style)
      </text>
    </svg>
  );
}

// ── Main Component ─────────────────────────────────────────
export default function VedicChartRenderer({ planets, lagna, title, style: initialStyle }: VedicChartProps) {
  const [chartStyle, setChartStyle] = useState<'north' | 'south'>(initialStyle || 'north');

  return (
    <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold flex items-center gap-2" style={{ color: 'var(--cosmic-gold)' }}>
          <span className="text-lg">🔮</span> {title || 'Vedic Chart'}
        </h3>
        <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'rgba(26,20,35,0.5)' }}>
          <button
            type="button"
            onClick={() => setChartStyle('north')}
            className="px-3 py-1 rounded-md text-sm font-medium transition-all"
            style={{
              background: chartStyle === 'north' ? 'rgba(197,168,128,0.15)' : 'transparent',
              color: chartStyle === 'north' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
            }}
          >
            North (Diamond)
          </button>
          <button
            type="button"
            onClick={() => setChartStyle('south')}
            className="px-3 py-1 rounded-md text-sm font-medium transition-all"
            style={{
              background: chartStyle === 'south' ? 'rgba(197,168,128,0.15)' : 'transparent',
              color: chartStyle === 'south' ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
            }}
          >
            South (Square)
          </button>
        </div>
      </div>

      {chartStyle === 'north' ? (
        <NorthIndianChart planets={planets} lagna={lagna} />
      ) : (
        <SouthIndianChart planets={planets} lagna={lagna} />
      )}

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {planets.map((p) => (
          <div key={p.planet} className="flex items-center gap-1 text-[10px]" style={{ color: PLANET_COLORS[p.planet] || '#fff' }}>
            <span>{PLANET_SYMBOLS[p.planet]}</span>
            <span>{p.planet}</span>
            {p.retrograde && <span style={{ color: '#ef4444' }}>R</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
