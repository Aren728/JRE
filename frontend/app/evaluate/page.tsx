'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import ReportTabs from '@/components/ReportTabs';
import { api, EvaluationResponse } from '@/lib/api';
import { getCoordinatesFromPlaceName, GeocodingResult } from '@/lib/geocoding';
import ApiKeyInput, { useApiKey } from '@/components/ApiKeyInput';
import {
  User, MapPin, Calendar, Clock, Key, Loader2, Globe,
  Sparkles, ExternalLink, CheckCircle2, AlertTriangle,
  Copy, RotateCcw, Navigation, Download, AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import DynamicKarmicReport from '@/components/DynamicKarmicReport';

const TIMEZONES = [
  'Asia/Kolkata', 'America/New_York', 'America/Los_Angeles',
  'Europe/London', 'Europe/Berlin', 'Asia/Tokyo',
  'Australia/Sydney', 'America/Chicago', 'Asia/Dubai',
  'Asia/Shanghai', 'Asia/Singapore', 'Pacific/Auckland',
  'Asia/Karachi', 'Asia/Dhaka', 'Asia/Colombo',
  'Asia/Kathmandu', 'Africa/Johannesburg', 'America/Sao_Paulo',
  'Europe/Paris', 'Europe/Moscow', 'Asia/Tokyo',
];

const GENDER_OPTIONS = ['Male', 'Female', 'Other', 'Prefer not to say'];

// ── Date helpers ──────────────────────────────────────
function formatDisplayDate(dateStr: string): string {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

function formatTimeDisplay(time24: string): string {
  if (!time24) return '';
  const [h, m] = time24.split(':').map(Number);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return `${h12}:${m.toString().padStart(2, '0')} ${ampm}`;
}

// ── Section Header ────────────────────────────────────
function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center"
        style={{
          background: 'rgba(201, 160, 255, 0.12)',
          border: '1px solid rgba(201, 160, 255, 0.2)',
        }}
      >
        {icon}
      </div>
      <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-accent)' }}>
        {title}
      </h3>
    </div>
  );
}

// ── Copy Button ───────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      type="button"
      onClick={handleCopy}
      className="p-1 rounded transition-colors"
      style={{ color: 'var(--text-secondary)' }}
      title="Copy"
    >
      {copied ? <CheckCircle2 size={14} className="text-green-400" /> : <Copy size={14} />}
    </button>
  );
}

