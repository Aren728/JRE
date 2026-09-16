'use client';

import React, { useMemo, useState } from 'react';

// ── Type Definitions ──────────────────────────────────────────────────────────

export interface DashaPeriod {
  id: string;
  planet: string;
  level: 'MD' | 'AD' | 'PD' | 'SD';
  startDate: string; // ISO format: YYYY-MM-DD
  endDate: string;
  durationDays: number;
  subPeriods?: DashaPeriod[];
}

interface DashaTreeViewerProps {
  dashaTree: DashaPeriod[];
  targetDate: string; // Active inspection date
  depthLimit: 'MD' | 'AD' | 'PD' | 'SD';
  onSelectDateRange?: (startDate: string, endDate: string, path: string[]) => void;
}

// ── Constants ────────────────────────────────────────────────────────────────

const PLANET_SYMBOLS: Record<string, string> = {
  'SUN': '☉',
  'MOON': '☽',
  'MARS': '♂',
  'MERCURY': '☿',
  'JUPITER': '♃',
  'VENUS': '♀',
  'SATURN': '♄',
  'RAHU': '☊',
  'KETU': '☋',
};

const DASHA_DURATIONS_YEARS: Record<string, number> = {
  'KETU': 7,
  'VENUS': 20,
  'SUN': 6,
  'MOON': 10,
  'MARS': 7,
  'RAHU': 18,
  'JUPITER': 16,
  'SATURN': 19,
  'MERCURY': 17,
};

const LEVEL_COLORS: Record<string, string> = {
  'MD': 'var(--cosmic-gold)',
  'AD': '#f472b6',
  'PD': '#22d3ee',
  'SD': '#34d399',
};

const LEVEL_LABELS: Record<string, string> = {
  'MD': 'Mahadasha',
  'AD': 'Antardasha',
  'PD': 'Pratyantardasha',
  'SD': 'Sookshma Dasha',
};

