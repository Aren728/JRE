'use client';

// ── ObservatoryDashboard — Phase 7 JRE Observatory executive view ────────
// Integrates the four forensic viewers into one diagnostic surface:
//
//   EvidenceGraphInspector  Prediction ──► Facts ──► Rules ──► References
//   DashaTreeViewer         Vimshottari timing tree (MD/AD/PD/SD)
//   YogaInspector           Yoga formation/activation inspector
//   SAVViewer               Ashtakavarga bindu strength table
//
// Pure presentation: the owning page fetches (evaluation response,
// evidence graph, dasha tree) and passes shaped props. No data fetching
// and no calculation here — consistent with the Phase 5 exit criterion
// that no calculation module depends on frontend state.

import React, { useMemo, useState } from 'react';
import EvidenceGraphInspector, {
  type EvidenceGraphResponse,
} from '@/components/evidence/EvidenceGraphInspector';
import DashaTreeViewer, { type DashaPeriod } from '@/components/dasha/DashaTreeViewer';
import YogaInspector, { type YogaEvaluation } from '@/components/yogas/YogaInspector';
import SAVViewer, { type AshtakavargaReport } from '@/components/ashtakavarga/SAVViewer';

export interface ObservatoryDashboardProps {
  evidenceGraph: EvidenceGraphResponse | null;
  dashaTree: DashaPeriod[];
  yogas: YogaEvaluation[];
  savReport: AshtakavargaReport | null;
  targetDate?: string;
  activeDashaLords?: string[];
  loading?: boolean;
  error?: string | null;
}

const SECTION_ORDER = ['evidence', 'dasha', 'yogas', 'ashtakavarga'] as const;

type SectionId = (typeof SECTION_ORDER)[number];

const SECTION_LABELS: Record<SectionId, string> = {
  evidence: 'Evidence Graph',
  dasha: 'Dasha Tree',
  yogas: 'Yoga Inspector',
  ashtakavarga: 'Ashtakavarga',
};

export default function ObservatoryDashboard({
  evidenceGraph,
  dashaTree,
  yogas,
  savReport,
  targetDate,
  activeDashaLords = [],
  loading = false,
  error = null,
}: ObservatoryDashboardProps) {
  const [visible, setVisible] = useState<Set<SectionId>>(new Set(SECTION_ORDER));

  const hasAnyData = useMemo(
    () =>
      Boolean(evidenceGraph) || dashaTree.length > 0 || yogas.length > 0 || Boolean(savReport),
    [evidenceGraph, dashaTree, yogas, savReport]
  );

  if (loading) {
    return (
      <div data-testid="observatory-loading" className="animate-pulse text-sm text-slate-400">
        Loading Observatory…
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="observatory-error" className="text-sm text-red-400" role="alert">
        {error}
      </div>
    );
  }

  if (!hasAnyData) {
    return (
      <div data-testid="observatory-empty" className="text-sm text-slate-400">
        No Observatory data loaded — evaluate a chart to populate the forensic views.
      </div>
    );
  }

  return (
    <div data-testid="observatory-dashboard" className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {SECTION_ORDER.map((section) => (
          <button
            key={section}
            type="button"
            data-testid={`section-toggle-${section}`}
            onClick={() =>
              setVisible((prev) => {
                const next = new Set(prev);
                if (next.has(section)) next.delete(section);
                else next.add(section);
                return next;
              })
            }
            className="rounded border border-slate-600 px-2 py-0.5 text-xs text-slate-300"
            style={{ opacity: visible.has(section) ? 1 : 0.35 }}
          >
            {SECTION_LABELS[section]}
          </button>
        ))}
      </div>

      {visible.has('evidence') && (
        <section data-testid="section-evidence" aria-label="Evidence Graph">
          <EvidenceGraphInspector graph={evidenceGraph} />
        </section>
      )}

      {visible.has('dasha') && (
        <section data-testid="section-dasha" aria-label="Dasha Tree">
          <DashaTreeViewer
            dashaTree={dashaTree}
            targetDate={targetDate ?? new Date().toISOString().split('T')[0]}
            depthLimit="SD"
            highlightedPlanet={activeDashaLords[0] ?? null}
          />
        </section>
      )}

      {visible.has('yogas') && (
        <section data-testid="section-yogas" aria-label="Yoga Inspector">
          <YogaInspector
            yogas={yogas}
            activeDashaLords={activeDashaLords}
            minStrengthCutoff={0}
            highlightedBodies={activeDashaLords}
          />
        </section>
      )}

      {visible.has('ashtakavarga') && (
        <section data-testid="section-ashtakavarga" aria-label="Ashtakavarga">
          <SAVViewer report={savReport} showShodhita />
        </section>
      )}
    </div>
  );
}
