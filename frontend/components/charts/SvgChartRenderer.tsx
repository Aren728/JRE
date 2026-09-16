"use client";

import React, { useState } from "react";

export interface PlanetPosition {
  name: string;
  house?: number;
  sign?: number | string;
  longitude?: number;
  isRetrograde?: boolean;
  degree?: number;
  minute?: number;
  dignity?: "exalted" | "debilitated" | "own" | "friendly" | "enemy" | "neutral" | string;
  nakshatra?: string;
}

export interface AspectLine {
  sourcePlanet: string;
  targetPlanet: string;
  type: string;
  angle: number;
}

export interface ChartData {
  ascendant: number;
  ascendantSign?: number;
  chartStyle?: string;
  vargaType?: string;
  planets: PlanetPosition[];
  planet_details: Record<string, PlanetPosition>;
}

export interface SvgChartRendererProps {
  data?: ChartData;
  planets?: PlanetPosition[];
  chartData?: PlanetPosition[];
  title?: string;
  style?: "NORTH_INDIAN" | "SOUTH_INDIAN" | "GRID";
  chartStyle?: "NORTH_INDIAN" | "SOUTH_INDIAN" | "GRID";
  vargaType?: string;
  showTransits?: boolean;
  transitPlanets?: Array<{ name: string; house: number; longitude: number }>;
  onPlanetClick?: (planetName: string) => void;
  onPlanetSelect?: (planetName: string) => void;
  selectedPlanet?: string | null;
  aspects?: AspectLine[];
  onAspectClick?: (aspect: AspectLine) => void;
  showAspectLines?: boolean;
  width?: number;
  height?: number;
}

export const SIGN_ABBREVS: Record<number, string> = {
  1: 'Ar', 2: 'Ta', 3: 'Ge', 4: 'Ca', 5: 'Le', 6: 'Vi',
  7: 'Li', 8: 'Sc', 9: 'Sg', 10: 'Cp', 11: 'Aq', 12: 'Pi',
};

const Varga_LABELS: Record<string, string> = {
  D1: 'Rashi (D-1)',
  D9: 'Navamsha (D-9)',
  D10: 'Dashamamsha (D-10)',
  D60: 'Shashtiamsha (D-60)',
};

export const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "Su",
  Moon: "Mo",
  Mars: "Ma",
  Mercury: "Me",
  Jupiter: "Ju",
  Venus: "Ve",
  Saturn: "Sa",
  Rahu: "Ra",
  Ketu: "Ke",
};

export function generateDemoChartData(
  ascendantSign: number = 1,
  chartStyle: string = "NORTH_INDIAN",
  vargaType: string = "D1"
): ChartData {
  const defaultPlanets: PlanetPosition[] = [
    { name: "Sun", house: ((ascendantSign - 1 + 0) % 12) + 1, sign: ascendantSign, degree: 15, minute: 30, dignity: "own", nakshatra: "Krittika" },
    { name: "Moon", house: ((ascendantSign - 1 + 1) % 12) + 1, sign: ((ascendantSign + 0) % 12) + 1, degree: 10, minute: 20, dignity: "friendly", nakshatra: "Rohini" },
    { name: "Mars", house: ((ascendantSign - 1 + 2) % 12) + 1, sign: ((ascendantSign + 1) % 12) + 1, degree: 5, minute: 15, dignity: "exalted" },
    { name: "Mercury", house: ((ascendantSign - 1 + 3) % 12) + 1, sign: ((ascendantSign + 2) % 12) + 1, degree: 12, minute: 45, dignity: "own" },
    { name: "Jupiter", house: ((ascendantSign - 1 + 4) % 12) + 1, sign: ((ascendantSign + 3) % 12) + 1, degree: 22, minute: 10, dignity: "friendly" },
    { name: "Venus", house: ((ascendantSign - 1 + 5) % 12) + 1, sign: ((ascendantSign + 4) % 12) + 1, degree: 18, minute: 5, dignity: "debilitated" },
    { name: "Saturn", house: ((ascendantSign - 1 + 6) % 12) + 1, sign: ((ascendantSign + 5) % 12) + 1, degree: 29, minute: 50, dignity: "neutral" },
    { name: "Rahu", house: ((ascendantSign - 1 + 7) % 12) + 1, sign: ((ascendantSign + 6) % 12) + 1, degree: 14, minute: 0, dignity: "enemy" },
    { name: "Ketu", house: ((ascendantSign - 1 + 8) % 12) + 1, sign: ((ascendantSign + 7) % 12) + 1, degree: 14, minute: 0, dignity: "enemy" },
  ];

  const details: Record<string, PlanetPosition> = {};
  defaultPlanets.forEach((p) => {
    details[p.name] = p;
  });

  return {
    ascendant: ascendantSign,
    ascendantSign,
    chartStyle,
    vargaType,
    planets: defaultPlanets,
    planet_details: details,
  };
}

