'use client';

import type { EvaluationResponse } from '@/lib/api';

// ── Sign / Planet helpers ────────────────────────────────
const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
];
const SIGN_NAMES: Record<string, string> = {
  MESHA: 'Aries', VRISHABHA: 'Taurus', MITHUNA: 'Gemini', KARKA: 'Cancer',
  SIMHA: 'Leo', KANYA: 'Virgo', TULA: 'Libra', VRISHCHIKA: 'Scorpio',
  DHANUSHA: 'Sagittarius', MAKARA: 'Capricorn', KUMBHA: 'Aquarius', MEENA: 'Pisces',
};

// ── Vastu Directions by Sign ─────────────────────────────
const VASTU_DIRECTIONS: Record<string, { entrance: string; avoid: string; color: string; deity: string; lucky_color: string }> = {
  MESHA: { entrance: 'East', avoid: 'Southwest', color: 'Red', deity: 'Lord Hanuman', lucky_color: 'Red, Orange' },
  VRISHABHA: { entrance: 'Southeast', avoid: 'Northwest', color: 'White, Green', deity: 'Goddess Lakshmi', lucky_color: 'White, Green' },
  MITHUNA: { entrance: 'North', avoid: 'South', color: 'Green, Yellow', deity: 'Lord Vishnu', lucky_color: 'Green, Yellow' },
  KARKA: { entrance: 'Northwest', avoid: 'Southeast', color: 'White, Silver', deity: 'Goddess Durga', lucky_color: 'White, Silver' },
  SIMHA: { entrance: 'East', avoid: 'Southwest', color: 'Gold, Orange', deity: 'Lord Surya', lucky_color: 'Gold, Orange' },
  KANYA: { entrance: 'East', avoid: 'Northwest', color: 'Green, Brown', deity: 'Lord Ganesha', lucky_color: 'Green, Brown' },
  TULA: { entrance: 'Northwest', avoid: 'Southeast', color: 'White, Pink', deity: 'Goddess Lakshmi', lucky_color: 'White, Pink' },
  VRISHCHIKA: { entrance: 'South', avoid: 'Northwest', color: 'Red, Maroon', deity: 'Lord Kartikeya', lucky_color: 'Red, Maroon' },
  DHANUSHA: { entrance: 'North', avoid: 'South', color: 'Yellow, Gold', deity: 'Lord Vishnu', lucky_color: 'Yellow, Gold' },
  MAKARA: { entrance: 'West', avoid: 'East', color: 'Blue, Black', deity: 'Lord Shiva', lucky_color: 'Blue, Black' },
  KUMBHA: { entrance: 'West', avoid: 'East', color: 'Blue, Silver', deity: 'Lord Shani', lucky_color: 'Blue, Silver' },
  MEENA: { entrance: 'Northwest', avoid: 'Southeast', color: 'Yellow, White', deity: 'Lord Vishnu', lucky_color: 'Yellow, White' },
};

// ── Auspicious Days ──────────────────────────────────────
const AUSPICIOUS_DAYS: Record<string, string[]> = {
  MESHA: ['Tuesday', 'Sunday'],
  VRISHABHA: ['Friday', 'Monday'],
  MITHUNA: ['Wednesday', 'Thursday'],
  KARKA: ['Monday', 'Thursday'],
  SIMHA: ['Sunday', 'Tuesday'],
  KANYA: ['Wednesday', 'Thursday'],
  TULA: ['Friday', 'Saturday'],
  VRISHCHIKA: ['Tuesday', 'Saturday'],
  DHANUSHA: ['Thursday', 'Sunday'],
  MAKARA: ['Saturday', 'Tuesday'],
  KUMBHA: ['Saturday', 'Sunday'],
  MEENA: ['Thursday', 'Wednesday'],
};

// ── Main Component ───────────────────────────────────────
interface VastuGuideProps {
  data: EvaluationResponse;
}

