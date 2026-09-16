'use client';

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SvgChartRenderer, { PlanetPosition } from '@/components/charts/SvgChartRenderer';
import { generateEvaluationPdf } from '@/lib/exportPdf';
import { API_BASE_URL } from '@/lib/api';

export interface YogaItem {
  name: string;
  status: string;
  planets: string[];
  strength: string;
  domains: string[];
}

export interface DashaPeriodItem {
  lord: string;
  level: string;
  start_utc: string;
  end_utc: string;
  duration_years: number;
}

export interface EvaluationReportTabsProps {
  evaluationData: any;
  apiKey?: string;
  birthDisplay?: Record<string, any>;
  synthesisMarkdown?: string;
  synthesisError?: string | null;
  isSynthesizing?: boolean;
  onGenerateReport?: () => void | Promise<void>;
  onDownloadPdf?: () => void;
}

const SIGN_INDEX: Record<string, number> = {
  MESHA: 1, VRISHABHA: 2, MITHUNA: 3, KARKA: 4, SIMHA: 5, KANYA: 6,
  TULA: 7, VRISHCHIKA: 8, DHANUSHA: 9, MAKARA: 10, KUMBHA: 11, MEENA: 12,
};

const SIGN_LORDS: Record<number, string> = {
  1: 'MARS', 2: 'VENUS', 3: 'MERCURY', 4: 'MOON', 5: 'SUN', 6: 'MERCURY',
  7: 'VENUS', 8: 'MARS', 9: 'JUPITER', 10: 'SATURN', 11: 'SATURN', 12: 'JUPITER',
};

const PLANET_REMEDIES: Record<string, { mantra: string; gemstone: string; day: string; colors: string }> = {
  SUN: { mantra: 'Om Suryaya Namaha', gemstone: 'Ruby', day: 'Sunday', colors: 'Saffron, Gold' },
  MOON: { mantra: 'Om Chandraya Namaha', gemstone: 'Pearl', day: 'Monday', colors: 'White, Silver' },
  MARS: { mantra: 'Om Mangalaya Namaha', gemstone: 'Red Coral', day: 'Tuesday', colors: 'Red' },
  MERCURY: { mantra: 'Om Budhaya Namaha', gemstone: 'Emerald', day: 'Wednesday', colors: 'Green' },
  JUPITER: { mantra: 'Om Gurave Namaha', gemstone: 'Yellow Sapphire', day: 'Thursday', colors: 'Yellow, Gold' },
  VENUS: { mantra: 'Om Shukraya Namaha', gemstone: 'Diamond', day: 'Friday', colors: 'White, Pink' },
  SATURN: { mantra: 'Om Shanaye Namaha', gemstone: 'Blue Sapphire', day: 'Saturday', colors: 'Black, Dark Blue' },
  RAHU: { mantra: 'Om Rahave Namaha', gemstone: 'Hessonite', day: 'Saturday', colors: 'Smoky, Brown' },
  KETU: { mantra: 'Om Ketave Namaha', gemstone: "Cat's Eye", day: 'Tuesday', colors: 'Grey' },
};

