import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ObservatoryDashboard from '@/components/observatory/ObservatoryDashboard';
import type { EvidenceGraphResponse } from '@/components/evidence/EvidenceGraphInspector';
import type { AshtakavargaReport } from '@/components/ashtakavarga/SAVViewer';

const GRAPH: EvidenceGraphResponse = {
  graph_id: 'graph-test-0000-0000',
  fixture_id: 'chart_001_pilot',
  node_count: 2,
  edge_count: 1,
  nodes: [
    { node_id: 'EV-0-abc', node_type: 'EVALUATION', payload: {} },
    { node_id: 'R-0-yoga001', node_type: 'RULE', payload: { yoga_name: 'Gajakesari' } },
  ],
  edges: [
    {
      edge_id: 'E-EV-0',
      source: 'EV-0-abc',
      target: 'R-0-yoga001',
      relationship: 'ESTABLISHED_BY',
    },
  ],
};

const SAV: AshtakavargaReport = {
  version: '1.0.0',
  anchor_signs: {},
  fact_ids: [],
  bav: {},
  sav: [28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
  shodhita_bav: {},
  shodhita_sav: [28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
  pinda: {},
};

const YOGAS = [
  {
    id: 'yoga-1',
    name: 'Gajakesari',
    category: 'RAJA' as const,
    description: 'Jupiter in kendra from Moon',
    participatingPlanets: ['JUPITER', 'MOON'],
    status: 'ACTIVE_DASHA' as const,
    strengthScore: 0.8,
    houseCombination: 'Jupiter 4th from Moon',
    ruleConditions: [{ conditionText: 'Jupiter kendra from Moon', isMet: true }],
  },
];

describe('ObservatoryDashboard', () => {
  it('renders the loading state', () => {
    render(
      <ObservatoryDashboard
        evidenceGraph={null}
        dashaTree={[]}
        yogas={[]}
        savReport={null}
        loading
      />
    );
    expect(screen.getByTestId('observatory-loading')).toBeInTheDocument();
  });

  it('renders the error state', () => {
    render(
      <ObservatoryDashboard
        evidenceGraph={null}
        dashaTree={[]}
        yogas={[]}
        savReport={null}
        error="boom"
      />
    );
    expect(screen.getByTestId('observatory-error')).toHaveTextContent('boom');
  });

  it('renders the empty state without data', () => {
    render(
      <ObservatoryDashboard
        evidenceGraph={null}
        dashaTree={[]}
        yogas={[]}
        savReport={null}
      />
    );
    expect(screen.getByTestId('observatory-empty')).toBeInTheDocument();
  });

  it('renders all four forensic sections when data is present', () => {
    render(
      <ObservatoryDashboard
        evidenceGraph={GRAPH}
        dashaTree={[
          {
            id: 'md-1',
            planet: 'Venus',
            level: 'MD',
            startDate: '2019-12-04',
            endDate: '2039-12-04',
            durationDays: 7305,
            subPeriods: [],
          },
        ]}
        yogas={YOGAS}
        savReport={SAV}
        targetDate="2026-01-01"
        activeDashaLords={['Venus']}
      />
    );
    expect(screen.getByTestId('observatory-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('section-evidence')).toBeInTheDocument();
    expect(screen.getByTestId('section-dasha')).toBeInTheDocument();
    expect(screen.getByTestId('section-yogas')).toBeInTheDocument();
    expect(screen.getByTestId('section-ashtakavarga')).toBeInTheDocument();
    // The evidence inspector renders inside the dashboard.
    expect(screen.getByTestId('evidence-graph-inspector')).toBeInTheDocument();
  });

  it('toggles a section off and back on', () => {
    render(
      <ObservatoryDashboard
        evidenceGraph={GRAPH}
        dashaTree={[]}
        yogas={YOGAS}
        savReport={SAV}
        targetDate="2026-01-01"
      />
    );
    expect(screen.getByTestId('section-dasha')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('section-toggle-dasha'));
    expect(screen.queryByTestId('section-dasha')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('section-toggle-dasha'));
    expect(screen.getByTestId('section-dasha')).toBeInTheDocument();
  });
});