export const defaultProps: {
  planets: PlanetPosition[];
  chartStyle: "NORTH_INDIAN" | "SOUTH_INDIAN";
  showTransits: boolean;
  transitPlanets: Array<{ name: string; house: number; longitude: number }>;
  aspects: AspectLine[];
  showAspectLines: boolean;
  width: number;
  height: number;
} = {
  planets: generateDemoChartData().planets,
  chartStyle: "NORTH_INDIAN",
  showTransits: false,
  transitPlanets: [],
  aspects: [],
  showAspectLines: false,
  width: 400,
  height: 400,
};

const NORTH_HOUSE_CENTERS: Record<number, { x: number; y: number }> = {
  1: { x: 200, y: 100 },
  2: { x: 100, y: 50 },
  3: { x: 50, y: 100 },
  4: { x: 100, y: 200 },
  5: { x: 50, y: 300 },
  6: { x: 100, y: 350 },
  7: { x: 200, y: 300 },
  8: { x: 300, y: 350 },
  9: { x: 350, y: 300 },
  10: { x: 300, y: 200 },
  11: { x: 350, y: 100 },
  12: { x: 300, y: 50 },
};

const SOUTH_HOUSE_RECTS: Record<number, { x: number; y: number; width: number; height: number }> = {
  1: { x: 100, y: 10, width: 95, height: 95 },
  2: { x: 195, y: 10, width: 95, height: 95 },
  3: { x: 290, y: 10, width: 100, height: 95 },
  4: { x: 290, y: 105, width: 100, height: 95 },
  5: { x: 290, y: 200, width: 100, height: 95 },
  6: { x: 290, y: 295, width: 100, height: 95 },
  7: { x: 195, y: 295, width: 95, height: 95 },
  8: { x: 100, y: 295, width: 95, height: 95 },
  9: { x: 10, y: 295, width: 90, height: 95 },
  10: { x: 10, y: 200, width: 90, height: 95 },
  11: { x: 10, y: 105, width: 90, height: 95 },
  12: { x: 10, y: 10, width: 90, height: 95 },
};

function getDignityBg(dignity?: string): string {
  const d = (dignity || '').toLowerCase();
  if (d.includes('exalt')) return 'fill-emerald-950/90 stroke-emerald-400';
  if (d.includes('debil')) return 'fill-rose-950/90 stroke-rose-400';
  if (d.includes('own')) return 'fill-amber-950/90 stroke-amber-400';
  if (d.includes('friend')) return 'fill-sky-950/90 stroke-sky-400';
  if (d.includes('enemy')) return 'fill-orange-950/90 stroke-orange-400';
  return 'fill-slate-900/90 stroke-slate-600';
}

function getDignityTextColor(dignity?: string): string {
  const d = (dignity || '').toLowerCase();
  if (d.includes('exalt')) return 'fill-emerald-300';
  if (d.includes('debil')) return 'fill-rose-300';
  if (d.includes('own')) return 'fill-amber-300';
  if (d.includes('friend')) return 'fill-sky-300';
  if (d.includes('enemy')) return 'fill-orange-300';
  return 'fill-slate-200';
}

