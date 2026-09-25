'use client';

// ── EvidenceGraphInspector — Phase 7 JRE Observatory ─────────────────────
// Renders the deterministic Phase 3 evidence DAG served by
// GET /api/v1/evidence/graph/{fixture_id} as an interactive node tree:
//
//   Prediction (EVALUATION) ──► Rules ──► Facts ──► Classical References
//
// Pure presentation: the parent page owns fetching; this component takes
// the parsed EvidenceGraphResponse. Node layers are collapsible, nodes
// are selectable (payload inspector), and the full provenance chain of
// the selected rule is traceable through the directed edges.

import React, { useMemo, useState } from 'react';

// ── Types (mirror of jrs.api.schemas EvidenceGraph* DTOs) ─────────────────

export interface EvidenceGraphNode {
  node_id: string;
  node_type: string;
  labels?: string[];
  payload?: Record<string, unknown>;
  parent?: string | null;
}

export interface EvidenceGraphEdge {
  edge_id: string;
  source: string;
  target: string;
  relationship: string;
  weight?: number;
  metadata?: Record<string, unknown>;
}

export interface EvidenceGraphResponse {
  graph_id: string;
  fixture_id: string;
  node_count: number;
  edge_count: number;
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
  engine_version?: string;
}

export interface EvidenceGraphInspectorProps {
  graph: EvidenceGraphResponse | null;
  loading?: boolean;
  error?: string | null;
}

// ── Layer constants ────────────────────────────────────────────────────────

const LAYER_ORDER = ['EVALUATION', 'RULE', 'FACT', 'TEMPORAL', 'CITATION', 'ANALYSIS'] as const;

const LAYER_META: Record<string, { label: string; color: string; description: string }> = {
  EVALUATION: {
    label: 'Prediction',
    color: '#fbbf24',
    description: 'The single evaluation root produced by the 5-layer pipeline.',
  },
  RULE: {
    label: 'Rules',
    color: '#f472b6',
    description: 'Classical yoga rules (YOGA-*) established by the evaluation.',
  },
  FACT: {
    label: 'Facts',
    color: '#22d3ee',
    description: 'Planetary-state facts (F-*) and calculation-module facts (FACT-*).',
  },
  TEMPORAL: {
    label: 'Dasha / Transit',
    color: '#34d399',
    description: 'Temporal layer: active dasha state and transit activations.',
  },
  CITATION: {
    label: 'Classical References',
    color: '#c084fc',
    description: 'Literature citations (BPHS chapters/verses) backing each rule.',
  },
  ANALYSIS: {
    label: 'Analysis',
    color: '#94a3b8',
    description: 'Derived analysis nodes.',
  },
};

function layerMeta(nodeType: string) {
  return LAYER_META[nodeType] ?? { label: nodeType, color: '#94a3b8', description: '' };
}

