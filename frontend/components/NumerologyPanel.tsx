'use client';

import { useState, useEffect } from 'react';
import type { NumerologyResponse } from '@/lib/api';

// ── Pythagorean Letter Values ────────────────────────────
const LETTER_VALUES: Record<string, number> = {
  A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8, I: 9,
  J: 1, K: 2, L: 3, M: 4, N: 5, O: 6, P: 7, Q: 8, R: 9,
  S: 1, T: 2, U: 3, V: 4, W: 5, X: 6, Y: 7, Z: 8,
};
const VOWELS = new Set('AEIOU');
const MASTER_NUMBERS = new Set([11, 22, 33]);

// ── Meaning Dictionaries ─────────────────────────────────
const LIFE_PATH_MEANINGS: Record<number, string> = {
  1: 'A natural leader with strong independence and initiative. Driven to achieve goals and inspire others.',
  2: 'A diplomatic peacemaker with sensitivity and intuition. Excel in partnerships and bringing harmony.',
  3: 'A creative communicator with artistic talent. Express freely and inspire joy in others.',
  4: 'A practical builder with strong work ethic. Create stability and order through discipline.',
  5: 'An adventurous spirit seeking change and freedom. Embrace life\'s variety with enthusiasm.',
  6: 'A nurturing caregiver with deep sense of responsibility. Bring comfort and healing to others.',
  7: 'A spiritual seeker with analytical mind. Pursue truth and wisdom through introspection.',
  8: 'A powerful achiever with material success potential. Manifest abundance through determination.',
  9: 'A compassionate humanitarian with universal love. Serve others and inspire positive change.',
  11: 'A spiritual messenger with heightened intuition. Inspire others through visionary insights.',
  22: 'A master builder with great humanitarian vision. Manifest large-scale positive change.',
  33: 'A spiritual teacher with unconditional love. Guide others through compassion and wisdom.',
};

const DESTINY_MEANINGS: Record<number, string> = {
  1: 'Your destiny is to lead and innovate. Pioneer new paths and inspire independence.',
  2: 'Your destiny is to cooperate and harmonize. Build bridges and create peace.',
  3: 'Your destiny is to create and express. Bring joy through art and communication.',
  4: 'Your destiny is to build and stabilize. Create lasting foundations for others.',
  5: 'Your destiny is to explore and adapt. Experience life\'s diversity and share wisdom.',
  6: 'Your destiny is to nurture and heal. Bring comfort and teach responsibility.',
  7: 'Your destiny is to seek truth and wisdom. Explore the deeper mysteries of life.',
  8: 'Your destiny is to achieve and prosper. Manifest abundance and lead with authority.',
  9: 'Your destiny is to serve and inspire. Uplift humanity through compassion.',
  11: 'Your destiny is to inspire and illuminate. Bring spiritual awakening to others.',
  22: 'Your destiny is to build and transform. Create lasting positive change on a large scale.',
  33: 'Your destiny is to teach and heal. Embody unconditional love and spiritual wisdom.',
};

const SOUL_URGE_MEANINGS: Record<number, string> = {
  1: 'Your heart desires independence and leadership. Yearn to be recognized for your unique identity.',
  2: 'Your heart desires harmony and partnership. Yearn for deep connection and peaceful relationships.',
  3: 'Your heart desires creative expression. Yearn to share your ideas and bring joy to others.',
  4: 'Your heart desires stability and security. Yearn for a solid foundation and orderly life.',
  5: 'Your heart desires freedom and adventure. Yearn for excitement and new experiences.',
  6: 'Your heart desires love and family. Yearn to nurture others and create a harmonious home.',
  7: 'Your heart desires spiritual understanding. Yearn for inner peace and deeper knowledge.',
  8: 'Your heart desires success and recognition. Yearn for achievement and material abundance.',
  9: 'Your heart desires to help humanity. Yearn to make a difference and serve a greater cause.',
  11: 'Your heart desires spiritual connection. Yearn to inspire others through intuition and insight.',
  22: 'Your heart desires to make a lasting impact. Yearn to build something meaningful for humanity.',
  33: 'Your heart desires to heal and teach. Yearn to spread love and spiritual wisdom.',
};

// ── Calculation Functions ────────────────────────────────
function reduceToSingle(n: number): number {
  while (n > 9 && !MASTER_NUMBERS.has(n)) {
    n = String(n).split('').reduce((sum, d) => sum + parseInt(d), 0);
  }
  return n;
}

function sumDigits(n: number): number {
  return String(Math.abs(n)).split('').reduce((sum, d) => sum + parseInt(d), 0);
}