// ── Main Page ─────────────────────────────────────────
export default function EvaluateCustomPage() {
  const { apiKey, setApiKey } = useApiKey();
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<EvaluationResponse | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoResult, setGeoResult] = useState<GeocodingResult | null>(null);
  const [geoError, setGeoError] = useState('');
  const placeInputRef = useRef<HTMLInputElement>(null);
  const geoTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [form, setForm] = useState({
    name: '',
    gender: '',
    date: '',
    time: '12:00',
    placeOfBirth: '',
    latitude: '',
    longitude: '',
    timezone: 'Asia/Kolkata',
    language: 'en',
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // ── Geocoding with debounce ─────────────────────────
  const handlePlaceChange = useCallback((value: string) => {
    setForm((f) => ({ ...f, placeOfBirth: value }));
    setGeoResult(null);
    setGeoError('');

    if (geoTimeoutRef.current) clearTimeout(geoTimeoutRef.current);

    if (value.length < 3) return;

    geoTimeoutRef.current = setTimeout(async () => {
      setGeoLoading(true);
      try {
        const result = await getCoordinatesFromPlaceName(value);
        setGeoResult(result);
        setForm((f) => ({
          ...f,
          latitude: result.latitude.toFixed(4),
          longitude: result.longitude.toFixed(4),
          timezone: result.timezone || f.timezone,
        }));
        setGeoError('');
      } catch (err: any) {
        setGeoError(err.message || 'Location lookup failed');
      } finally {
        setGeoLoading(false);
      }
    }, 600);
  }, []);

  // ── Current Location ────────────────────────────────
  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser');
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        setForm((f) => ({ ...f, latitude: lat.toFixed(4), longitude: lon.toFixed(4) }));
        setGeoResult({ latitude: lat, longitude: lon, displayName: 'Current Location' });
        setGeoLoading(false);
        setGeoError('');
      },
      () => {
        setGeoError('Unable to retrieve your location');
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // ── Validation ──────────────────────────────────────
  const validate = (): boolean => {
    const errs: Record<string, string> = {};

    if (!apiKey) errs.apiKey = 'API key is required';
    if (!form.date) errs.date = 'Date of birth is required';
    if (!form.time) errs.time = 'Time of birth is required';
    if (!form.latitude || isNaN(parseFloat(form.latitude)))
      errs.latitude = 'Valid latitude is required (-90 to 90)';
    else {
      const lat = parseFloat(form.latitude);
      if (lat < -90 || lat > 90) errs.latitude = 'Latitude must be between -90 and 90';
    }
    if (!form.longitude || isNaN(parseFloat(form.longitude)))
      errs.longitude = 'Valid longitude is required (-180 to 180)';
    else {
      const lon = parseFloat(form.longitude);
      if (lon < -180 || lon > 180) errs.longitude = 'Longitude must be between -180 and 180';
    }

    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // ── Submit ──────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError('');
    try {
      const response = await api.evaluateCustom(
        {
          date: form.date,
          time: form.time,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          timezone: form.timezone,
          language: form.language,
        },
        apiKey
      );
      setResult(response.data);
      // Persist evaluation for other pages (Chart, Report, Transits)
      try {
        const storeData = { ...response.data, _language: form.language };
        localStorage.setItem('jre_last_evaluation', JSON.stringify(storeData));
        // Also store birth data for advanced API calls (Shadbala, Ashtakavarga, Remedies)
        localStorage.setItem('jre_birth_data', JSON.stringify({
          date: form.date,
          time: form.time,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          timezone: form.timezone,
        }));
      } catch { /* storage full or unavailable */ }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Evaluation failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // ── PDF Download ─────────────────────────────────────
  const handleDownloadPdf = async () => {
    if (!apiKey) return;
    setPdfLoading(true);
    try {
      const response = await api.downloadPdfCustom(
        {
          date: form.date,
          time: form.time,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          timezone: form.timezone,
        },
        apiKey
      );
      const blob = new Blob([response.data as BlobPart], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jre-report-${result?.evaluation_id || 'unknown'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('PDF generation failed. Is the backend running with weasyprint?');
    } finally {
      setPdfLoading(false);
    }
  };

  // ── Reset ───────────────────────────────────────────
  const handleReset = () => {
    setResult(null);
    setError('');
    setFormErrors({});
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
            background: 'rgba(201, 160, 255, 0.1)',
            border: '1px solid rgba(201, 160, 255, 0.2)',
            color: 'var(--cosmic-accent)',
          }}
        >
          <Sparkles size={12} />
          Chart Evaluation
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
          Cast a Natal Chart
        </h1>
        <p className="text-base max-w-xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
          Enter birth details to detect classical yogas and evaluate Dasha activations through the 5-layer pipeline.
        </p>
      </motion.div>

      {/* ── Form ──────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {!result ? (
          <motion.form
            key="form"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.4 }}
            onSubmit={handleSubmit}
            className="glass-card p-6 sm:p-8 space-y-8"
          >
            {/* Identity Section */}
            <div>
              <SectionHeader icon={<User size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="IDENTITY" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="cosmic-label">Name (optional)</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="Subject name"
                    className="cosmic-input"
                  />
                </div>
                <div>
                  <label className="cosmic-label">Gender</label>
                  <div className="relative">
                    <select
                      value={form.gender}
                      onChange={(e) => setForm({ ...form, gender: e.target.value })}
                      className="cosmic-select"
                    >
                      <option value="">Select…</option>
                      {GENDER_OPTIONS.map((g) => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Date & Time Section */}
            <div>
              <SectionHeader icon={<Calendar size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="DATE & TIME OF BIRTH" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="cosmic-label">Date of Birth</label>
                  <input
                    type="date"
                    value={form.date}
                    onChange={(e) => setForm({ ...form, date: e.target.value })}
                    className="cosmic-input"
                    required
                  />
                  {form.date && (
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                      {formatDisplayDate(form.date)}
                    </p>
                  )}
                  {formErrors.date && (
                    <p className="text-xs mt-1 flex items-center gap-1" style={{ color: '#f87171' }}>
                      <AlertTriangle size={11} /> {formErrors.date}
                    </p>
                  )}
                </div>

                <div>
                  <label className="cosmic-label">
                    <Clock size={12} className="inline mr-1" />
                    Time of Birth
                  </label>
                  <input
                    type="time"
                    value={form.time}
                    onChange={(e) => setForm({ ...form, time: e.target.value })}
                    className="cosmic-input"
                    required
                  />
                  <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                    {formatTimeDisplay(form.time) || 'Select time (24-hour format)'}
                  </p>
                  {formErrors.time && (
                    <p className="text-xs mt-1 flex items-center gap-1" style={{ color: '#f87171' }}>
                      <AlertTriangle size={11} /> {formErrors.time}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Location Section */}
            <div>
              <SectionHeader icon={<MapPin size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="PLACE OF BIRTH" />
              <div className="space-y-4">
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <input
                      ref={placeInputRef}
                      type="text"
                      value={form.placeOfBirth}
                      onChange={(e) => handlePlaceChange(e.target.value)}
                      placeholder="Start typing a city name…"
                      className="cosmic-input pr-8"
                    />
                    {geoLoading && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <Loader2 size={14} className="animate-spin" style={{ color: 'var(--cosmic-accent)' }} />
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={useCurrentLocation}
                    disabled={geoLoading}
                    className="cosmic-btn-outline flex items-center gap-1.5 whitespace-nowrap"
                    title="Use current location"
                  >
                    <Navigation size={14} />
                    <span className="hidden sm:inline">Use My Location</span>
                  </button>
                </div>

                {geoResult && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="geo-success"
                  >
                    ✓ {geoResult.displayName}
                  </motion.p>
                )}
                {geoError && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="geo-error"
                  >
                    {geoError}
                  </motion.p>
                )}

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="cosmic-label">Latitude</label>
                    <input
                      type="text"
                      value={form.latitude}
                      onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                      placeholder="28.6139"
                      className="cosmic-input"
                      readOnly={!!geoResult}
                      style={geoResult ? { opacity: 0.7 } : {}}
                    />
                    {formErrors.latitude && (
                      <p className="text-xs mt-1" style={{ color: '#f87171' }}>{formErrors.latitude}</p>
                    )}
                  </div>
                  <div>
                    <label className="cosmic-label">Longitude</label>
                    <input
                      type="text"
                      value={form.longitude}
                      onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                      placeholder="77.2090"
                      className="cosmic-input"
                      readOnly={!!geoResult}
                      style={geoResult ? { opacity: 0.7 } : {}}
                    />
                    {formErrors.longitude && (
                      <p className="text-xs mt-1" style={{ color: '#f87171' }}>{formErrors.longitude}</p>
                    )}
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="cosmic-label">Timezone</label>
                    <div className="relative">
                      <select
                        value={form.timezone}
                        onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                        className="cosmic-select"
                      >
                        {TIMEZONES.map((tz) => (
                          <option key={tz} value={tz}>{tz.replace('_', ' ')}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Language */}
            <div>
              <SectionHeader icon={<Globe size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="LANGUAGE" />
              <select
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value })}
                className="cosmic-select"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="ta">தமிழ் (Tamil)</option>
                <option value="ml">മലയാളം (Malayalam)</option>
                <option value="te">తెలుగు (Telugu)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
                <option value="mr">मराठी (Marathi)</option>
                <option value="bn">বাংলা (Bengali)</option>
                <option value="as">অসমীয়া (Assamese)</option>
                <option value="or">ଓଡ଼ିଆ (Odia)</option>
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="gu">ગુજરાતી (Gujarati)</option>
              </select>
              <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                Report language. Astrological terms remain in English/Sanskrit.
              </p>
            </div>

            {/* API Key */}
            <div>
              <SectionHeader icon={<Key size={16} style={{ color: 'var(--cosmic-accent)' }} />} title="AUTHENTICATION" />
              <ApiKeyInput value={apiKey} onChange={setApiKey} />
              {formErrors.apiKey && (
                <p className="text-xs mt-1" style={{ color: '#f87171' }}>{formErrors.apiKey}</p>
              )}
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 rounded-xl flex items-start gap-3"
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                }}
              >
                <AlertTriangle size={18} className="text-red-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-300">Evaluation Failed</p>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{error}</p>
                </div>
              </motion.div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="cosmic-btn w-full text-base py-3.5 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Computing Yogas & Dasha…
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
            <div
              className="glass-card p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4"
            >
              <div className="w-12 h-12 rounded-full flex items-center justify-center shrink-0"
                style={{ background: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.3)' }}
              >
                <CheckCircle2 size={24} className="text-green-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Evaluation Complete
                </h2>
                <div className="flex flex-wrap items-center gap-3 mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                  <span className="flex items-center gap-1">
                    Lagna: <strong style={{ color: 'var(--cosmic-accent)' }}>{result.lagna}</strong>
                  </span>
                  <span>·</span>
                  <span>
                    {result.yoga_count} yogas ({result.formed_count} active)
                  </span>
                  <span>·</span>
                  <span>{result.processing_time_ms.toFixed(1)}ms</span>
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
                <Link
                  href={`/report/${result.evaluation_id}`}
                  className="cosmic-btn-outline text-xs flex items-center gap-1"
                >
                  <ExternalLink size={12} /> Full Report
                </Link>
                <Link
                  href={`/feedback?eval_id=${result.evaluation_id}`}
                  className="cosmic-btn-outline text-xs flex items-center gap-1"
                >
                  Submit Feedback
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
                    Birth time was not provided. Noon (12:00) was used as a computational default.
                    The computed Lagna is unreliable — <strong>Lagna-dependent yogas have been suspended</strong>.
                  </p>
                  {result.skipped_yogas.length > 0 && (
                    <p className="mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
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
                  {/* Elemental Balance */}
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
                  {/* Dignity Summary */}
                  {Object.keys(result.dignity_map || {}).length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>PLANETARY DIGNITIES</p>
                      <div className="flex gap-2 flex-wrap">
                        {Object.entries(result.dignity_map).map(([planet, dignity]) => (
                          <span
                            key={planet}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
                            style={{
                              background: dignity === 'Exalted' ? 'rgba(34,197,94,0.15)' :
                                         dignity === 'Debilitated' ? 'rgba(239,68,68,0.15)' :
                                         dignity === 'Own Sign' ? 'rgba(59,130,246,0.15)' :
                                         'rgba(255,255,255,0.05)',
                              color: dignity === 'Exalted' ? '#4ade80' :
                                     dignity === 'Deilitated' ? '#f87171' :
                                     dignity === 'Own Sign' ? '#60a5fa' :
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
                      <td className="hidden sm:table-cell text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {yoga.domains.join(', ')}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Disclaimer */}
            <div
              className="glass-card-static p-4 text-xs leading-relaxed"
              style={{ color: 'var(--text-secondary)' }}
            >
              <strong style={{ color: 'var(--cosmic-accent)' }}>Disclaimer:</strong>{' '}
              {result.disclaimer}
            </div>

            {/* Actions */}
            <div className="flex justify-center">
              <button
                type="button"
                onClick={handleReset}
                className="cosmic-btn-outline flex items-center gap-2"
              >
                <RotateCcw size={14} />
                New Evaluation
              </button>
            </div>

            {/* Dynamic Overview Report - Generated beneath evaluation results */}
            <div className="mt-8">
              <h2 className="font-['Cinzel'] text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                <Sparkles size={18} className="text-purple-400" />
                Dynamic Report Generation
              </h2>
              <DynamicKarmicReport chartData={result} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <ReportTabs />
    </div>
  );
}
