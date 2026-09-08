'use client';

import { AlertTriangle, Loader2 } from 'lucide-react';

// ── Spinner ──────────────────────────────────────────────
export function Spinner({ size = 18, label }: { size?: number; label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12" style={{ color: 'var(--cosmic-muted)' }}>
      <Loader2 size={size} className="animate-spin" style={{ color: 'var(--cosmic-gold)' }} />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}

// ── Skeleton Bar ─────────────────────────────────────────
function SkeletonBar({ width = '100%', height = '1rem', className = '' }: {
  width?: string; height?: string; className?: string;
}) {
  return (
    <div
      className={`rounded-lg animate-pulse ${className}`}
      style={{ width, height, background: 'rgba(197,168,128,0.06)' }}
    />
  );
}

// ── Chart Skeleton ───────────────────────────────────────
export function ChartSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <SkeletonBar width="12rem" height="2rem" />
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <div className="aspect-square rounded-2xl" style={{ background: 'rgba(197,168,128,0.05)' }} />
        </div>
        <div className="lg:col-span-3 space-y-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <SkeletonBar key={i} height="2.5rem" />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Report Skeleton ──────────────────────────────────────
export function ReportSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <SkeletonBar width="14rem" height="2rem" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-36 rounded-2xl" style={{ background: 'rgba(197,168,128,0.05)' }} />
        ))}
      </div>
      <div className="h-48 rounded-2xl" style={{ background: 'rgba(197,168,128,0.04)' }} />
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonBar key={i} height="3rem" />
        ))}
      </div>
    </div>
  );
}

// ── Transits Skeleton ────────────────────────────────────
export function TransitsSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <SkeletonBar width="16rem" height="2rem" />
      <div className="flex gap-3 overflow-hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="shrink-0 w-40 h-24 rounded-xl" style={{ background: 'rgba(197,168,128,0.05)' }} />
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="h-24 rounded-xl" style={{ background: 'rgba(197,168,128,0.04)' }} />
        ))}
      </div>
    </div>
  );
}

// ── Error Banner ─────────────────────────────────────────
export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      className="p-4 rounded-xl flex items-start gap-3"
      style={{
        background: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
      }}
    >
      <AlertTriangle size={18} className="text-red-400 mt-0.5 shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: '#fca5a5' }}>Something went wrong</p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="text-xs px-3 py-1 rounded-lg shrink-0 transition-colors"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: '#fca5a5',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}

// ── Empty State ──────────────────────────────────────────
export function EmptyState({ icon, title, description, action }: {
  icon?: string; title: string; description?: string;
  action?: { label: string; href: string };
}) {
  return (
    <div className="text-center py-12">
      {icon && <div className="text-4xl mb-3">{icon}</div>}
      <p className="text-sm font-medium mb-1" style={{ color: 'var(--cosmic-text)' }}>{title}</p>
      {description && <p className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>{description}</p>}
      {action && (
        <a
          href={action.href}
          className="inline-block mt-3 text-xs px-4 py-2 rounded-lg transition-colors"
          style={{
            background: 'rgba(197,168,128,0.1)',
            border: '1px solid rgba(197,168,128,0.2)',
            color: 'var(--cosmic-gold)',
          }}
        >
          {action.label}
        </a>
      )}
    </div>
  );
}
