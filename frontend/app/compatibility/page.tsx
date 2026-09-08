'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Sparkles, ArrowRight, RotateCcw } from 'lucide-react';
import { api } from '@/lib/api';
import type { CompatibilityResponse } from '@/lib/api';

// ── Nakshatra options ────────────────────────────────────
const NAKSHATRA_OPTIONS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
  'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

// ── Helper functions ─────────────────────────────────────
function getScoreColor(score: number, max: number): string {
  const pct = score / max;
  if (pct >= 0.75) return '#34d399';
  if (pct >= 0.5) return '#facc15';
  return '#f87171';
}

function getLaymanSummary(score: number, max: number): string {
  const pct = score / max;
  if (pct >= 0.85) return 'An excellent match! This pairing shows strong spiritual, emotional, and practical harmony. The stars are aligned for a deep and lasting bond.';
  if (pct >= 0.70) return 'A very good match with strong compatibility across most areas. Minor differences may arise but can be easily navigated with mutual understanding.';
  if (pct >= 0.55) return 'A moderate match with good potential. Some areas require conscious effort and compromise, but the foundation is solid enough for a fulfilling partnership.';
  if (pct >= 0.40) return 'A challenging match that requires significant effort from both partners. With dedication and classical remedies, the relationship can still thrive.';
  return 'This pairing has significant challenges. Classical texts recommend specific remedies and careful consideration before proceeding.';
}

// ── Birth Data Form ──────────────────────────────────────
interface BirthFormData {
  name: string;
  nakshatra: string;
}

