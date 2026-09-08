'use client';

import type { RemedyResponse, PlanetRemedy, DoshaRemedy } from '@/lib/api';

// ── Icon Components ──────────────────────────────────────
const ICONS = {
  mantra: '📿',
  gemstone: '💎',
  temple: '🛕',
  charity: '🎁',
  colors: '🎨',
  fasting: '🍽️',
  lifestyle: '🧘',
  dosha: '⚠️',
  star: '⭐',
  warning: '⚠️',
  check: '✅',
  sun: '☀️',
  moon: '🌙',
  fire: '🔥',
  water: '💧',
  earth: '🌍',
  air: '💨',
};

// ── Severity Colors ──────────────────────────────────────
function getSeverityColor(severity: string): { color: string; bg: string } {
  switch (severity) {
    case 'high':
      return { color: 'var(--malefic-red)', bg: 'rgba(239, 68, 68, 0.1)' };
    case 'medium':
      return { color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)' };
    case 'low':
      return { color: 'var(--benefic-green)', bg: 'rgba(16, 185, 129, 0.1)' };
    default:
      return { color: 'var(--cosmic-muted)', bg: 'rgba(138, 148, 166, 0.08)' };
  }
}

// ── Assessment Colors ────────────────────────────────────
function getAssessmentColor(assessment: string): { color: string; label: string } {
  switch (assessment) {
    case 'excellent':
      return { color: 'var(--benefic-green)', label: 'Excellent - Chart is Well Balanced' };
    case 'good':
      return { color: 'var(--benefic-green)', label: 'Good - Minor Afflictions' };
    case 'moderate':
      return { color: 'var(--cosmic-gold)', label: 'Moderate - Some Remedies Recommended' };
    case 'challenging':
      return { color: '#eab308', label: 'Challenging - Remedies Strongly Recommended' };
    case 'difficult':
      return { color: 'var(--malefic-red)', label: 'Difficult - Comprehensive Remedies Required' };
    default:
      return { color: 'var(--cosmic-muted)', label: 'Unknown' };
  }
}

