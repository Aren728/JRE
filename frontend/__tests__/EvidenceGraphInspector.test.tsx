import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import EvidenceGraphInspector, {
  type EvidenceGraphResponse,
} from '@/components/evidence/EvidenceGraphInspector';

const GRAPH: EvidenceGraphResponse = {
  graph_id: 'graph-test-0000-0000',
  fixture_id: 'chart_001_pilot',
  node_count: 5,
  edge_count: 3,
  nodes: [
    { node_id: 'EV-0-abc', node_type: 'EVALUATION', payload: { prediction_id: 'P-x' } },
    {
      node_id: 'R-0-yoga001',
      node_type: 'RULE',
      payload: { yoga_name: 'Gajakesari', rule_id: 'YOGA-001', status: 'FORMED' },
    },
    { node_id: 'F-0-sun', node_type: 'FACT', labels: ['FACT'], payload: { fact_id: 'F-101' } },
    {
      node_id: 'CIT-0',
      node_type: 'CITATION',
      payload: { citation_id: 'CIT-BPHS-34-SL-12', canonical_ref: 'BPHS Ch. 34 Sl. 12' },
    },
    { node_id: 'temporal', node_type: 'TEMPORAL', payload: { dasha_active: 'Venus/Sun' } },
  ],
  edges: [
    {
      edge_id: 'E-EV-0',
      source: 'EV-0-abc',
      target: 'R-0-yoga001',
      relationship: 'ESTABLISHED_BY',
    },
    { edge_id: 'E-R-0-a', source: 'R-0-yoga001', target: 'F-0-sun', relationship: 'SUPPORTS' },
    { edge_id: 'E-C-0', source: 'R-0-yoga001', target: 'CIT-0', relationship: 'DERIVES_FROM' },
  ],
  engine_version: 'v1.0.0-beta',
};

describe('EvidenceGraphInspector', () => {
  it('renders the loading state', () => {
    render(<EvidenceGraphInspector graph={null} loading />);
    expect(screen.getByTestId('evidence-graph-loading')).toBeInTheDocument();
  });

  it('renders the error state', () => {
    render(<EvidenceGraphInspector graph={null} error="boom" />);
    expect(screen.getByTestId('evidence-graph-error')).toHaveTextContent('boom');
  });

  it('renders the empty state without data', () => {
    render(<EvidenceGraphInspector graph={null} />);
    expect(screen.getByTestId('evidence-graph-empty')).toBeInTheDocument();
  });

  it('renders all node layers with counts and totals', () => {
    render(<EvidenceGraphInspector graph={GRAPH} />);
    expect(screen.getByTestId('layer-EVALUATION')).toBeInTheDocument();
    expect(screen.getByTestId('layer-RULE')).toBeInTheDocument();
    expect(screen.getByTestId('layer-FACT')).toBeInTheDocument();
    expect(screen.getByTestId('layer-TEMPORAL')).toBeInTheDocument();
    expect(screen.getByTestId('layer-CITATION')).toBeInTheDocument();
    expect(screen.getByText(/5 nodes · 3 edges/)).toBeInTheDocument();
  });

  it('shows the classical citation payload on a CITATION node', () => {
    render(<EvidenceGraphInspector graph={GRAPH} />);
    expect(screen.getByText(/CIT-BPHS-34-SL-12/)).toBeInTheDocument();
    expect(screen.getByText(/BPHS Ch\. 34 Sl\. 12/)).toBeInTheDocument();
  });

  it('opens a node inspector with payload and provenance chain on select', () => {
    render(<EvidenceGraphInspector graph={GRAPH} />);
    fireEvent.click(screen.getByTestId('node-R-0-yoga001'));
    expect(screen.getByTestId('node-inspector')).toBeInTheDocument();
    expect(screen.getByTestId('node-payload')).toHaveTextContent('YOGA-001');
    // The rule traces upward to the EVALUATION root via ESTABLISHED_BY.
    const chain = screen.getByTestId('provenance-chain');
    expect(chain).toHaveTextContent('R-0-yoga001');
    expect(chain).toHaveTextContent('EV-0-abc');
  });

  it('toggles a layer off and back on', () => {
    render(<EvidenceGraphInspector graph={GRAPH} />);
    expect(screen.getByTestId('layer-FACT')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('layer-toggle-FACT'));
    expect(screen.queryByTestId('layer-FACT')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('layer-toggle-FACT'));
    expect(screen.getByTestId('layer-FACT')).toBeInTheDocument();
  });
});