function BirthDataForm({
  label,
  data,
  onChange,
  accentColor,
}: {
  label: string;
  data: BirthFormData;
  onChange: (d: BirthFormData) => void;
  accentColor: string;
}) {
  return (
    <div className="rounded-2xl p-5" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: accentColor }}>
        {label}
      </p>
      <div className="space-y-3">
        <div>
          <label className="cosmic-label">Name (optional)</label>
          <input
            type="text"
            value={data.name}
            onChange={(e) => onChange({ ...data, name: e.target.value })}
            placeholder={`${label} name`}
            className="cosmic-input"
          />
        </div>
        <div>
          <label className="cosmic-label">Nakshatra (Birth Star)</label>
          <select
            value={data.nakshatra}
            onChange={(e) => onChange({ ...data, nakshatra: e.target.value })}
            className="cosmic-select"
          >
            <option value="">Select nakshatra…</option>
            {NAKSHATRA_OPTIONS.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

// ── Circular Score ───────────────────────────────────────
function CircularScore({ score, max }: { score: number; max: number }) {
  const pct = score / max;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const color = getScoreColor(score, max);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="150" height="150" viewBox="0 0 150 150">
        {/* Background circle */}
        <circle cx="75" cy="75" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        {/* Progress arc */}
        <circle
          cx="75" cy="75" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 75 75)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-2xl font-bold" style={{ color, fontFamily: 'var(--font-playfair), Georgia, serif' }}>
          {score}
        </p>
        <p className="text-[10px]" style={{ color: 'var(--cosmic-muted)' }}>/ {max}</p>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN PAGE
// ══════════════════════════════════════════════════════════

export default function CompatibilityPage() {
  const [personA, setPersonA] = useState<BirthFormData>({ name: '', nakshatra: '' });
  const [personB, setPersonB] = useState<BirthFormData>({ name: '', nakshatra: '' });
  const [result, setResult] = useState<CompatibilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canCalculate = personA.nakshatra && personB.nakshatra;

  const handleCalculate = useCallback(async () => {
    if (!canCalculate) return;

    setLoading(true);
    setError(null);

    try {
      const apiKey = localStorage.getItem('jre_api_key') || '';
      const response = await api.calculateCompatibility(
        {
          person_a: { nakshatra: personA.nakshatra },
          person_b: { nakshatra: personB.nakshatra },
        },
        apiKey
      );
      setResult(response.data);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to calculate compatibility';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [personA, personB, canCalculate]);

  const handleReset = useCallback(() => {
    setResult(null);
    setPersonA({ name: '', nakshatra: '' });
    setPersonB({ name: '', nakshatra: '' });
    setError(null);
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-medium mb-3"
          style={{ background: 'rgba(197,168,128,0.1)', border: '1px solid rgba(197,168,128,0.2)', color: 'var(--cosmic-gold)' }}>
          <Heart size={11} />
          Ashtakoota Matching
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold"
          style={{ color: 'var(--cosmic-text)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
          Compatibility Check
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
          Classical Vedic Ashtakoota guna milan for relationship assessment
        </p>
      </motion.div>

      <AnimatePresence mode="wait">
        {!result ? (
          /* ── Input Form ────────────────────────────── */
          <motion.div key="form" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.4 }}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <BirthDataForm label="Person A" data={personA} onChange={setPersonA} accentColor="var(--cosmic-gold)" />
              <BirthDataForm label="Person B" data={personB} onChange={setPersonB} accentColor="#93c5fd" />
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl text-xs" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
                {error}
              </div>
            )}

            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleCalculate}
                disabled={!canCalculate || loading}
                className="cosmic-btn flex items-center gap-2 text-sm px-8"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Calculate Compatibility
                  </>
                )}
              </button>
            </div>
          </motion.div>
        ) : (
          /* ── Results Scorecard ──────────────────────── */
          <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            {/* Score Header */}
            <div className="flex flex-col sm:flex-row items-center gap-6 mb-8 p-6 rounded-2xl"
              style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <CircularScore score={result.total_score} max={result.max_score} />
              <div className="flex-1 text-center sm:text-left">
                <h2 className="text-lg font-bold mb-1" style={{ color: 'var(--cosmic-text)', fontFamily: 'var(--font-playfair), Georgia, serif' }}>
                  {result.assessment}
                </h2>
                <p className="text-sm mb-2" style={{ color: 'var(--cosmic-muted)' }}>
                  {personA.name || 'Person A'} ({result.person_a_nakshatra})
                  {' × '}
                  {personB.name || 'Person B'} ({result.person_b_nakshatra})
                </p>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--cosmic-muted)' }}>
                  {result.assessment_details}
                </p>

                {/* Dosha Warnings */}
                {(result.has_nadi_dosha || result.has_bhakoot_dosha) && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {result.has_nadi_dosha && (
                      <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(239,68,68,0.1)', color: '#fca5a5' }}>
                        ⚠️ Nadi Dosha
                      </span>
                    )}
                    {result.has_bhakoot_dosha && (
                      <span className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'rgba(239,68,68,0.1)', color: '#fca5a5' }}>
                        ⚠️ Bhakoot Dosha
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Breakdown */}
            <div className="rounded-2xl p-5 mb-6" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <h3 className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--cosmic-muted)' }}>
                Ashtakoota Breakdown
              </h3>
              <div className="space-y-3">
                {result.kootas.map((f, i) => (
                  <motion.div
                    key={f.name}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-3"
                  >
                    <span className="text-xs font-medium w-28 shrink-0" style={{ color: 'var(--cosmic-text)' }}>
                      {f.name}
                    </span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(f.score / f.max_points) * 100}%` }}
                        transition={{ duration: 0.6, delay: 0.3 + i * 0.05 }}
                        className="h-full rounded-full"
                        style={{ background: getScoreColor(f.score, f.max_points) }}
                      />
                    </div>
                    <span className="text-xs font-bold w-12 text-right" style={{ color: getScoreColor(f.score, f.max_points) }}>
                      {f.score}/{f.max_points}
                    </span>
                    <span className="text-[10px] hidden sm:block w-48" style={{ color: 'var(--cosmic-muted)' }}>
                      {f.description}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-center">
              <button type="button" onClick={handleReset}
                className="cosmic-btn-outline flex items-center gap-2 text-sm">
                <RotateCcw size={14} />
                New Calculation
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