export default function VastuGuide({ data }: VastuGuideProps) {
  const lagna = data.lagna;
  const vastu = VASTU_DIRECTIONS[lagna] || VASTU_DIRECTIONS.MESHA;
  const auspiciousDays = AUSPICIOUS_DAYS[lagna] || ['Thursday', 'Sunday'];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
              Vastu Recommendations
            </h3>
            <p className="text-[10px] mt-0.5" style={{ color: 'var(--cosmic-muted)' }}>
              Based on your Lagna: {SIGN_NAMES[lagna] || lagna}
            </p>
          </div>
          <span className="text-2xl">🏠</span>
        </div>
      </div>

      {/* Main Recommendations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Entrance Direction */}
        <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🚪</span>
            <h4 className="text-xs font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
              Favorable Entrance Direction
            </h4>
          </div>
          <div className="text-center py-4">
            <div className="text-3xl font-bold mb-1" style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
              {vastu.entrance}
            </div>
            <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
              Best direction for main entrance
            </p>
          </div>
          <div className="mt-3 p-2 rounded-lg text-center" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
            <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>
              Avoid: <strong style={{ color: 'var(--malefic-red)' }}>{vastu.avoid}</strong> entrance
            </p>
          </div>
        </div>

        {/* Colors & Deity */}
        <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🎨</span>
            <h4 className="text-xs font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
              Home Colors & Deity
            </h4>
          </div>

          <div className="space-y-3">
            <div className="text-center py-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <p className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Recommended Colors</p>
              <p className="text-sm font-bold" style={{ color: 'var(--cosmic-text)' }}>{vastu.color}</p>
            </div>

            <div className="text-center py-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <p className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Lucky Color</p>
              <p className="text-sm font-bold" style={{ color: 'var(--cosmic-gold)' }}>{vastu.lucky_color}</p>
            </div>

            <div className="text-center py-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
              <p className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--cosmic-muted)' }}>Home Temple Deity</p>
              <p className="text-sm font-bold" style={{ color: 'var(--benefic-green)' }}>{vastu.deity}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Auspicious Days & Griha Pravesh */}
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">📅</span>
          <h4 className="text-xs font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
            Auspicious Days for Griha Pravesh
          </h4>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {auspiciousDays.map((day) => (
            <div key={day} className="text-center py-3 rounded-lg" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}>
              <p className="text-xs font-bold" style={{ color: 'var(--benefic-green)' }}>{day}</p>
              <p className="text-[9px]" style={{ color: 'var(--cosmic-muted)' }}>Favorable</p>
            </div>
          ))}
        </div>

        <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
          <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
            <strong style={{ color: 'var(--cosmic-gold)' }}>Griha Pravesh Tips:</strong>{' '}
            Perform a small puja before entering. Light a diya in the entrance. Offer prayers to {vastu.deity} for prosperity and protection.
          </p>
        </div>
      </div>

      {/* Additional Vastu Tips */}
      <div className="rounded-2xl p-4" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">💡</span>
          <h4 className="text-xs font-semibold" style={{ color: 'var(--cosmic-gold)' }}>
            Additional Vastu Tips
          </h4>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="p-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
            <p className="text-[10px] font-semibold mb-1" style={{ color: 'var(--cosmic-gold)' }}>Kitchen</p>
            <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
              Place the kitchen in the Southeast. Cook facing East for positive energy.
            </p>
          </div>
          <div className="p-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
            <p className="text-[10px] font-semibold mb-1" style={{ color: 'var(--cosmic-gold)' }}>Bedroom</p>
            <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
              Master bedroom in Southwest. Sleep with head towards South or East.
            </p>
          </div>
          <div className="p-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
            <p className="text-[10px] font-semibold mb-1" style={{ color: 'var(--cosmic-gold)' }}>Puja Room</p>
            <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
              Place in Northeast. Face East or North while praying. Keep clean and lit.
            </p>
          </div>
          <div className="p-3 rounded-lg" style={{ background: 'rgba(26,20,35,0.3)' }}>
            <p className="text-[10px] font-semibold mb-1" style={{ color: 'var(--cosmic-gold)' }}>Water Elements</p>
            <p className="text-[10px] leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
              Water features (fountain, aquarium) in North. Keep water flowing for prosperity.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