function summarizePayload(node: EvidenceGraphNode): string {
  const p = node.payload ?? {};
  const parts: string[] = [];
  if (typeof p.yoga_name === 'string') parts.push(p.yoga_name);
  if (typeof p.rule_id === 'string') parts.push(p.rule_id);
  if (typeof p.fact_id === 'string') parts.push(p.fact_id);
  if (typeof p.citation_id === 'string') parts.push(p.citation_id);
  if (typeof p.canonical_ref === 'string') parts.push(p.canonical_ref);
  if (typeof p.status === 'string') parts.push(p.status);
  if (typeof p.dasha_active === 'string') parts.push(p.dasha_active);
  for (const label of node.labels ?? []) {
    if (label !== node.node_type && !parts.includes(label)) parts.push(label);
  }
  return parts.join(' · ') || node.node_id;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function EvidenceGraphInspector({
  graph,
  loading = false,
  error = null,
}: EvidenceGraphInspectorProps) {
  const [hiddenLayers, setHiddenLayers] = useState<Set<string>>(new Set());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const layers = useMemo(() => {
    if (!graph) return [];
    const byType = new Map<string, EvidenceGraphNode[]>();
    for (const node of graph.nodes) {
      const list = byType.get(node.node_type) ?? [];
      list.push(node);
      byType.set(node.node_type, list);
    }
    return LAYER_ORDER.filter((t) => byType.has(t)).map((t) => ({
      type: t,
      nodes: byType.get(t) ?? [],
    }));
  }, [graph]);

  const selectedNode = useMemo(
    () => graph?.nodes.find((n) => n.node_id === selectedNodeId) ?? null,
    [graph, selectedNodeId]
  );

  const incoming = useMemo(
    () => (graph && selectedNodeId ? graph.edges.filter((e) => e.target === selectedNodeId) : []),
    [graph, selectedNodeId]
  );
  const outgoing = useMemo(
    () => (graph && selectedNodeId ? graph.edges.filter((e) => e.source === selectedNodeId) : []),
    [graph, selectedNodeId]
  );

  const tracePath = useMemo(() => {
    // Trace the full provenance chain of the selected node upward via
    // incoming edges (selected ──► … ──► EVALUATION root).
    if (!graph || !selectedNode) return [];
    const path: EvidenceGraphNode[] = [selectedNode];
    const seen = new Set<string>([selectedNode.node_id]);
    let frontier: string[] = [selectedNode.node_id];
    while (frontier.length) {
      const next: string[] = [];
      for (const edge of graph.edges) {
        if (frontier.includes(edge.target) && !seen.has(edge.source)) {
          seen.add(edge.source);
          next.push(edge.source);
        }
      }
      const nodes = graph.nodes.filter((n) => next.includes(n.node_id));
      path.push(...nodes);
      frontier = next;
    }
    return path;
  }, [graph, selectedNode]);

  if (loading) {
    return (
      <div data-testid="evidence-graph-loading" className="animate-pulse text-sm text-slate-400">
        Building evidence graph…
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="evidence-graph-error" className="text-sm text-red-400" role="alert">
        {error}
      </div>
    );
  }

  if (!graph) {
    return (
      <div data-testid="evidence-graph-empty" className="text-sm text-slate-400">
        No evidence graph loaded.
      </div>
    );
  }

  return (
    <div data-testid="evidence-graph-inspector" className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-slate-200">
          Evidence Graph {graph.graph_id.slice(0, 12)}
        </span>
        <span className="text-xs text-slate-400">
          {graph.node_count} nodes · {graph.edge_count} edges
        </span>
        {layers.map(({ type }) => (
          <button
            key={type}
            type="button"
            data-testid={`layer-toggle-${type}`}
            onClick={() =>
              setHiddenLayers((prev) => {
                const next = new Set(prev);
                if (next.has(type)) next.delete(type);
                else next.add(type);
                return next;
              })
            }
            className="rounded px-2 py-0.5 text-xs"
            style={{
              border: `1px solid ${layerMeta(type).color}`,
              opacity: hiddenLayers.has(type) ? 0.35 : 1,
              color: layerMeta(type).color,
            }}
            title={layerMeta(type).description}
          >
            {layerMeta(type).label}
          </button>
        ))}
      </div>

      {layers
        .filter(({ type }) => !hiddenLayers.has(type))
        .map(({ type, nodes }) => (
          <div key={type} data-testid={`layer-${type}`} className="space-y-1">
            <div className="text-xs uppercase tracking-wide" style={{ color: layerMeta(type).color }}>
              {layerMeta(type).label} ({nodes.length})
            </div>
            {nodes.map((node) => (
              <button
                key={node.node_id}
                type="button"
                data-testid={`node-${node.node_id}`}
                onClick={() =>
                  setSelectedNodeId((prev) => (prev === node.node_id ? null : node.node_id))
                }
                className="block w-full rounded px-2 py-1 text-left"
                style={{
                  border: `1px solid ${layerMeta(type).color}`,
                  background: selectedNodeId === node.node_id ? 'rgba(255,255,255,0.08)' : 'transparent',
                }}
              >
                <span className="font-mono text-xs text-slate-300">{node.node_id}</span>
                <span className="ml-2 text-xs text-slate-400">{summarizePayload(node)}</span>
              </button>
            ))}
          </div>
        ))}

      {selectedNode && (
        <div data-testid="node-inspector" className="rounded border border-slate-600 p-2">
          <div className="font-semibold text-slate-200">Selected: {selectedNode.node_id}</div>
          <div className="text-xs text-slate-400">type: {selectedNode.node_type}</div>
          <pre
            data-testid="node-payload"
            className="mt-1 overflow-x-auto rounded bg-slate-900 p-2 text-xs text-slate-300"
          >
            {JSON.stringify(selectedNode.payload ?? {}, null, 2)}
          </pre>
          <div className="mt-1 text-xs text-slate-400">
            incoming: {incoming.length} · outgoing: {outgoing.length}
          </div>
          {tracePath.length > 1 && (
            <div data-testid="provenance-chain" className="mt-1 text-xs text-slate-300">
              provenance chain:{' '}
              {tracePath.map((n) => n.node_id).join(' ──► ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