function calculateLifePath(birthDate: string): number {
  const parts = birthDate.replace(/\//g, '-').split('-');
  if (parts.length !== 3) return 0;
  const year = parseInt(parts[0]);
  const month = parseInt(parts[1]);
  const day = parseInt(parts[2]);
  if (isNaN(year) || isNaN(month) || isNaN(day)) return 0;
  return reduceToSingle(sumDigits(year) + sumDigits(month) + sumDigits(day));
}

function calculateDestiny(fullName: string): number {
  let total = 0;
  for (const char of fullName.toUpperCase()) {
    total += LETTER_VALUES[char] || 0;
  }
  return reduceToSingle(total);
}

function calculateSoulUrge(fullName: string): number {
  let total = 0;
  for (const char of fullName.toUpperCase()) {
    if (VOWELS.has(char)) {
      total += LETTER_VALUES[char] || 0;
    }
  }
  return reduceToSingle(total);
}

function computeNumerology(birthDate: string, fullName: string): NumerologyResponse | null {
  if (!birthDate || !fullName) return null;
  const lifePath = calculateLifePath(birthDate);
  const destiny = calculateDestiny(fullName);
  const soulUrge = calculateSoulUrge(fullName);
  if (lifePath === 0 || destiny === 0 || soulUrge === 0) return null;
  return {
    birth_date: birthDate,
    full_name: fullName,
    life_path: { number: lifePath, meaning: LIFE_PATH_MEANINGS[lifePath] || 'A unique spiritual path.' },
    destiny: { number: destiny, meaning: DESTINY_MEANINGS[destiny] || 'A unique destiny awaits.' },
    soul_urge: { number: soulUrge, meaning: SOUL_URGE_MEANINGS[soulUrge] || 'A unique heart\'s desire.' },
  };
}

// ── Icon Components ──────────────────────────────────────
const ICONS = {
  life_path: '🛤️',
  destiny: '⭐',
  soul_urge: '💜',
};

// ── Number Card ──────────────────────────────────────────
function NumberCard({ icon, title, number, meaning, color }: {
  icon: string; title: string; number: number; meaning: string; color: string;
}) {
  return (
    <div className="rounded-xl p-4" style={{ background: 'var(--glass-bg)', border: `1px solid ${color}30` }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <h4 className="text-sm font-semibold" style={{ color }}>{title}</h4>
      </div>
      <div className="flex items-center justify-center mb-3">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold"
          style={{ background: `${color}15`, border: `2px solid ${color}40`, color, fontFamily: 'var(--font-playfair), Georgia, serif' }}
        >
          {number}
        </div>
      </div>
      <p className="text-xs text-center leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{meaning}</p>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────
interface NumerologyPanelProps {
  data?: NumerologyResponse | null;
  loading?: boolean;
  error?: string | null;
  showInput?: boolean;
  initialBirthDate?: string;
  initialName?: string;
}

export default function NumerologyPanel({
  data: initialData,
  showInput = true,
  initialBirthDate = '',
  initialName = '',
}: NumerologyPanelProps) {
  const [birthDate, setBirthDate] = useState(initialBirthDate);
  const [fullName, setFullName] = useState(initialName);
  const [data, setData] = useState<NumerologyResponse | null>(initialData || null);

  // Auto-calculate when initial values are provided
  useEffect(() => {
    if (initialBirthDate && initialName && !data) {
      const result = computeNumerology(initialBirthDate, initialName);
      if (result) setData(result);
    }
  }, [initialBirthDate, initialName, data]);

  // Recalculate when inputs change
  const handleRecalculate = () => {
    const result = computeNumerology(birthDate, fullName);
    if (result) setData(result);
  };

  if (!data && !showInput) {
    return (
      <div className="rounded-2xl p-8 text-center" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
        <p style={{ color: 'var(--cosmic-muted)' }}>No numerology data available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Input Form */}
      {showInput && !data && (
        <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--cosmic-gold)' }}>
            Calculate Your Numbers
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            <div>
              <label className="cosmic-label">Birth Date</label>
              <input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} className="cosmic-input" />
            </div>
            <div>
              <label className="cosmic-label">Full Name</label>
              <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="First Middle Last" className="cosmic-input" />
            </div>
          </div>
          <button
            type="button"
            onClick={handleRecalculate}
            disabled={!birthDate || !fullName}
            className="cosmic-btn text-sm"
          >
            Calculate Numbers
          </button>
        </div>
      )}

      {/* Results */}
      {data && (
        <>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(26, 20, 35, 0.4)', border: '1px solid var(--glass-border)' }}>
            <p className="text-xs" style={{ color: 'var(--cosmic-muted)' }}>
              <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>{data.full_name}</span>
              {' · Born '}
              <span className="font-medium" style={{ color: 'var(--cosmic-text)' }}>{data.birth_date}</span>
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <NumberCard icon={ICONS.life_path} title="Life Path Number" number={data.life_path.number} meaning={data.life_path.meaning} color="var(--cosmic-gold)" />
            <NumberCard icon={ICONS.destiny} title="Destiny Number" number={data.destiny.number} meaning={data.destiny.meaning} color="var(--benefic-green)" />
            <NumberCard icon={ICONS.soul_urge} title="Soul Urge Number" number={data.soul_urge.number} meaning={data.soul_urge.meaning} color="#c084fc" />
          </div>

          <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
            <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--cosmic-gold)' }}>Detailed Interpretation</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5">{ICONS.life_path}</span>
                <div>
                  <h4 className="text-xs font-semibold mb-1" style={{ color: 'var(--cosmic-gold)' }}>Life Path {data.life_path.number}</h4>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{data.life_path.meaning}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5">{ICONS.destiny}</span>
                <div>
                  <h4 className="text-xs font-semibold mb-1" style={{ color: 'var(--benefic-green)' }}>Destiny {data.destiny.number}</h4>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{data.destiny.meaning}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5">{ICONS.soul_urge}</span>
                <div>
                  <h4 className="text-xs font-semibold mb-1" style={{ color: '#c084fc' }}>Soul Urge {data.soul_urge.number}</h4>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>{data.soul_urge.meaning}</p>
                </div>
              </div>
            </div>
          </div>

          {showInput && (
            <div className="flex justify-center">
              <button type="button" onClick={() => setData(null)} className="cosmic-btn-outline text-sm">
                Calculate Again
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