export const SvgChartRenderer: React.FC<SvgChartRendererProps> = ({
  data,
  planets: propPlanets,
  chartData,
  title,
  style,
  chartStyle = "NORTH_INDIAN",
  vargaType,
  showTransits = false,
  transitPlanets = [],
  onPlanetClick,
  onPlanetSelect,
  selectedPlanet,
  aspects = [],
  onAspectClick,
  showAspectLines = false,
  width = 400,
  height = 400,
}) => {
  const [hoveredPlanet, setHoveredPlanet] = useState<PlanetPosition | null>(null);
  const [userStyle, setUserStyle] = useState<"NORTH_INDIAN" | "SOUTH_INDIAN" | "GRID" | null>(null);
  const activeStyle = userStyle || style || chartStyle;
  const chartVargaType = vargaType || 'D1';
  const handlePlanetClick = onPlanetClick || onPlanetSelect;

  const rawList: PlanetPosition[] = chartData || propPlanets || data?.planets || [];

  const isGridOnly = activeStyle === "GRID" || (Boolean(chartData) && rawList.length > 0 && rawList.every((p) => !p.house));

  const ascSign = Number(data?.ascendantSign || data?.ascendant) || 1;

  const getPlanetsByHouse = () => {
    const houses: Record<number, Array<PlanetPosition & { isTransit?: boolean }>> = {};
    for (let i = 1; i <= 12; i++) houses[i] = [];

    if (rawList.length > 0) {
      rawList.forEach((p, idx) => {
        const targetHouse = p.house || (idx % 12) + 1;
        if (houses[targetHouse]) {
          houses[targetHouse].push({ ...p, isTransit: false });
        }
      });
    } else if (data?.planet_details) {
      Object.entries(data.planet_details).forEach(([name, p]: [string, any]) => {
        if (p && typeof p === "object") {
          const houseNum = Number(p.house) || 1;
          if (houses[houseNum]) {
            houses[houseNum].push({
              name,
              house: houseNum,
              degree: p.degree !== undefined ? p.degree : p.degree_in_sign,
              nakshatra: p.nakshatra,
              dignity: p.dignity,
              isTransit: false,
            });
          }
        }
      });
    }

    if (showTransits && transitPlanets.length > 0) {
      transitPlanets.forEach((tp) => {
        if (tp.house && houses[tp.house]) {
          houses[tp.house].push({ name: tp.name, house: tp.house, longitude: tp.longitude, isTransit: true });
        }
      });
    }

    return houses;
  };

  const getPlanetsBySign = () => {
    const signs: Record<number, Array<PlanetPosition & { isTransit?: boolean }>> = {};
    for (let i = 1; i <= 12; i++) signs[i] = [];

    const resolveSignNum = (s?: number | string): number => {
      if (typeof s === 'number') return s >= 1 && s <= 12 ? s : (((s - 1) % 12) + 1);
      if (typeof s === 'string') {
        const upper = s.toUpperCase();
        const map: Record<string, number> = {
          ARIES: 1, MESHA: 1, AR: 1,
          TAURUS: 2, VRISHABHA: 2, TA: 2,
          GEMINI: 3, MITHUNA: 3, GE: 3,
          CANCER: 4, KARKA: 4, CA: 4,
          LEO: 5, SIMHA: 5, LE: 5,
          VIRGO: 6, KANYA: 6, VI: 6,
          LIBRA: 7, TULA: 7, LI: 7,
          SCORPIO: 8, VRISHCHIKA: 8, SC: 8,
          SAGITTARIUS: 9, DHANUSHA: 9, DHANU: 9, SG: 9,
          CAPRICORN: 10, MAKARA: 10, CP: 10,
          AQUARIUS: 11, KUMBHA: 11, AQ: 11,
          PISCES: 12, MEENA: 12, PI: 12,
        };
        if (map[upper]) return map[upper];
        const n = parseInt(s, 10);
        if (!isNaN(n) && n >= 1 && n <= 12) return n;
      }
      return 0;
    };

    if (rawList.length > 0) {
      rawList.forEach((p, idx) => {
        let signNum = resolveSignNum(p.sign);
        if (!signNum && p.house) {
          signNum = ((ascSign - 1 + (p.house - 1)) % 12) + 1;
        }
        if (!signNum) {
          signNum = (idx % 12) + 1;
        }
        if (signs[signNum]) {
          signs[signNum].push({ ...p, isTransit: false });
        }
      });
    } else if (data?.planet_details) {
      Object.entries(data.planet_details).forEach(([name, p]: [string, any]) => {
        if (p && typeof p === "object") {
          let signNum = resolveSignNum(p.sign || p.sign_num || p.rashi);
          const houseNum = Number(p.house) || 1;
          if (!signNum && houseNum) {
            signNum = ((ascSign - 1 + (houseNum - 1)) % 12) + 1;
          }
          if (!signNum) signNum = 1;
          signs[signNum].push({
            name,
            house: houseNum,
            sign: signNum,
            degree: p.degree !== undefined ? p.degree : p.degree_in_sign,
            nakshatra: p.nakshatra,
            dignity: p.dignity,
            isTransit: false,
          });
        }
      });
    }

    if (showTransits && transitPlanets.length > 0) {
      transitPlanets.forEach((tp) => {
        const signNum = ((ascSign - 1 + (tp.house - 1)) % 12) + 1;
        if (signs[signNum]) {
          signs[signNum].push({ name: tp.name, house: tp.house, longitude: tp.longitude, isTransit: true });
        }
      });
    }

    return signs;
  };

  const housePlanets = getPlanetsByHouse();
  const signPlanets = getPlanetsBySign();

  return (
    <div
      className="relative border border-amber-500/30 rounded-xl p-4 bg-slate-950/80 shadow-lg max-w-[500px] mx-auto"
      data-testid="svg-chart-renderer"
    >
      {/* Chart Title Header & Layout Toggle */}
      <div className="flex justify-between items-center mb-2 px-1 gap-2">
        {title && (
          <h4 className="text-sm font-semibold text-amber-400">{title}</h4>
        )}
        {!isGridOnly && (
          <div className="inline-flex rounded-lg p-0.5 bg-slate-900 border border-slate-800 text-[10px]">
            <button
              type="button"
              onClick={() => setUserStyle("NORTH_INDIAN")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeStyle === "NORTH_INDIAN"
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              North Indian
            </button>
            <button
              type="button"
              onClick={() => setUserStyle("SOUTH_INDIAN")}
              className={`px-2 py-0.5 rounded transition-colors ${
                activeStyle === "SOUTH_INDIAN"
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              South Indian
            </button>
          </div>
        )}
      </div>

      {/* Interactive Tooltip Banner */}
      <div className="h-8 mb-2 text-xs flex items-center justify-center text-slate-300 bg-slate-900/60 rounded px-2 border border-slate-800/80">
        {hoveredPlanet ? (
          <span>
            <strong className="text-amber-300">{hoveredPlanet.name}</strong>
            {hoveredPlanet.degree !== undefined && ` • ${typeof hoveredPlanet.degree === 'number' ? hoveredPlanet.degree.toFixed(2) : hoveredPlanet.degree}°`}
            {hoveredPlanet.nakshatra && ` • Nakshatra: ${hoveredPlanet.nakshatra}`}
            {hoveredPlanet.dignity && ` (${hoveredPlanet.dignity})`}
          </span>
        ) : (
          <span className="text-slate-500">Hover over a planet to inspect details</span>
        )}
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto max-w-[380px] mx-auto stroke-slate-700 fill-none">
        {/* Title within SVG */}
        {!title && (
          <>
            <text
              x={width / 2}
              y={18}
              textAnchor="middle"
              fontSize="13"
              fontWeight="700"
              fontFamily="var(--font-playfair), Georgia, serif"
              fill="var(--cosmic-gold, #fbbf24)"
              opacity={0.9}
            >
              {Varga_LABELS[chartVargaType] || chartVargaType}
            </text>
            <text
              x={width / 2}
              y={32}
              textAnchor="middle"
              fontSize="8"
              fontFamily="var(--font-inter), system-ui, sans-serif"
              fill="var(--cosmic-muted, #64748b)"
            >
              {activeStyle === 'NORTH_INDIAN' ? 'House-fixed diamond grid' : 'Sign-fixed grid — Ascendant shifts dynamically'}
            </text>
          </>
        )}

        {activeStyle === 'SOUTH_INDIAN' && (
          <text
            x={width - 20}
            y={18}
            textAnchor="end"
            fontSize="8"
            fontFamily="var(--font-inter), system-ui, sans-serif"
            fill="var(--cosmic-gold, #fbbf24)"
          >
            ASC / Lg
          </text>
        )}

        {isGridOnly ? (
          /* Simple 3x3 Grid Mode */
          <>
            <rect x="10" y="10" width="380" height="380" fill="none" stroke="#d97706" strokeWidth="2" />
            <line x1="136" y1="10" x2="136" y2="390" stroke="#78350f" strokeWidth="1" />
            <line x1="264" y1="10" x2="264" y2="390" stroke="#78350f" strokeWidth="1" />
            <line x1="10" y1="136" x2="390" y2="136" stroke="#78350f" strokeWidth="1" />
            <line x1="10" y1="264" x2="390" y2="264" stroke="#78350f" strokeWidth="1" />

            {rawList.map((planet, idx) => (
              <g
                key={idx}
                data-planet={planet.name}
                className="cursor-pointer transition-transform hover:scale-110"
                onMouseEnter={() => setHoveredPlanet(planet)}
                onMouseLeave={() => setHoveredPlanet(null)}
                onClick={() => handlePlanetClick?.(planet.name)}
              >
                <title>
                  {`${planet.name}${planet.degree !== undefined ? ` • ${typeof planet.degree === 'number' ? planet.degree.toFixed(2) : planet.degree}°` : ''}${planet.nakshatra ? ` • Nakshatra: ${planet.nakshatra}` : ''}${planet.dignity ? ` (${planet.dignity})` : ''}`}
                </title>
                <circle
                  cx={73 + (idx % 3) * 127}
                  cy={73 + Math.floor(idx / 3) * 127}
                  r="16"
                  className={`${getDignityBg(planet.dignity)} stroke-amber-400 hover:fill-amber-600`}
                  strokeWidth="1.5"
                />
                <text
                  x={73 + (idx % 3) * 127}
                  y={77 + Math.floor(idx / 3) * 127}
                  textAnchor="middle"
                  className="text-[11px] font-bold fill-amber-200 pointer-events-none"
                >
                  {PLANET_SYMBOLS[planet.name] || planet.name.substring(0, 2)}
                </text>
                {planet.degree !== undefined && (
                  <g className="degree-overlay-badge">
                    <rect
                      x={58 + (idx % 3) * 127}
                      y={86 + Math.floor(idx / 3) * 127}
                      width="30"
                      height="13"
                      rx="3"
                      ry="3"
                      className="fill-slate-900/90 stroke-amber-500/40"
                      strokeWidth="0.8"
                    />
                    <text
                      x={73 + (idx % 3) * 127}
                      y={96 + Math.floor(idx / 3) * 127}
                      textAnchor="middle"
                      className="text-[9px] font-mono font-bold fill-amber-200 pointer-events-none"
                    >
                      {typeof planet.degree === 'number' ? `${planet.degree.toFixed(1)}°` : `${planet.degree}°`}
                    </text>
                  </g>
                )}
              </g>
            ))}
          </>
        ) : activeStyle === "NORTH_INDIAN" ? (
          <>
            <rect x="10" y="10" width="380" height="380" strokeWidth="2" className="stroke-slate-600" />
            <line x1="10" y1="10" x2="390" y2="390" strokeWidth="1" />
            <line x1="390" y1="10" x2="10" y2="390" strokeWidth="1" />
            <line x1="200" y1="10" x2="10" y2="200" strokeWidth="1" />
            <line x1="10" y1="200" x2="200" y2="390" strokeWidth="1" />
            <line x1="200" y1="390" x2="390" y2="200" strokeWidth="1" />
            <line x1="390" y1="200" x2="200" y2="10" strokeWidth="1" />

            {Object.entries(housePlanets).map(([houseStr, planets]) => {
              const houseNum = parseInt(houseStr, 10);
              const pos = NORTH_HOUSE_CENTERS[houseNum] || { x: 200, y: 200 };

              return (
                <g key={`house-${houseNum}`} transform={`translate(${pos.x}, ${pos.y})`}>
                  <text
                    x="0"
                    y="-25"
                    textAnchor="middle"
                    className="text-[10px] fill-amber-500/60 font-mono font-semibold pointer-events-none"
                  >
                    {houseNum}{houseNum === 1 ? ' ASC' : ''}
                  </text>

                  <g transform="translate(0, -6)">
                    {planets.map((p, idx) => {
                      const yOffset = idx * 16;
                      const label = PLANET_SYMBOLS[p.name] || p.name.slice(0, 2);
                      const isSelected = selectedPlanet === p.name;
                      const degText = p.degree !== undefined ? `${Math.floor(Number(p.degree))}°` : '';

                      return (
                        <g
                          key={`p-${houseNum}-${idx}`}
                          data-planet={p.name}
                          className="cursor-pointer transition-transform hover:scale-110"
                          onMouseEnter={() => setHoveredPlanet(p)}
                          onMouseLeave={() => setHoveredPlanet(null)}
                          onClick={() => handlePlanetClick?.(p.name)}
                        >
                          <title>
                            {`${p.name}${p.degree !== undefined ? ` • ${Number(p.degree).toFixed(2)}°` : ''}${p.nakshatra ? ` • Nakshatra: ${p.nakshatra}` : ''}${p.dignity ? ` (${p.dignity})` : ''}`}
                          </title>
                          <circle
                            cx={degText ? -10 : 0}
                            cy={yOffset - 3}
                            r="8"
                            className={`${getDignityBg(p.dignity)} ${isSelected ? "stroke-amber-400 stroke-2" : "stroke-amber-500/40"}`}
                          />
                          <text
                            x={degText ? -10 : 0}
                            y={yOffset}
                            textAnchor="middle"
                            className={`text-[9px] font-bold ${isSelected ? "fill-amber-300 font-extrabold" : p.isTransit ? "fill-emerald-400 italic" : getDignityTextColor(p.dignity)}`}
                          >
                            {p.isTransit ? `t${label}` : label}
                          </text>
                          {p.isRetrograde && (
                            <text
                              x={degText ? -3 : 7}
                              y={yOffset - 6}
                              className="text-[7px] font-bold fill-rose-400"
                            >
                              R
                            </text>
                          )}
                          {degText && (
                            <g className="degree-overlay-badge">
                              <rect
                                x="2"
                                y={yOffset - 8}
                                width={degText.length > 3 ? 24 : 18}
                                height="11"
                                rx="3"
                                ry="3"
                                className="fill-slate-950/85 stroke-amber-500/30"
                                strokeWidth="0.8"
                              />
                              <text
                                x={degText.length > 3 ? 14 : 11}
                                y={yOffset}
                                textAnchor="middle"
                                className="text-[8px] font-mono font-bold fill-amber-300 pointer-events-none"
                              >
                                {degText}
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </g>
                </g>
              );
            })}
          </>
        ) : (
          /* South Indian Chart */
          <>
            <rect x="10" y="10" width="380" height="380" strokeWidth="2" className="stroke-slate-600" />
            <line x1="100" y1="10" x2="100" y2="390" strokeWidth="1" />
            <line x1="195" y1="10" x2="195" y2="105" strokeWidth="1" />
            <line x1="195" y1="295" x2="195" y2="390" strokeWidth="1" />
            <line x1="290" y1="10" x2="290" y2="390" strokeWidth="1" />
            <line x1="10" y1="105" x2="390" y2="105" strokeWidth="1" />
            <line x1="10" y1="200" x2="100" y2="200" strokeWidth="1" />
            <line x1="290" y1="200" x2="390" y2="200" strokeWidth="1" />
            <line x1="10" y1="295" x2="390" y2="295" strokeWidth="1" />

            {/* Center Area */}
            <rect x="100" y="105" width="190" height="190" strokeWidth="1" className="stroke-slate-700 fill-slate-950/70" />
            <g className="south-chart-center pointer-events-none">
              <text
                x="195"
                y="195"
                textAnchor="middle"
                fontSize="11"
                fontWeight="600"
                fill="#f59e0b"
              >
                Lagna: {SIGN_ABBREVS[ascSign] || 'Ar'}
              </text>
              <text
                x="195"
                y="215"
                textAnchor="middle"
                fontSize="9"
                fontFamily="var(--font-inter), system-ui, sans-serif"
                fill="var(--cosmic-muted, #64748b)"
              >
                Fixed Sign Geometry
              </text>
            </g>

            {/* 12 Sign Boxes */}
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((signNum) => {
              const rect = SOUTH_HOUSE_RECTS[signNum] || { x: 10, y: 10, width: 90, height: 95 };
              const planets = signPlanets[signNum] || [];
              const isAscSign = signNum === ascSign;
              const relHouse = ((signNum - ascSign + 12) % 12) + 1;
              const centerX = rect.x + rect.width / 2;
              const centerY = rect.y + 24;

              return (
                <g key={`south-sign-${signNum}`}>
                  {/* Sign abbreviation at bottom-left */}
                  <text
                    x={rect.x + 8}
                    y={rect.y + rect.height - 4}
                    className="text-[7px] fill-slate-500 font-mono font-bold pointer-events-none"
                  >
                    {SIGN_ABBREVS[signNum]}
                  </text>

                  {/* House number at top-left */}
                  <text
                    x={rect.x + 8}
                    y={rect.y + 16}
                    className="text-[9px] fill-amber-500/60 font-mono font-semibold pointer-events-none"
                  >
                    {relHouse}
                  </text>

                  {/* Ascendant badge and diagonal mark */}
                  {isAscSign && (
                    <>
                      <line
                        x1={rect.x + rect.width - 24}
                        y1={rect.y}
                        x2={rect.x + rect.width}
                        y2={rect.y + 24}
                        stroke="#f59e0b"
                        strokeWidth="1"
                        opacity="0.7"
                      />
                      <text
                        x={rect.x + rect.width - 6}
                        y={rect.y + 14}
                        textAnchor="end"
                        className="text-[8px] font-bold fill-amber-400 font-mono pointer-events-none"
                      >
                        ASC
                      </text>
                    </>
                  )}

                  {/* Planets in sign */}
                  <g transform={`translate(${centerX}, ${centerY})`}>
                    {planets.map((p, idx) => {
                      const yOffset = idx * 16;
                      const label = PLANET_SYMBOLS[p.name] || p.name.slice(0, 2);
                      const isSelected = selectedPlanet === p.name;
                      const degText = p.degree !== undefined ? `${Math.floor(Number(p.degree))}°` : '';

                      return (
                        <g
                          key={`sp-${signNum}-${idx}`}
                          data-planet={p.name}
                          className="cursor-pointer transition-transform hover:scale-110"
                          onMouseEnter={() => setHoveredPlanet(p)}
                          onMouseLeave={() => setHoveredPlanet(null)}
                          onClick={() => handlePlanetClick?.(p.name)}
                        >
                          <title>
                            {`${p.name}${p.degree !== undefined ? ` • ${Number(p.degree).toFixed(2)}°` : ''}${p.nakshatra ? ` • Nakshatra: ${p.nakshatra}` : ''}${p.dignity ? ` (${p.dignity})` : ''}`}
                          </title>
                          <circle
                            cx={degText ? -10 : 0}
                            cy={yOffset - 3}
                            r="8"
                            className={`${getDignityBg(p.dignity)} ${isSelected ? "stroke-amber-400 stroke-2" : "stroke-amber-500/40"}`}
                          />
                          <text
                            x={degText ? -10 : 0}
                            y={yOffset}
                            textAnchor="middle"
                            className={`text-[9px] font-bold ${isSelected ? "fill-amber-300 font-extrabold" : p.isTransit ? "fill-emerald-400 italic" : getDignityTextColor(p.dignity)}`}
                          >
                            {p.isTransit ? `t${label}` : label}
                          </text>
                          {p.isRetrograde && (
                            <text
                              x={degText ? -3 : 7}
                              y={yOffset - 6}
                              className="text-[7px] font-bold fill-rose-400"
                            >
                              R
                            </text>
                          )}
                          {degText && (
                            <g className="degree-overlay-badge">
                              <rect
                                x="2"
                                y={yOffset - 8}
                                width={degText.length > 3 ? 24 : 18}
                                height="11"
                                rx="3"
                                ry="3"
                                className="fill-slate-950/85 stroke-amber-500/30"
                                strokeWidth="0.8"
                              />
                              <text
                                x={degText.length > 3 ? 14 : 11}
                                y={yOffset}
                                textAnchor="middle"
                                className="text-[8px] font-mono font-bold fill-amber-300 pointer-events-none"
                              >
                                {degText}
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </g>
                </g>
              );
            })}
          </>
        )}

        {(showAspectLines || aspects.length > 0) && (
          <g data-testid="aspect-vectors">
            {aspects.map((aspect, idx) => (
              <line
                key={`aspect-${idx}`}
                x1="200"
                y1="200"
                x2="100"
                y2="100"
                stroke="#6366f1"
                strokeWidth="1.5"
                strokeDasharray="4"
                onClick={() => onAspectClick?.(aspect)}
                className="cursor-pointer hover:stroke-indigo-400"
              />
            ))}
          </g>
        )}
      </svg>
    </div>
  );
};

export default SvgChartRenderer;