const QUICK_DATES: { label: string; date: string }[] = [
  { label: 'Today', date: new Date().toISOString().split('T')[0] },
  { label: '1 Year Ago', date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] },
  { label: '1 Year Ahead', date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] },
  { label: 'Birth Date', date: '1990-01-15' },
  { label: '5 Years Ahead', date: new Date(Date.now() + 5 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function parseDate(dateStr: string): Date {
  return new Date(dateStr + 'T00:00:00Z');
}

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

function daysBetween(start: string, end: string): number {
  const s = parseDate(start).getTime();
  const e = parseDate(end).getTime();
  return Math.round((e - s) / (24 * 60 * 60 * 1000));
}

function progressPercentage(targetDate: Date, startDate: string, endDate: string): number {
  const target = targetDate.getTime();
  const s = parseDate(startDate).getTime();
  const e = parseDate(endDate).getTime();
  if (e === s) return 0;
  return Math.max(0, Math.min(100, ((target - s) / (e - s)) * 100));
}

function isDateInRange(targetDate: Date, startDate: string, endDate: string): boolean {
  const t = targetDate.getTime();
  const s = parseDate(startDate).getTime();
  const e = parseDate(endDate).getTime();
  return t >= s && t < e;
}

function generateId(level: string, planet: string, index: number): string {
  return `${level}-${planet}-${index}`;
}

// ── Depth Limit Check ────────────────────────────────────────────────────────

function shouldShowChildren(level: string, depthLimit: string): boolean {
  const order = ['MD', 'AD', 'PD', 'SD'];
  const currentIdx = order.indexOf(level);
  const limitIdx = order.indexOf(depthLimit);
  return currentIdx < limitIdx;
}

// ── Tree Node Component ──────────────────────────────────────────────────────

interface TreeNodeProps {
  period: DashaPeriod;
  targetDate: Date;
  depthLimit: string;
  expandedNodes: Set<string>;
  activePath: string[];
  onToggle: (id: string) => void;
  onSelect: (period: DashaPeriod) => void;
  level: number;
}

function TreeNode({
  period,
  targetDate,
  depthLimit,
  expandedNodes,
  activePath,
  onToggle,
  onSelect,
  level: indentLevel,
}: TreeNodeProps) {
  const isActive = isDateInRange(targetDate, period.startDate, period.endDate);
  const isExpanded = expandedNodes.has(period.id);
  const hasChildren = shouldShowChildren(period.level, depthLimit) && period.subPeriods && period.subPeriods.length > 0;
  const progress = progressPercentage(targetDate, period.startDate, period.endDate);
  const isInActivePath = activePath.includes(period.id);

  return (
    <div className="relative" style={{ marginLeft: indentLevel * 16 }}>
      {/* Node row */}
      <div
        className="flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all duration-200 group"
        style={{
          background: isActive
            ? 'rgba(197, 168, 128, 0.12)'
            : isInActivePath
            ? 'rgba(197, 168, 128, 0.05)'
            : 'transparent',
          border: isActive
            ? '1.5px solid var(--cosmic-gold)'
            : isInActivePath
            ? '1px solid rgba(197, 168, 128, 0.2)'
            : '1px solid transparent',
          boxShadow: isActive
            ? '0 0 12px rgba(197, 168, 128, 0.25)'
            : 'none',
        }}
        onClick={() => onSelect(period)}
      >
        {/* Expand/collapse button */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggle(period.id);
          }}
          className="w-5 h-5 flex items-center justify-center rounded hover:bg-white/10 transition-colors shrink-0"
          style={{
            color: hasChildren ? 'var(--cosmic-muted)' : 'transparent',
          }}
        >
          {hasChildren && (
            <svg
              width="10"
              height="10"
              viewBox="0 0 10 10"
              fill="none"
              style={{
                transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease',
              }}
            >
              <path d="M3 2L7 5L3 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>

        {/* Planet symbol */}
        <span
          className="text-lg shrink-0"
          style={{ color: LEVEL_COLORS[period.level] || 'var(--cosmic-text)' }}
        >
          {PLANET_SYMBOLS[period.planet] || '?'}
        </span>

        {/* Planet name & level */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              className="font-semibold text-sm truncate"
              style={{ color: isActive ? 'var(--cosmic-gold)' : 'var(--cosmic-text)' }}
            >
              {period.planet}
            </span>
            <span
              className="text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0"
              style={{
                background: `${LEVEL_COLORS[period.level]}20`,
                color: LEVEL_COLORS[period.level] || 'var(--cosmic-muted)',
              }}
            >
              {period.level}
            </span>
            {isActive && (
              <span
                className="text-[9px] font-semibold px-1.5 py-0.5 rounded shrink-0"
                style={{
                  background: 'rgba(197, 168, 128, 0.2)',
                  color: 'var(--cosmic-gold)',
                }}
              >
                ACTIVE
              </span>
            )}
          </div>
          <div className="text-[10px] mt-0.5 truncate" style={{ color: 'var(--cosmic-muted)' }}>
            {LEVEL_LABELS[period.level]}
          </div>
        </div>

        {/* Date range */}
        <div className="text-[10px] text-right shrink-0" style={{ color: 'var(--cosmic-muted)' }}>
          <div>{period.startDate}</div>
          <div className="text-[9px]">→ {period.endDate}</div>
        </div>

        {/* Duration badge */}
        <div
          className="text-[9px] px-1.5 py-0.5 rounded shrink-0 text-right"
          style={{ color: 'var(--cosmic-muted)', background: 'rgba(255,255,255,0.05)' }}
        >
          {period.durationDays}d
        </div>

        {/* Progress bar indicator */}
        {isActive && (
          <div
            className="w-12 h-1.5 rounded-full overflow-hidden shrink-0"
            style={{ background: 'rgba(255,255,255,0.1)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: 'var(--cosmic-gold)',
              }}
            />
          </div>
        )}
      </div>

      {/* Progress bar detail */}
      {isActive && (
        <div className="mt-1 ml-7">
          <div className="flex items-center gap-2 text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>
            <span>Progress:</span>
            <span className="font-mono font-medium" style={{ color: 'var(--cosmic-gold)' }}>
              {Math.round(progress)}%
            </span>
            <span>·</span>
            <span>
              {Math.round((targetDate.getTime() - parseDate(period.startDate).getTime()) / (24 * 60 * 60 * 1000))} days elapsed
            </span>
          </div>
        </div>
      )}

      {/* Children */}
      {hasChildren && isExpanded && period.subPeriods && (
        <div className="mt-1">
          {period.subPeriods.map((child, idx) => (
            <TreeNode
              key={child.id}
              period={child}
              targetDate={targetDate}
              depthLimit={depthLimit}
              expandedNodes={expandedNodes}
              activePath={activePath}
              onToggle={onToggle}
              onSelect={onSelect}
              level={indentLevel + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Active Path Breadcrumbs ──────────────────────────────────────────────────

interface BreadcrumbsProps {
  path: string[];
  planetSymbols: Record<string, string>;
}

function ActiveBreadcrumbs({ path, planetSymbols }: BreadcrumbsProps) {
  if (path.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap p-2.5 rounded-lg" style={{ background: 'rgba(197,168,128,0.1)' }}>
      <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-gold)' }}>
        Active Path:
      </span>
      {path.map((id, idx) => {
        // Parse the id to get planet and level
        const parts = id.split('-');
        const planet = parts[1];
        const level = parts[0];
        const isLast = idx === path.length - 1;

        return (
          <React.Fragment key={id}>
            <span
              className="flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium"
              style={{
                background: isLast ? 'rgba(197,168,128,0.2)' : 'rgba(255,255,255,0.05)',
                color: isLast ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
              }}
            >
              <span style={{ color: LEVEL_COLORS[level] || 'var(--cosmic-muted)' }}>
                {planetSymbols[planet] || '?'}
              </span>
              <span>{planet}</span>
            </span>
            {!isLast && (
              <svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                className="shrink-0"
              >
                <path
                  d="M6 2L10 6L6 10"
                  stroke="var(--cosmic-gold)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Date Range Scrubber ──────────────────────────────────────────────────────

interface DateScrubberProps {
  targetDate: string;
  onDateChange: (date: string) => void;
  quickDates: { label: string; date: string }[];
}

function DateScrubber({ targetDate, onDateChange, quickDates }: DateScrubberProps) {
  const [customInput, setCustomInput] = useState(targetDate);

  const handleCustomDate = () => {
    if (customInput && /^\d{4}-\d{2}-\d{2}$/.test(customInput)) {
      onDateChange(customInput);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <label className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
          Timeline Scrubber
        </label>
        <span className="text-[10px] font-mono" style={{ color: 'var(--cosmic-gold)' }}>
          Selected: {targetDate}
        </span>
      </div>

      {/* Quick date buttons */}
      <div className="flex flex-wrap gap-1">
        {quickDates.map((qd) => (
          <button
            key={qd.date}
            type="button"
            onClick={() => onDateChange(qd.date)}
            className="px-2.5 py-1 text-[10px] rounded-md transition-all"
            style={{
              background: targetDate === qd.date ? 'rgba(197,168,128,0.2)' : 'rgba(255,255,255,0.05)',
              border: targetDate === qd.date ? '1px solid rgba(197,168,128,0.3)' : '1px solid transparent',
              color: targetDate === qd.date ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
            }}
          >
            {qd.label}
          </button>
        ))}
      </div>

      {/* Custom date input */}
      <div className="flex gap-1">
        <input
          type="date"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          className="flex-1 p-1.5 text-[10px] rounded border"
          style={{
            background: 'rgba(255,255,255,0.05)',
            borderColor: 'rgba(197,168,128,0.2)',
            color: 'var(--cosmic-text)',
          }}
        />
        <button
          type="button"
          onClick={handleCustomDate}
          className="px-2 py-1 text-[10px] rounded bg-blue-600/20 text-blue-400 border border-blue-600/30 hover:bg-blue-600/30 transition-colors"
        >
          Go
        </button>
      </div>
    </div>
  );
}

// ── Depth Limit Selector ─────────────────────────────────────────────────────

interface DepthSelectorProps {
  currentDepth: 'MD' | 'AD' | 'PD' | 'SD';
  onChange: (depth: 'MD' | 'AD' | 'PD' | 'SD') => void;
}

function DepthSelector({ currentDepth, onChange }: DepthSelectorProps) {
  const depths: { value: 'MD' | 'AD' | 'PD' | 'SD'; label: string }[] = [
    { value: 'MD', label: 'MD Only' },
    { value: 'AD', label: 'MD + AD' },
    { value: 'PD', label: 'MD + AD + PD' },
    { value: 'SD', label: 'Full Tree (MD→AD→PD→SD)' },
  ];

  return (
    <div className="flex items-center gap-2">
      <label className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
        Depth:
      </label>
      <select
        value={currentDepth}
        onChange={(e) => onChange(e.target.value as 'MD' | 'AD' | 'PD' | 'SD')}
        className="text-[10px] p-1.5 rounded border"
        style={{
          background: 'rgba(255,255,255,0.05)',
          borderColor: 'rgba(197,168,128,0.2)',
          color: 'var(--cosmic-text)',
        }}
      >
        {depths.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// ── Main DashaTreeViewer Component ───────────────────────────────────────────

export default function DashaTreeViewer({
  dashaTree,
  targetDate: targetDateStr,
  depthLimit,
  onSelectDateRange,
}: DashaTreeViewerProps) {
  const targetDate = useMemo(() => new Date(targetDateStr + 'T00:00:00Z'), [targetDateStr]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [depthLimitState, setDepthLimitState] = useState(depthLimit);

  // Auto-expand nodes that contain the target date
  const autoExpanded = useMemo(() => {
    const expanded = new Set<string>();

    function expandToTarget(periods: DashaPeriod[], target: Date): boolean {
      for (const period of periods) {
        if (isDateInRange(target, period.startDate, period.endDate)) {
          expanded.add(period.id);
          if (period.subPeriods && shouldShowChildren(period.level, depthLimitState)) {
            expandToTarget(period.subPeriods, target);
          }
          return true;
        }
      }
      return false;
    }

    for (const root of dashaTree) {
      expandToTarget([root], targetDate);
    }

    return expanded;
  }, [dashaTree, targetDate, depthLimitState]);

  // Merge auto-expanded with user-expanded
  const allExpanded = useMemo(() => {
    const merged = new Set(expandedNodes);
    for (const id of autoExpanded) {
      merged.add(id);
    }
    return merged;
  }, [expandedNodes, autoExpanded]);

  // Compute active path (breadcrumbs)
  const activePath = useMemo(() => {
    const path: string[] = [];

    function findActivePath(periods: DashaPeriod[], target: Date): boolean {
      for (const period of periods) {
        if (isDateInRange(target, period.startDate, period.endDate)) {
          path.push(period.id);
          if (period.subPeriods) {
            if (findActivePath(period.subPeriods, target)) {
              return true;
            }
          }
          return true;
        }
      }
      return false;
    }

    for (const root of dashaTree) {
      if (findActivePath([root], targetDate)) {
        break;
      }
    }

    return path;
  }, [dashaTree, targetDate]);

  const handleToggle = (id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelect = (period: DashaPeriod) => {
    onSelectDateRange?.(period.startDate, period.endDate, activePath);
  };

  // Filter tree to respect depth limit
  const filteredTree = useMemo(() => {
    function trimTree(periods: DashaPeriod[], currentLevel: string): DashaPeriod[] {
      return periods.map((period) => {
        const shouldShow = shouldShowChildren(currentLevel, depthLimitState);
        if (shouldShow && period.subPeriods) {
          return {
            ...period,
            subPeriods: trimTree(period.subPeriods, period.level),
          };
        }
        return { ...period, subPeriods: undefined };
      });
    }

    return trimTree(dashaTree, 'ROOT');
  }, [dashaTree, depthLimitState]);

  return (
    <div className="space-y-4">
      {/* Header controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <DepthSelector currentDepth={depthLimitState} onChange={setDepthLimitState} />

        <DateScrubber
          targetDate={targetDateStr}
          onDateChange={(date) => {}}
          quickDates={QUICK_DATES}
        />
      </div>

      {/* Active breadcrumbs */}
      {activePath.length > 0 && (
        <ActiveBreadcrumbs
          path={activePath}
          planetSymbols={PLANET_SYMBOLS}
        />
      )}

      {/* Tree */}
      <div className="p-3 rounded-xl" style={{ background: 'rgba(26, 20, 35, 0.6)', border: '1px solid var(--glass-border)' }}>
        {filteredTree.map((rootPeriod) => (
          <TreeNode
            key={rootPeriod.id}
            period={rootPeriod}
            targetDate={targetDate}
            depthLimit={depthLimitState}
            expandedNodes={allExpanded}
            activePath={activePath}
            onToggle={handleToggle}
            onSelect={handleSelect}
            level={0}
          />
        ))}

        {filteredTree.length === 0 && (
          <div className="text-center py-8 text-sm" style={{ color: 'var(--cosmic-muted)' }}>
            No Dasha periods available for the selected date range.
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
        {Object.entries(LEVEL_LABELS).map(([level, label]) => (
          <div key={level} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-full"
              style={{ background: LEVEL_COLORS[level] || 'var(--cosmic-muted)' }}
            />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Helper: Convert backend DeepDashaResult to tree format ──────────────────

export interface DeepDashaBackend {
  md: { lord: string; level: string; start_utc: string; end_utc: string; duration_years: number };
  ad: { lord: string; level: string; start_utc: string; end_utc: string; duration_years: number };
  pd: { lord: string; level: string; start_utc: string; end_utc: string; duration_years: number };
  sd: { lord: string; start_utc: string; end_utc: string; duration_years: number; parent_pd_lord: string; parent_md_lord: string };
  ad_timeline: Array<{ lord: string; level: string; start_utc: string; end_utc: string; duration_years: number }>;
  pd_timeline: Array<{ lord: string; level: string; start_utc: string; end_utc: string; duration_years: number }>;
  sd_timeline: Array<{ lord: string; start_utc: string; end_utc: string; duration_years: number; parent_pd_lord: string; parent_md_lord: string }>;
  activation_multiplier: number;
}

export function convertDeepDashaToTree(
  backend: DeepDashaBackend,
  targetDateStr: string,
): DashaPeriod[] {
  const targetDate = new Date(targetDateStr + 'T00:00:00Z');

  // Find active AD in timeline
  const activeAd = backend.ad_timeline.find((p) => {
    const s = new Date(p.start_utc).getTime();
    const e = new Date(p.end_utc).getTime();
    return targetDate.getTime() >= s && targetDate.getTime() < e;
  }) || backend.ad;

  // Find active PD in timeline
  const activePd = backend.pd_timeline.find((p) => {
    const s = new Date(p.start_utc).getTime();
    const e = new Date(p.end_utc).getTime();
    return targetDate.getTime() >= s && targetDate.getTime() < e;
  }) || backend.pd;

  // Build SD periods from timeline
  const sdPeriods: DashaPeriod[] = backend.sd_timeline.map((p, idx) => ({
    id: `SD-${p.lord}-${idx}`,
    planet: p.lord,
    level: 'SD' as const,
    startDate: p.start_utc.split('T')[0],
    endDate: p.end_utc.split('T')[0],
    durationDays: daysBetween(p.start_utc.split('T')[0], p.end_utc.split('T')[0]),
  }));

  // Build PD periods from timeline
  const pdPeriods: DashaPeriod[] = backend.pd_timeline.map((p, idx) => ({
    id: `PD-${p.lord}-${idx}`,
    planet: p.lord,
    level: 'PD' as const,
    startDate: p.start_utc.split('T')[0],
    endDate: p.end_utc.split('T')[0],
    durationDays: daysBetween(p.start_utc.split('T')[0], p.end_utc.split('T')[0]),
    subPeriods: sdPeriods,
  }));

  // Build AD periods with PD sub-periods
  const adPeriods: DashaPeriod[] = backend.ad_timeline.map((p, idx) => {
    const isActiveAd = backend.ad === p || activeAd?.lord === p.lord;
    const subPd = isActiveAd
      ? pdPeriods
      : backend.pd_timeline.map((pd, pidx) => ({
          id: `PD-${pd.lord}-${pidx}`,
          planet: pd.lord,
          level: 'PD' as const,
          startDate: pd.start_utc.split('T')[0],
          endDate: pd.end_utc.split('T')[0],
          durationDays: daysBetween(pd.start_utc.split('T')[0], pd.end_utc.split('T')[0]),
        }));

    return {
      id: `AD-${p.lord}-${idx}`,
      planet: p.lord,
      level: 'AD' as const,
      startDate: p.start_utc.split('T')[0],
      endDate: p.end_utc.split('T')[0],
      durationDays: daysBetween(p.start_utc.split('T')[0], p.end_utc.split('T')[0]),
      subPeriods: subPd,
    };
  });

  // Root MD period
  return [
    {
      id: `MD-${backend.md.lord}-0`,
      planet: backend.md.lord,
      level: 'MD' as const,
      startDate: backend.md.start_utc.split('T')[0],
      endDate: backend.md.end_utc.split('T')[0],
      durationDays: daysBetween(backend.md.start_utc.split('T')[0], backend.md.end_utc.split('T')[0]),
      subPeriods: adPeriods,
    },
  ];
}
