'use client';

import { useState, useEffect } from 'react';
import { api, FeedbackEntry } from '@/lib/api';
import ApiKeyInput, { useApiKey } from '@/components/ApiKeyInput';
import {
  MessageSquare, Key, Loader2, CheckCircle2, AlertTriangle, Send,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const DOMAINS = ['CAREER', 'WEALTH', 'HEALTH', 'MARRIAGE', 'ARTISTIC', 'EDUCATION', 'SPIRITUAL', 'OTHER'];

const FLAGS = [
  { key: 'expert_agreement', label: 'Expert Agreement', color: '#4ade80', bg: 'rgba(34,197,94,0.1)' },
  { key: 'expert_disagreement', label: 'Expert Disagreement', color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
  { key: 'missing_yoga', label: 'Missing Yoga', color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
  { key: 'false_positive', label: 'False Positive', color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
  { key: 'false_negative', label: 'False Negative', color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
  { key: 'timing_issue', label: 'Timing Issue', color: '#facc15', bg: 'rgba(234,179,8,0.1)' },
  { key: 'interpretation_issue', label: 'Interpretation Issue', color: '#facc15', bg: 'rgba(234,179,8,0.1)' },
  { key: 'astronomical_issue', label: 'Astronomical Issue', color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
  { key: 'other', label: 'Other', color: 'var(--text-secondary)', bg: 'rgba(255,255,255,0.05)' },
] as const;

export default function FeedbackPage() {
  const { apiKey, setApiKey } = useApiKey();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [expertId, setExpertId] = useState('');

  useEffect(() => {
    const stored = localStorage.getItem('jre_expert_id');
    if (stored) setExpertId(stored);
    // Check for evaluation_id in URL params
    const params = new URLSearchParams(window.location.search);
    const evalId = params.get('eval_id');
    if (evalId) setForm((f) => ({ ...f, evaluation_id: evalId }));
  }, []);

  const [form, setForm] = useState({
    evaluation_id: '',
    domain: 'CAREER',
    expert_agreement: false,
    expert_disagreement: false,
    missing_yoga: false,
    false_positive: false,
    false_negative: false,
    timing_issue: false,
    interpretation_issue: false,
    astronomical_issue: false,
    other: false,
    free_text: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey || !expertId || !form.evaluation_id) {
      setError('Please fill in API key, Expert ID, and Evaluation ID');
      return;
    }
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      localStorage.setItem('jre_expert_id', expertId);
      const entry: FeedbackEntry = { ...form, expert_id: expertId };
      const response = await api.submitFeedback(entry, apiKey);
      setSuccess(`Feedback recorded — Entry #${response.data.entry_count}`);
      setForm({
        ...form, evaluation_id: '', free_text: '',
        expert_agreement: false, expert_disagreement: false, missing_yoga: false,
        false_positive: false, false_negative: false, timing_issue: false,
        interpretation_issue: false, astronomical_issue: false, other: false,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
          style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.2)', color: '#fbbf24' }}
        >
          <MessageSquare size={12} />
          Expert Feedback
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
          Submit Feedback
        </h1>
        <p className="text-base max-w-lg mx-auto" style={{ color: 'var(--text-secondary)' }}>
          Your feedback feeds the evidence dataset — it does not modify the frozen engine.
        </p>
      </motion.div>

      <form onSubmit={handleSubmit} className="glass-card p-6 sm:p-8 space-y-6">
        {/* IDs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="cosmic-label">Evaluation ID</label>
            <input type="text" value={form.evaluation_id}
              onChange={(e) => setForm({ ...form, evaluation_id: e.target.value })}
              placeholder="Paste from evaluation response"
              className="cosmic-input font-mono text-sm" required />
          </div>
          <div>
            <label className="cosmic-label">Expert ID</label>
            <input type="text" value={expertId} onChange={(e) => setExpertId(e.target.value)}
              placeholder="YOUR_INITIALS"
              className="cosmic-input text-sm" required />
          </div>
        </div>

        {/* Domain */}
        <div>
          <label className="cosmic-label">Domain</label>
          <select value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })}
            className="cosmic-select">
            {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>

        {/* Assessment Flags */}
        <div>
          <label className="cosmic-label mb-3 block">Assessment Flags</label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {FLAGS.map((flag) => {
              const checked = form[flag.key] as boolean;
              return (
                <label
                  key={flag.key}
                  className="flex items-center gap-2.5 p-2.5 rounded-xl cursor-pointer transition-all duration-200"
                  style={{
                    background: checked ? flag.bg : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${checked ? flag.color + '40' : 'rgba(255,255,255,0.06)'}`,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => setForm({ ...form, [flag.key]: e.target.checked })}
                    className="sr-only"
                  />
                  <div
                    className="w-4 h-4 rounded flex items-center justify-center shrink-0 transition-colors"
                    style={{
                      background: checked ? flag.color : 'transparent',
                      border: `1.5px solid ${checked ? flag.color : 'rgba(255,255,255,0.2)'}`,
                    }}
                  >
                    {checked && (
                      <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                        <path d="M1 4L3.5 6.5L9 1" stroke="#000" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </div>
                  <span className="text-sm" style={{ color: checked ? flag.color : 'var(--text-secondary)' }}>
                    {flag.label}
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Free Text */}
        <div>
          <label className="cosmic-label">Detailed Notes</label>
          <textarea
            value={form.free_text}
            onChange={(e) => setForm({ ...form, free_text: e.target.value })}
            rows={4}
            placeholder="Explain your assessment — what matches, what's missing, and why…"
            className="cosmic-input resize-none"
          />
        </div>

        {/* API Key */}
        <div>
          <label className="cosmic-label">
            <Key size={12} className="inline mr-1" />
            Authentication
          </label>
          <ApiKeyInput value={apiKey} onChange={setApiKey} />
        </div>

        {/* Error / Success */}
        <AnimatePresence>
          {error && (
            <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="p-4 rounded-xl flex items-start gap-3"
              style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)' }}
            >
              <AlertTriangle size={18} className="text-red-400 mt-0.5 shrink-0" />
              <p className="text-sm" style={{ color: '#fca5a5' }}>{error}</p>
            </motion.div>
          )}
          {success && (
            <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="p-4 rounded-xl flex items-start gap-3"
              style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.25)' }}
            >
              <CheckCircle2 size={18} className="text-green-400 mt-0.5 shrink-0" />
              <p className="text-sm text-green-300">{success}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Submit */}
        <button type="submit" disabled={loading}
          className="cosmic-btn w-full text-base py-3.5 flex items-center justify-center gap-2"
        >
          {loading ? (
            <><Loader2 size={18} className="animate-spin" /> Submitting…</>
          ) : (
            <><Send size={18} /> Submit Feedback</>
          )}
        </button>
      </form>
    </div>
  );
}