function titleize(value: string): string {
  if (!value) return '';
  return value
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatUtcDate(utc: string): string {
  if (!utc) return '—';
  const d = new Date(utc);
  return isNaN(d.getTime())
    ? utc
    : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function extractChartPlanets(evaluationData: any, division: 'D1' | 'D9'): PlanetPosition[] {
  const planetDetails: Record<string, any> = evaluationData?.planet_details || {};
  const planets: PlanetPosition[] = [];

  for (const [nameRaw, detailRaw] of Object.entries(planetDetails)) {
    if (typeof detailRaw !== 'object' || detailRaw === null) continue;
    const detail = detailRaw as Record<string, any>;
    const name = nameRaw.charAt(0) + nameRaw.slice(1).toLowerCase();

    if (division === 'D1') {
      const house = Number(detail.house) || 0;
      const sign = Number(detail.sign_num) || SIGN_INDEX[String(detail.sign || '').toUpperCase()] || 0;
      if (!house || !sign) continue;
      planets.push({
        name,
        house,
        sign,
        longitude: Number(detail.degree_in_sign) || 0,
        degree: Math.floor(Number(detail.degree_in_sign) || 0),
        dignity: String(detail.dignity || '').toLowerCase(),
        nakshatra: detail.nakshatra || '',
      });
    } else {
      const house = Number(detail.navamsha_house) || 0;
      const sign = SIGN_INDEX[String(detail.navamsha_sign || '').toUpperCase()] || 0;
      if (!house || !sign) continue;
      planets.push({ name, house, sign });
    }
  }

  return planets;
}

export function EvaluationReportTabs({
  evaluationData,
  apiKey,
  birthDisplay: birthDisplayProp,
  synthesisMarkdown: parentSynthesisMarkdown,
  synthesisError: parentSynthesisError,
  isSynthesizing: parentSynthesizing,
  onGenerateReport,
  onDownloadPdf,
}: EvaluationReportTabsProps) {
  const [activeTab, setActiveTab] = useState<
    | 'blueprint'
    | 'timeline'
    | 'life_paths'
    | 'circle'
    | 'alignment'
    | 'lucky_elements'
    | 'charts'
    | 'overview'
  >('blueprint');

  const [synthesisLoading, setSynthesisLoading] = useState(false);
  const [synthesisError, setSynthesisError] = useState('');

  const evaluationId: string = evaluationData?.evaluation_id || 'unknown';
  const [synthesisContent, setSynthesisContent] = useState<string>(() => {
    if (typeof window === 'undefined') return '';
    try {
      return localStorage.getItem(`jre_synthesis_${evaluationId}`) || '';
    } catch {
      return '';
    }
  });

  useEffect(() => {
    const handleSync = (e: any) => {
      if (e?.detail) setSynthesisContent(e.detail);
    };
    window.addEventListener('jre-synthesis-updated', handleSync);
    return () => window.removeEventListener('jre-synthesis-updated', handleSync);
  }, []);

  const handleSynthesisGenerated = (markdown: string) => {
    setSynthesisContent(markdown);
    try {
      localStorage.setItem(`jre_synthesis_${evaluationId}`, markdown);
    } catch {
      /* storage full or unavailable */
    }
  };

  // Parent-managed synthesis flow (optional): the evaluate page owns generation.
  // Internal state remains as a cached fallback for standalone usage.
  const parentManaged = typeof onGenerateReport === 'function';

  useEffect(() => {
    if (parentManaged && parentSynthesisMarkdown) {
      handleSynthesisGenerated(parentSynthesisMarkdown);
    }
  }, [parentManaged, parentSynthesisMarkdown]);

  const yogaList: YogaItem[] = (evaluationData?.yogas || []).map((y: any) => ({
    name: y.yoga_name,
    status: y.status,
    planets: y.involved_planets || [],
    strength: y.static_strength > 0 ? `${(y.static_strength * 100).toFixed(0)}%` : '—',
    domains: y.domains || [],
  }));

  const formedYogas = yogaList.filter((y) => y.status === 'FORMED');

  const deepDasha: any = evaluationData?.deep_dasha || null;
  const adTimeline: DashaPeriodItem[] = deepDasha?.ad_timeline || [];
  const birthDisplay: Record<string, any> = birthDisplayProp || evaluationData?.birth_data_display || {};
  const planetDetails: Record<string, any> = evaluationData?.planet_details || {};
  const dignityMap: Record<string, string> = evaluationData?.dignity_map || {};
  const elementalBalance: Record<string, number> = evaluationData?.elemental_balance || {};
  const parivartanas: any[] = evaluationData?.parivartana_yogas || [];
  const parivartanaSynthesis: Record<string, string> = evaluationData?.parivartana_synthesis || {};

  const lagnaName = titleize(evaluationData?.lagna || '');
  const moonNak = titleize(evaluationData?.moon_nakshatra || '');
  const lagnaSignNum =
    SIGN_INDEX[String(birthDisplay?.lagna || evaluationData?.lagna || '').toUpperCase()] || 0;
  const lagnaLord = lagnaSignNum ? SIGN_LORDS[lagnaSignNum] : '';
  const lagnaLordRemedy = PLANET_REMEDIES[lagnaLord] || {
    mantra: 'Om Namah Shivaya',
    gemstone: 'Consult an astrologer',
    day: '—',
    colors: '—',
  };

  const seventhOccupants = Object.entries(planetDetails)
    .filter(([, d]) => Number(d?.house) === 7)
    .map(([name]) => titleize(name));
  const seventhSignNum = lagnaSignNum ? ((lagnaSignNum + 5) % 12) + 1 : 0;
  const seventhLord = seventhSignNum ? SIGN_LORDS[seventhSignNum] : '';

  const hasNavamshaData = Object.values(planetDetails).some((d: any) => d?.navamsha_sign);
  const hasD1Data = Object.values(planetDetails).some((d: any) => Number(d?.house) > 0);

  const lifePathDomains: { domain: string; yogas: YogaItem[] }[] = [];
  for (const yoga of formedYogas) {
    for (const domain of yoga.domains) {
      const label = titleize(domain);
      let bucket = lifePathDomains.find((d) => d.domain === label);
      if (!bucket) {
        bucket = { domain: label, yogas: [] };
        lifePathDomains.push(bucket);
      }
      bucket.yogas.push(yoga);
    }
  }

  const afflictedPlanets = Object.entries(planetDetails).filter(
    ([, d]) => d?.dignity === 'Debilitated' || d?.combust
  );
  const debilitatedPlanet = Object.entries(dignityMap).find(
    ([, dignity]) => dignity === 'Debilitated'
  );

  const fetchSynthesis = async () => {
    setSynthesisLoading(true);
    setSynthesisError('');
    try {
      if (!birthDisplay?.date) {
        throw new Error('Birth data missing from evaluation — cannot generate report.');
      }
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey || (typeof window !== 'undefined' ? localStorage.getItem('jre_api_key') || '' : ''),
        },
        body: JSON.stringify({
          date: birthDisplay?.date,
          time: birthDisplay?.time || '12:00',
          latitude: parseFloat(birthDisplay?.latitude || '0'),
          longitude: parseFloat(birthDisplay?.longitude || '0'),
          timezone: birthDisplay?.timezone || 'Asia/Kolkata',
        }),
      });
      if (!response.ok) {
        throw new Error(`Analyze API returned ${response.status}. Is the backend running?`);
      }
      const data = await response.json();
      if (data?.synthesis_markdown) {
        handleSynthesisGenerated(data.synthesis_markdown);
      } else {
        throw new Error('Backend response did not include a synthesis report.');
      }
    } catch (err) {
      console.error('Failed to fetch synthesis:', err);
      setSynthesisError(
        err instanceof Error ? err.message : 'Failed to generate report. Is the backend running?'
      );
    } finally {
      setSynthesisLoading(false);
    }
  };

  const effectiveSynthesisContent = parentManaged
    ? parentSynthesisMarkdown || synthesisContent
    : synthesisContent;
  const effectiveSynthesisError = parentManaged ? parentSynthesisError || null : synthesisError || null;
  const effectiveSynthesizing = parentManaged ? !!parentSynthesizing : synthesisLoading;

  return (
    <div id="report-content-container" className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header Banner */}
      <div className="border border-slate-800 bg-slate-900/60 p-6 rounded-2xl flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-400">Dynamic Astro-Karmic Blueprint</h1>
          <p className="text-sm text-slate-400">
            Lagna: <span className="text-amber-300 font-semibold">{lagnaName || '—'}</span>
            {moonNak && (
              <>
                {' '}• Moon: <span className="text-amber-300">{moonNak}</span>
              </>
            )}{' '}• {yogaList.length} Yogas Detected ({formedYogas.length} active)
            {birthDisplay?.date && <> • {birthDisplay.date}</>}
          </p>
        </div>
        <button
          onClick={() => {
            generateEvaluationPdf('report-content-container');
            onDownloadPdf?.();
          }}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg transition-colors"
        >
          Download PDF Report
        </button>
      </div>

      {/* Primary Tab Bar */}
      <div className="flex border-b border-slate-800 overflow-x-auto gap-2 text-sm font-semibold scrollbar-none">
        {[
          { id: 'blueprint', label: 'My Blueprint', icon: '✨' },
          { id: 'timeline', label: 'My Cosmic Timeline', icon: '🧭' },
          { id: 'life_paths', label: 'My Life Paths', icon: '💖' },
          { id: 'circle', label: 'My Circle', icon: '🕊️' },
          { id: 'alignment', label: 'Parihara (Remedies)', icon: '☯️' },
          { id: 'lucky_elements', label: 'Lucky Elements', icon: '🍀' },
          { id: 'charts', label: 'Charts', icon: '📊' },
          { id: 'overview', label: 'Overview', icon: '📝' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-5 py-3 border-b-2 font-medium transition-all whitespace-nowrap uppercase tracking-wider ${
              activeTab === tab.id
                ? 'border-amber-400 text-amber-400 bg-amber-400/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="mt-6">
        {/* TAB 1: BLUEPRINT */}
        {activeTab === 'blueprint' && (
          <div className="space-y-8">
            {/* Core Natal Charts Preview */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
              <h2 className="text-lg font-bold text-amber-400">Core Natal Charts</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* D1 Rasi Chart */}
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">D1 Rasi Chart (Birth Chart)</h3>
                  {hasD1Data ? (
                    <SvgChartRenderer
                      planets={extractChartPlanets(evaluationData, 'D1')}
                      chartStyle="NORTH_INDIAN"
                      vargaType="D1"
                      width={400}
                      height={400}
                    />
                  ) : (
                    <p className="text-slate-400 text-sm py-8 text-center">
                      Planetary positions unavailable for this evaluation.
                    </p>
                  )}
                </div>

                {/* D9 Navamsa Chart */}
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">D9 Navamsa Chart (Soul Chart)</h3>
                  {hasNavamshaData ? (
                    <SvgChartRenderer
                      planets={extractChartPlanets(evaluationData, 'D9')}
                      chartStyle="NORTH_INDIAN"
                      vargaType="D9"
                      width={400}
                      height={400}
                    />
                  ) : (
                    <p className="text-slate-400 text-sm py-8 text-center">
                      Navamsha positions unavailable for this evaluation.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Detected Yogas Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-amber-400 mb-4">Detected Yogas</h2>
              {yogaList.length === 0 ? (
                <p className="text-slate-400">No yogas detected for this chart.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="py-2.5 px-3">Yoga</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Planets</th>
                        <th className="py-2.5 px-3">Strength</th>
                        <th className="py-2.5 px-3">Domains</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {yogaList.map((y, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="py-3 px-3 font-semibold text-slate-200">{y.name}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-1 rounded text-xs font-bold ${
                                y.status === 'FORMED'
                                  ? 'bg-emerald-500/20 text-emerald-400'
                                  : y.status === 'WEAKENED'
                                  ? 'bg-amber-500/20 text-amber-400'
                                  : 'bg-rose-500/20 text-rose-400'
                              }`}
                            >
                              {y.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-slate-300">{y.planets.join(', ')}</td>
                          <td className="py-3 px-3 font-mono text-amber-300">{y.strength}</td>
                          <td className="py-3 px-3 text-slate-400">{y.domains.map(titleize).join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Core Alignment Narrative */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h2 className="text-lg font-bold text-amber-400">The Core Alignment</h2>
              <p className="text-slate-300 leading-relaxed">
                Your outward approach is governed by a{' '}
                <strong className="text-amber-300">{lagnaName || '—'}</strong> Ascendant
                {moonNak ? (
                  <>
                    , while your Moon rests in <strong className="text-amber-300">{moonNak}</strong>{' '}
                    Nakshatra — blending external experience with internal intuitive focus.
                  </>
                ) : (
                  '.'
                )}
              </p>
              {(Object.keys(elementalBalance).length > 0 || Object.keys(dignityMap).length > 0) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  {Object.keys(elementalBalance).length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-2 text-slate-400">ELEMENTAL BALANCE</p>
                      <div className="flex gap-3 flex-wrap">
                        {Object.entries(elementalBalance).map(([elem, count]) => (
                          <div key={elem} className="flex items-center gap-1.5">
                            <span className="text-sm">
                              {elem === 'fire' ? '🔥' : elem === 'earth' ? '🌍' : elem === 'air' ? '💨' : '💧'}
                            </span>
                            <span className="text-xs capitalize text-slate-200">{elem}</span>
                            <span className="text-xs font-bold text-amber-300">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {Object.keys(dignityMap).length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-2 text-slate-400">PLANETARY DIGNITIES</p>
                      <div className="flex gap-2 flex-wrap">
                        {Object.entries(dignityMap).map(([planet, dignity]) => (
                          <span
                            key={planet}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700"
                          >
                            {titleize(planet)}: {dignity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Synthesis Blueprint Content */}
            {effectiveSynthesisContent && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <h2 className="text-lg font-bold text-amber-400">Cosmic Synthesis Blueprint</h2>
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ children }) => <h3 className="text-xl font-bold text-amber-400 mb-4">{children}</h3>,
                      h2: ({ children }) => <h4 className="text-lg font-semibold text-amber-300 mb-3">{children}</h4>,
                      p: ({ children }) => <p className="text-slate-300 leading-relaxed mb-4">{children}</p>,
                      strong: ({ children }) => <strong className="text-amber-300">{children}</strong>,
                      ul: ({ children }) => <ul className="list-disc list-inside text-slate-300 space-y-2 mb-4">{children}</ul>,
                      li: ({ children }) => <li className="ml-2">{children}</li>,
                    }}
                  >
                    {effectiveSynthesisContent}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: COSMIC TIMELINE */}
        {activeTab === 'timeline' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-amber-400 mb-1">Vimshottari Dasha Timeline</h2>
              <p className="text-xs text-slate-400">Planetary operating cycles and activation windows</p>
            </div>

            {deepDasha ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400 uppercase tracking-wide">Current Mahadasha (MD)</p>
                    <p className="text-lg font-bold text-amber-300 mt-1">
                      {titleize(deepDasha.md?.lord || '—')} Dasha
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {formatUtcDate(deepDasha.md?.start_utc)} – {formatUtcDate(deepDasha.md?.end_utc)}
                    </p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400 uppercase tracking-wide">Antardasha (AD)</p>
                    <p className="text-lg font-bold text-amber-300 mt-1">
                      {titleize(deepDasha.ad?.lord || '—')} within {titleize(deepDasha.md?.lord || '—')}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {formatUtcDate(deepDasha.ad?.start_utc)} – {formatUtcDate(deepDasha.ad?.end_utc)}
                    </p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <p className="text-xs text-slate-400 uppercase tracking-wide">Pratyantardasha (PD)</p>
                    <p className="text-lg font-bold text-amber-300 mt-1">
                      {titleize(deepDasha.pd?.lord || '—')} Sub-period
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {formatUtcDate(deepDasha.pd?.start_utc)} – {formatUtcDate(deepDasha.pd?.end_utc)}
                    </p>
                  </div>
                </div>

                {adTimeline.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">
                      Antardasha periods within the {titleize(deepDasha.md?.lord || '')} Mahadasha
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400">
                            <th className="py-2 px-3">Sub-Period Lord</th>
                            <th className="py-2 px-3">Level</th>
                            <th className="py-2 px-3">Start Date</th>
                            <th className="py-2 px-3">End Date</th>
                            <th className="py-2 px-3">Duration</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {adTimeline.map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/30">
                              <td className="py-2.5 px-3 font-semibold text-amber-300">
                                {titleize(item.lord)}
                              </td>
                              <td className="py-2.5 px-3 text-slate-400">{item.level}</td>
                              <td className="py-2.5 px-3 text-slate-300 font-mono">{formatUtcDate(item.start_utc)}</td>
                              <td className="py-2.5 px-3 text-slate-300 font-mono">{formatUtcDate(item.end_utc)}</td>
                              <td className="py-2.5 px-3 text-slate-400">{item.duration_years?.toFixed(1)} yrs</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-slate-400 text-sm">Dasha calculations unavailable for this evaluation.</p>
            )}
          </div>
        )}

        {/* TAB 3: LIFE PATHS */}
        {activeTab === 'life_paths' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-amber-400 mb-1">Life Paths &amp; Expression</h2>
              <p className="text-xs text-slate-400">Key life sectors activated by formed planetary yogas</p>
            </div>
            {lifePathDomains.length === 0 ? (
              <p className="text-slate-400 text-sm">No active life path domains found for this chart.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {lifePathDomains.map(({ domain, yogas }) => (
                  <div key={domain} className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2">
                    <h3 className="text-sm font-semibold text-amber-300">{domain}</h3>
                    <p className="text-xs text-slate-400">Activated by:</p>
                    <ul className="space-y-1">
                      {yogas.map((y, idx) => (
                        <li key={idx} className="text-xs text-slate-200 flex justify-between">
                          <span>{y.name}</span>
                          <span className="font-mono text-amber-400/80">{y.strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: CIRCLE */}
        {activeTab === 'circle' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-amber-400 mb-1">My Circle &amp; Relationships</h2>
              <p className="text-xs text-slate-400">The 7th house and relational dynamics</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wide">7th House Lord</p>
                <p className="text-lg font-bold text-amber-300">{seventhLord ? titleize(seventhLord) : '—'}</p>
                <p className="text-xs text-slate-400">Governs partnership harmony and collaborative dynamics.</p>
              </div>
              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wide">7th House Occupants</p>
                <p className="text-sm font-semibold text-slate-200">
                  {seventhOccupants.length > 0 ? seventhOccupants.join(', ') : 'None (clean slate)'}
                </p>
                <p className="text-xs text-slate-400">
                  {seventhOccupants.length > 0
                    ? 'Planets in the 7th cast direct focus onto one-on-one bonds.'
                    : 'An unoccupied 7th indicates relationships develop primarily through the house lord.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: REMEDIES / PARIHARA */}
        {activeTab === 'alignment' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-amber-400 mb-1">Parihara (Remedial Measures)</h2>
              <p className="text-xs text-slate-400">Classical corrective actions for afflicted and key planetary energies</p>
            </div>

            {lagnaLord && (
              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
                <h3 className="text-sm font-semibold text-amber-300">
                  Lagna Lord Strengthening: {titleize(lagnaLord)}
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block">Mantra</span>
                    <span className="font-semibold text-slate-200">{lagnaLordRemedy.mantra}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Gemstone</span>
                    <span className="font-semibold text-slate-200">{lagnaLordRemedy.gemstone}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Favorable Day</span>
                    <span className="font-semibold text-slate-200">{lagnaLordRemedy.day}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Colors</span>
                    <span className="font-semibold text-slate-200">{lagnaLordRemedy.colors}</span>
                  </div>
                </div>
              </div>
            )}

            {afflictedPlanets.length > 0 ? (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-300">Planetary Considerations</h3>
                {afflictedPlanets.map(([planet, d]: [string, any]) => {
                  const remedy = PLANET_REMEDIES[planet.toUpperCase()] || {
                    mantra: 'Om Namah Shivaya',
                    gemstone: 'Consult an astrologer',
                    day: '—',
                    colors: '—',
                  };
                  return (
                    <div key={planet} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold text-amber-400">{titleize(planet)}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">
                          {d?.dignity || 'Combust'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-300">
                        <div>
                          <span className="text-slate-400 block">Mantra:</span> {remedy.mantra}
                        </div>
                        <div>
                          <span className="text-slate-400 block">Day:</span> {remedy.day}
                        </div>
                        <div>
                          <span className="text-slate-400 block">Gemstone:</span> {remedy.gemstone}
                        </div>
                        <div>
                          <span className="text-slate-400 block">Colors:</span> {remedy.colors}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs text-slate-400">
                <p className="text-sm font-semibold text-emerald-400 mb-1">General Practice</p>
                No severely debilitated planets identified. Regular meditation, charity on favorable days, and
                harmonious daily routines remain beneficial.
              </div>
            )}
          </div>
        )}

        {/* TAB 6: LUCKY ELEMENTS */}
        {activeTab === 'lucky_elements' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-amber-400 mb-1">Lucky Elements &amp; Alignments</h2>
              <p className="text-xs text-slate-400">Favorable directions, colors, and planetary days</p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Lagna Sign</span>
                <span className="text-sm font-bold text-amber-300">{lagnaName || '—'}</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Moon Nakshatra</span>
                <span className="text-sm font-bold text-amber-300">{moonNak || '—'}</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Lagna Lord Day</span>
                <span className="text-sm font-bold text-slate-200">{lagnaLordRemedy.day}</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Harmonious Colors</span>
                <span className="text-sm font-bold text-slate-200">{lagnaLordRemedy.colors}</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Supporting Gemstone</span>
                <span className="text-sm font-bold text-slate-200">{lagnaLordRemedy.gemstone}</span>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Primary Mantra</span>
                <span className="text-xs font-mono text-amber-400">{lagnaLordRemedy.mantra}</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: CHARTS */}
        {activeTab === 'charts' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <h2 className="text-lg font-bold text-amber-400">Divisional Charts</h2>
            {evaluationData ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* D1 Rasi Chart */}
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">D1 Rasi Chart (Birth Chart)</h3>
                  {hasD1Data ? (
                    <SvgChartRenderer
                      planets={extractChartPlanets(evaluationData, 'D1')}
                      chartStyle="NORTH_INDIAN"
                      vargaType="D1"
                      width={400}
                      height={400}
                    />
                  ) : (
                    <p className="text-slate-400 text-sm py-8 text-center">
                      Planetary positions unavailable for this evaluation.
                    </p>
                  )}
                </div>

                {/* D9 Navamsa Chart */}
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">D9 Navamsa Chart (Soul Chart)</h3>
                  {hasNavamshaData ? (
                    <SvgChartRenderer
                      planets={extractChartPlanets(evaluationData, 'D9')}
                      chartStyle="NORTH_INDIAN"
                      vargaType="D9"
                      width={400}
                      height={400}
                    />
                  ) : (
                    <p className="text-slate-400 text-sm py-8 text-center">
                      Navamsha positions unavailable for this evaluation.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-slate-400">Run an evaluation to view charts.</p>
            )}
          </div>
        )}

        {/* TAB 8: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-amber-400">Chart Synthesis Report</h2>
              {evaluationData && (
                <button
                  onClick={() => {
                    if (onGenerateReport) {
                      void onGenerateReport();
                    } else {
                      void fetchSynthesis();
                    }
                  }}
                  disabled={effectiveSynthesizing}
                  className="bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {effectiveSynthesizing ? 'Consulting the Cosmos…' : 'Generate Full Report'}
                </button>
              )}
            </div>
            {effectiveSynthesisError && (
              <div
                className="p-4 rounded-lg border mb-4"
                style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
              >
                <p className="text-sm font-medium text-red-300">Report generation failed</p>
                <p className="text-xs text-slate-400 mt-1">{effectiveSynthesisError}</p>
              </div>
            )}
            {effectiveSynthesisContent ? (
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h3 className="text-xl font-bold text-amber-400 mb-4">{children}</h3>,
                    h2: ({ children }) => <h4 className="text-lg font-semibold text-amber-300 mb-3">{children}</h4>,
                    p: ({ children }) => <p className="text-slate-300 leading-relaxed mb-4">{children}</p>,
                    strong: ({ children }) => <strong className="text-amber-300">{children}</strong>,
                    ul: ({ children }) => <ul className="list-disc list-inside text-slate-300 space-y-2 mb-4">{children}</ul>,
                    li: ({ children }) => <li className="ml-2">{children}</li>,
                  }}
                >
                  {synthesisContent}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-slate-400">
                No report synthesis generated yet. Click “Generate Full Report” to create one.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default EvaluationReportTabs;
