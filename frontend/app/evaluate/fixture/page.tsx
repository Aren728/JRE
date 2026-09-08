'use client';

import { useState, useEffect } from 'react';
import { api, EvaluationResponse } from '@/lib/api';
import ApiKeyInput, { useApiKey } from '@/components/ApiKeyInput';
import {
  ClipboardList, Loader2, Sparkles, ExternalLink,
  CheckCircle2, AlertTriangle, RotateCcw, Copy, Key,
  Download, AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button type="button" onClick={handleCopy} className="p-1 rounded" style={{ color: 'var(--text-secondary)' }} title="Copy">
      {copied ? <CheckCircle2 size={14} className="text-green-400" /> : <Copy size={14} />}
    </button>
  );
}

export default function EvaluateFixturePage() {
  const { apiKey, setApiKey } = useApiKey();
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<EvaluationResponse | null>(null);
  const [fixtures, setFixtures] = useState<string[]>([]);
  const [selectedFixture, setSelectedFixture] = useState('');
  const [loadingFixtures, setLoadingFixtures] = useState(false);

  useEffect(() => {
    if (apiKey) {
      setLoadingFixtures(true);
      api.getFixtures(apiKey)
        .then((res) => setFixtures(res.data.fixtures))
        .catch(() => setError('Failed to load fixtures. Check your API key.'))
        .finally(() => setLoadingFixtures(false));
    }
  }, [apiKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey || !selectedFixture) {
      setError('Please enter API key and select a fixture');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await api.evaluateFixture({ fixture_id: selectedFixture }, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Evaluation failed.');
    } finally {
      setLoading(false);
    }
  };

  const formatFixtureName = (name: string) =>
    name.replace(/^chart_\d+_/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const handleDownloadPdf = async () => {
    if (!apiKey || !selectedFixture) return;
    setPdfLoading(true);
    try {
      const response = await api.downloadPdfFixture(selectedFixture, apiKey);
      const blob = new Blob([response.data as BlobPart], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jre-report-${result?.evaluation_id || selectedFixture}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('PDF generation failed.');
    } finally {
      setPdfLoading(false);
    }
  };

  const [jatakamLoading, setJatakamLoading] = useState(false);

  const handleDownloadJatakam = async () => {
    if (!apiKey || !selectedFixture) return;
    setJatakamLoading(true);
    try {
      const response = await api.downloadJatakamBook(selectedFixture, apiKey, 'pdf');
      const blob = new Blob([response.data as BlobPart], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jatakam-${result?.evaluation_id || selectedFixture}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Jatakam Book generation failed.');
    } finally {
      setJatakamLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:py-12">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
          style={{
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            color: '#93c5fd',
          }}
        >
          <ClipboardList size={12} />
          Historical Charts
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
          Evaluate a Fixture
        </h1>
        <p className="text-base max-w-xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
          Select from 50+ pre-validated historical chart fixtures to run through the evaluation pipeline.
        </p>
      </motion.div>

      <AnimatePresence mode="wait">
        {!result ? (
          <motion.form
            key="form"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.4 }}
            onSubmit={handleSubmit}
            className="glass-card p-6 sm:p-8 space-y-6 max-w-2xl mx-auto"
          >
            {/* Fixture Selector */}
            <div>
              <label className="cosmic-label">
                <ClipboardList size={12} className="inline mr-1" />
                Select Chart Fixture
              </label>
              <select
                value={selectedFixture}
                onChange={(e) => setSelectedFixture(e.target.value)}
                className="cosmic-select"
                disabled={loadingFixtures}
              >
                <option value="">{loadingFixtures ? 'Loading fixtures…' : 'Choose a historical chart…'}</option>
                {fixtures.map((f) => (
                  <option key={f} value={f}>{formatFixtureName(f)}</option>
                ))}
              </select>
              <p className="text-[11px] mt-1.5" style={{ color: 'var(--text-secondary)', opacity: 0.6 }}>
                {fixtures.length} fixtures available
              </p>
            </div>

            {/* API Key */}
            <div>
              <SectionHeader icon={<Key size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="AUTHENTICATION" />
              <ApiKeyInput value={apiKey} onChange={setApiKey} />
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 rounded-xl flex items-start gap-3"
                style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)' }}
              >
                <AlertTriangle size={18} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-sm" style={{ color: '#fca5a5' }}>{error}</p>
              </motion.div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !selectedFixture}
              className="cosmic-btn w-full text-base py-3.5 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Evaluating…
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Run Evaluation
                </>
              )}
            </button>
          </motion.form>
        ) : (
          /* ── Results ──────────────────────────────────── */
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            {/* Success Banner */}
            <div className="glass-card p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="w-12 h-12 rounded-full flex items-center justify-center shrink-0"
                style={{ background: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.3)' }}
              >
                <CheckCircle2 size={24} className="text-green-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {result.subject || formatFixtureName(selectedFixture)}
                </h2>
                <div className="flex flex-wrap items-center gap-3 mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                  <span>Lagna: <strong style={{ color: 'var(--cosmic-accent)' }}>{result.lagna}</strong></span>
                  <span>·</span>
                  <span>Moon: {result.moon_nakshatra}</span>
                  <span>·</span>
                  <span>{result.yoga_count} yogas ({result.formed_count} active)</span>
                  <span>·</span>
                  <span className="flex items-center gap-1">
                    ID: <code className="text-[11px]" style={{ color: 'var(--cosmic-gold)' }}>{result.evaluation_id}</code>
                    <CopyButton text={result.evaluation_id} />
                  </span>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  type="button"
                  onClick={handleDownloadPdf}
                  disabled={pdfLoading}
                  className="cosmic-btn-outline text-xs flex items-center gap-1"
                  title="Download 9-step comprehensive PDF report"
                >
                  {pdfLoading ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />} Comprehensive PDF
                </button>
                <button
                  type="button"
                  onClick={handleDownloadJatakam}
                  disabled={jatakamLoading}
                  className="cosmic-btn text-xs flex items-center gap-1"
                  title="Generate complete 90-year Jatakam Book"
                  style={{ background: 'linear-gradient(135deg, #8B0000, #c0392b)', color: 'white', border: 'none' }}
                >
                  {jatakamLoading ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />} 90-Year Jatakam Book
                </button>
                <Link
                  href={`/report/${result.evaluation_id}`}
                  className="cosmic-btn-outline text-xs flex items-center gap-1"
                >
                  <ExternalLink size={12} /> Report
                </Link>
                <Link
                  href={`/feedback?eval_id=${result.evaluation_id}`}
                  className="cosmic-btn-outline text-xs flex items-center gap-1"
                >
                  Feedback
                </Link>
              </div>
            </div>

            {/* Unknown TOB Warning */}
            {result.unknown_tob && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card-static p-5 flex items-start gap-3"
                style={{
                  background: 'rgba(234, 179, 8, 0.08)',
                  border: '1px solid rgba(234, 179, 8, 0.25)',
                }}
              >
                <AlertCircle size={18} className="text-yellow-400 mt-0.5 shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-yellow-300 mb-1">⚠ Unknown Time of Birth</p>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    Birth time was not provided. Noon default used. Lagna-dependent yogas suspended.
                  </p>
                  {result.skipped_yogas.length > 0 && (
                    <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      Skipped: {result.skipped_yogas.join(', ')}
                    </p>
                  )}
                </div>
              </motion.div>
            )}

            {/* Elemental & Dignity Summary */}
            {(Object.keys(result.elemental_balance || {}).length > 0 || Object.keys(result.dignity_map || {}).length > 0) && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-6"
              >
                <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--cosmic-accent)' }}>
                  CHART SIGNATURES
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Object.keys(result.elemental_balance || {}).length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>ELEMENTAL BALANCE</p>
                      <div className="flex gap-3 flex-wrap">
                        {Object.entries(result.elemental_balance).map(([elem, count]) => (
                          <div key={elem} className="flex items-center gap-1.5">
                            <span className="text-sm">{elem === 'fire' ? '🔥' : elem === 'earth' ? '🌍' : elem === 'air' ? '💨' : '💧'}</span>
                            <span className="text-xs capitalize" style={{ color: 'var(--text-primary)' }}>{elem}</span>
                            <span className="text-xs font-bold" style={{ color: 'var(--cosmic-gold)' }}>{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {Object.keys(result.dignity_map || {}).length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>PLANETARY DIGNITIES</p>
                      <div className="flex gap-2 flex-wrap">
                        {Object.entries(result.dignity_map).slice(0, 8).map(([planet, dignity]) => (
                          <span
                            key={planet}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
                            style={{
                              background: dignity === 'Exalted' ? 'rgba(34,197,94,0.15)' :
                                         dignity === 'Debilitated' ? 'rgba(239,68,68,0.15)' :
                                         'rgba(255,255,255,0.05)',
                              color: dignity === 'Exalted' ? '#4ade80' :
                                     dignity === 'Debilitated' ? '#f87171' :
                                     'var(--text-secondary)',
                              border: '1px solid rgba(255,255,255,0.08)',
                            }}
                          >
                            {planet}: {dignity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Yogas Table */}
            <div className="glass-card p-6 overflow-x-auto">
              <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--cosmic-accent)' }}>
                DETECTED YOGAS
              </h3>
              <table className="cosmic-table">
                <thead>
                  <tr>
                    <th>Yoga</th>
                    <th>Status</th>
                    <th>Planets</th>
                    <th>Strength</th>
                    <th>Dynamic</th>
                    <th className="hidden sm:table-cell">Domains</th>
                  </tr>
                </thead>
                <tbody>
                  {result.yogas.map((yoga, i) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.03 }}
                    >
                      <td className="font-medium">{yoga.yoga_name}</td>
                      <td>
                        <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${
                          yoga.status === 'FORMED' ? 'badge-formed' :
                          yoga.status === 'WEAKENED' ? 'badge-weakened' :
                          'badge-not-formed'
                        }`}>
                          {yoga.status}
                        </span>
                      </td>
                      <td className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {yoga.involved_planets.join(', ') || '—'}
                      </td>
                      <td className="font-medium" style={{ color: 'var(--cosmic-gold-light)' }}>
                        {yoga.static_strength > 0 ? `${(yoga.static_strength * 100).toFixed(0)}%` : '—'}
                      </td>
                      <td className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {yoga.dynamic_strength?.toFixed(2) ?? '—'}
                      </td>
                      <td className="hidden sm:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {yoga.domains.join(', ')}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Disclaimer */}
            <div className="glass-card-static p-4 text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--cosmic-accent)' }}>Disclaimer:</strong> {result.disclaimer}
            </div>

            {/* Actions */}
            <div className="flex justify-center">
              <button type="button" onClick={() => { setResult(null); setError(''); }} className="cosmic-btn-outline flex items-center gap-2">
                <RotateCcw size={14} />
                New Evaluation
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center"
        style={{ background: 'rgba(201, 160, 255, 0.12)', border: '1px solid rgba(201, 160, 255, 0.2)' }}
      >
        {icon}
      </div>
      <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-accent)' }}>
        {title}
      </h3>
    </div>
  );
}