// ── Card Component ───────────────────────────────────────
function RemedyCard({
  icon,
  title,
  children,
  className = '',
}: {
  icon: string;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl p-4 ${className}`}
      style={{
        background: 'var(--glass-bg)',
        border: '1px solid var(--glass-border)',
        backdropFilter: 'blur(16px)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <h4 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
          {title}
        </h4>
      </div>
      {children}
    </div>
  );
}

// ── Info Row Component ───────────────────────────────────
function InfoRow({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between items-start py-1.5">
      <span className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
        {label}
      </span>
      <span
        className="text-xs font-medium text-right max-w-[60%]"
        style={{ color: highlight ? 'var(--cosmic-gold)' : 'var(--cosmic-text)' }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Planet Remedy Card ───────────────────────────────────
function PlanetRemedyCard({ remedy }: { remedy: PlanetRemedy }) {
  const severityStyle = getSeverityColor(remedy.severity);

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{ border: `1px solid ${severityStyle.color}30` }}
    >
      {/* Header */}
      <div
        className="px-4 py-3"
        style={{ background: severityStyle.bg }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{ICONS.star}</span>
            <h3 className="font-bold" style={{ color: 'var(--cosmic-text)' }}>
              {remedy.planet}
            </h3>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ background: `${severityStyle.color}20`, color: severityStyle.color }}
            >
              {remedy.severity.toUpperCase()}
            </span>
          </div>
          <span className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
            {remedy.affliction.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Remedy Grid */}
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Mantra */}
        {remedy.mantra?.moola_mantra && (
          <RemedyCard icon={ICONS.mantra} title="Mantra">
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--cosmic-text)' }}>
              {remedy.mantra.moola_mantra}
            </p>
            <div className="space-y-1">
              <InfoRow label="Gayatri" value={remedy.mantra.gayatri || '—'} />
              <InfoRow label="Count" value={`${remedy.mantra.count?.toLocaleString()} times`} />
              <InfoRow label="Best Day" value={remedy.mantra.best_day || '—'} />
              <InfoRow label="Best Time" value={remedy.mantra.best_time || '—'} />
            </div>
          </RemedyCard>
        )}

        {/* Gemstone */}
        {remedy.gemstone?.primary_stone && (
          <RemedyCard icon={ICONS.gemstone} title="Gemstone">
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--cosmic-text)' }}>
              {remedy.gemstone.primary_stone}
            </p>
            <div className="space-y-1">
              <InfoRow label="Weight" value={`${remedy.gemstone.weight_carat} carat`} />
              <InfoRow label="Metal" value={remedy.gemstone.metal || '—'} />
              <InfoRow label="Finger" value={remedy.gemstone.finger || '—'} />
              <InfoRow label="Day to Wear" value={remedy.gemstone.day_to_wear || '—'} />
              {remedy.gemstone.certification && (
                <InfoRow label="Note" value={remedy.gemstone.certification} highlight />
              )}
            </div>
          </RemedyCard>
        )}

        {/* Temple */}
        {remedy.temple?.deity && (
          <RemedyCard icon={ICONS.temple} title="Temple Worship">
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--cosmic-text)' }}>
              {remedy.temple.deity}
            </p>
            <div className="space-y-1">
              <InfoRow label="Temple" value={remedy.temple.temple_name || '—'} />
              <InfoRow label="Facing" value={remedy.temple.facing_direction || '—'} />
              <InfoRow label="Offering" value={remedy.temple.offering || '—'} />
              {remedy.temple.prasad && (
                <InfoRow label="Prasad" value={remedy.temple.prasad} />
              )}
            </div>
          </RemedyCard>
        )}

        {/* Charity */}
        {remedy.charity?.item_to_donate && (
          <RemedyCard icon={ICONS.charity} title="Charity">
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--cosmic-text)' }}>
              {remedy.charity.item_to_donate}
            </p>
            <div className="space-y-1">
              <InfoRow label="Recipient" value={remedy.charity.recipient || '—'} />
              <InfoRow label="Day" value={remedy.charity.day || '—'} />
              {remedy.charity.quantity && (
                <InfoRow label="Quantity" value={remedy.charity.quantity} />
              )}
              {remedy.charity.specific_donation && (
                <InfoRow label="Special" value={remedy.charity.specific_donation} highlight />
              )}
            </div>
          </RemedyCard>
        )}

        {/* Color Therapy */}
        {remedy.color_therapy?.favorable_colors && (
          <RemedyCard icon={ICONS.colors} title="Color Therapy">
            <div className="space-y-2">
              <div>
                <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  Favorable
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {remedy.color_therapy.favorable_colors.map((color) => (
                    <span
                      key={color}
                      className="text-[10px] px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--benefic-green)' }}
                    >
                      {color}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  Avoid
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {remedy.color_therapy.colors_to_avoid.map((color) => (
                    <span
                      key={color}
                      className="text-[10px] px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--malefic-red)' }}
                    >
                      {color}
                    </span>
                  ))}
                </div>
              </div>
              {remedy.color_therapy.lucky_color && (
                <InfoRow label="Lucky Color" value={remedy.color_therapy.lucky_color} highlight />
              )}
            </div>
          </RemedyCard>
        )}

        {/* Fasting */}
        {remedy.fasting?.day && (
          <RemedyCard icon={ICONS.fasting} title="Fasting">
            <div className="space-y-1">
              <InfoRow label="Day" value={remedy.fasting.day} />
              {remedy.fasting.duration && (
                <InfoRow label="Duration" value={remedy.fasting.duration} />
              )}
              <div>
                <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  Avoid
                </span>
                <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-text)' }}>
                  {remedy.fasting.food_to_avoid?.join(', ') || '—'}
                </p>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--cosmic-muted)' }}>
                  Allowed
                </span>
                <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-text)' }}>
                  {remedy.fasting.allowed_foods?.join(', ') || '—'}
                </p>
              </div>
            </div>
          </RemedyCard>
        )}

        {/* Lifestyle */}
        {remedy.lifestyle && (
          <RemedyCard icon={ICONS.lifestyle} title="Lifestyle">
            <div className="space-y-1">
              {remedy.lifestyle.exercise && (
                <InfoRow label="Exercise" value={remedy.lifestyle.exercise} />
              )}
              {remedy.lifestyle.meditation && (
                <InfoRow label="Meditation" value={remedy.lifestyle.meditation} />
              )}
              {remedy.lifestyle.behavior && (
                <InfoRow label="Behavior" value={remedy.lifestyle.behavior} />
              )}
            </div>
          </RemedyCard>
        )}
      </div>
    </div>
  );
}

// ── Dosha Card ───────────────────────────────────────────
function DoshaCard({ dosha }: { dosha: DoshaRemedy }) {
  const severityStyle = getSeverityColor(dosha.severity);

  return (
    <div
      className="rounded-xl p-4"
      style={{ background: severityStyle.bg, border: `1px solid ${severityStyle.color}30` }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{ICONS.dosha}</span>
        <h4 className="font-semibold text-sm" style={{ color: severityStyle.color }}>
          {dosha.dosha.replace(/_/g, ' ').toUpperCase()}
        </h4>
        <span
          className="text-[10px] px-2 py-0.5 rounded-full font-medium"
          style={{ background: `${severityStyle.color}20`, color: severityStyle.color }}
        >
          {dosha.severity.toUpperCase()}
        </span>
      </div>
      <p className="text-xs mb-3" style={{ color: 'var(--cosmic-muted)' }}>
        {dosha.description}
      </p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span style={{ color: 'var(--cosmic-muted)' }}>Mantra: </span>
          <span style={{ color: 'var(--cosmic-text)' }}>{dosha.mantra}</span>
        </div>
        <div>
          <span style={{ color: 'var(--cosmic-muted)' }}>Charity: </span>
          <span style={{ color: 'var(--cosmic-text)' }}>{dosha.charity}</span>
        </div>
        <div>
          <span style={{ color: 'var(--cosmic-muted)' }}>Temple: </span>
          <span style={{ color: 'var(--cosmic-text)' }}>{dosha.temple}</span>
        </div>
        <div>
          <span style={{ color: 'var(--cosmic-muted)' }}>Remedy: </span>
          <span style={{ color: 'var(--cosmic-text)' }}>{dosha.remedy}</span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────
interface RemediesPanelProps {
  data: RemedyResponse | null;
  loading?: boolean;
  error?: string | null;
}

export default function RemediesPanel({ data, loading, error }: RemediesPanelProps) {
  if (loading) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded-lg" style={{ background: 'rgba(197,168,128,0.06)' }} />
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-32 rounded-xl" style={{ background: 'rgba(197,168,128,0.04)' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="rounded-2xl p-6"
        style={{ background: 'var(--glass-bg)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
      >
        <p className="text-sm" style={{ color: '#fca5a5' }}>
          Failed to load remedies: {error}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        className="rounded-2xl p-8 text-center"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <p style={{ color: 'var(--cosmic-muted)' }}>No remedies data available.</p>
      </div>
    );
  }

  const assessmentStyle = getAssessmentColor(data.overall_assessment);
  const hasAfflictions = data.afflicted_planets.length > 0;
  const hasDoshas = data.doshas.length > 0;

  return (
    <div className="space-y-6">
      {/* Overall Assessment */}
      <div
        className="rounded-2xl p-4"
        style={{
          background: 'var(--glass-bg)',
          border: `1px solid ${assessmentStyle.color}30`,
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {hasAfflictions || hasDoshas ? ICONS.warning : ICONS.check}
            </span>
            <div>
              <h3 className="font-bold" style={{ color: assessmentStyle.color }}>
                {assessmentStyle.label}
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
                {hasAfflictions ? `${data.afflicted_planets.length} planet(s) need remedies` : 'No major afflictions'}
                {hasDoshas && ` · ${data.doshas.length} Dosha(s) detected`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* No Afflictions Message */}
      {!hasAfflictions && !hasDoshas && (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <span className="text-4xl mb-3 block">{ICONS.check}</span>
          <p className="text-sm font-medium" style={{ color: 'var(--benefic-green)' }}>
            Your chart is well-balanced!
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--cosmic-muted)' }}>
            No major planetary afflictions detected. Maintain your spiritual practices.
          </p>
        </div>
      )}

      {/* Planet Remedies */}
      {hasAfflictions && (
        <div>
          <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
            Planetary Remedies ({data.afflicted_planets.length})
          </h3>
          <div className="space-y-4">
            {data.afflicted_planets.map((remedy) => (
              <PlanetRemedyCard key={remedy.planet} remedy={remedy} />
            ))}
          </div>
        </div>
      )}

      {/* Dosha Remedies */}
      {hasDoshas && (
        <div>
          <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
            Dosha Remedies ({data.doshas.length})
          </h3>
          <div className="space-y-3">
            {data.doshas.map((dosha) => (
              <DoshaCard key={dosha.dosha} dosha={dosha} />
            ))}
          </div>
        </div>
      )}

      {/* General Remedies */}
      {data.general_remedies && (
        <div
          className="rounded-2xl p-4"
          style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--cosmic-gold)' }}>
            General Spiritual Practices
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {data.general_remedies.daily_practice && (
              <div>
                <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--cosmic-muted)' }}>
                  Daily Practice
                </h4>
                <ul className="space-y-1">
                  {data.general_remedies.daily_practice.map((item, i) => (
                    <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: 'var(--cosmic-text)' }}>
                      <span style={{ color: 'var(--benefic-green)' }}>•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.general_remedies.weekly_practice && (
              <div>
                <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--cosmic-muted)' }}>
                  Weekly Practice
                </h4>
                <ul className="space-y-1">
                  {data.general_remedies.weekly_practice.map((item, i) => (
                    <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: 'var(--cosmic-text)' }}>
                      <span style={{ color: 'var(--cosmic-gold)' }}>•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.general_remedies.monthly_practice && (
              <div>
                <h4 className="text-xs font-semibold mb-2" style={{ color: 'var(--cosmic-muted)' }}>
                  Monthly Practice
                </h4>
                <ul className="space-y-1">
                  {data.general_remedies.monthly_practice.map((item, i) => (
                    <li key={i} className="text-xs flex items-start gap-1.5" style={{ color: 'var(--cosmic-text)' }}>
                      <span style={{ color: '#c084fc' }}>•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div
        className="rounded-xl p-4 text-xs"
        style={{
          background: 'rgba(234, 179, 8, 0.06)',
          border: '1px solid rgba(234, 179, 8, 0.15)',
          color: 'var(--cosmic-muted)',
        }}
      >
        <p className="flex items-start gap-2">
          <span className="text-base">{ICONS.warning}</span>
          <span>{data.disclaimer}</span>
        </p>
      </div>
    </div>
  );
}
