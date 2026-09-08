'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { api } from '@/lib/api';
import ApiKeyInput, { useApiKey } from '@/components/ApiKeyInput';
import {
  FileText, Loader2, AlertTriangle, Key,
} from 'lucide-react';
import { motion } from 'framer-motion';

export default function ReportViewerPage() {
  const params = useParams();
  const evaluationId = params.evaluationId as string;
  const { apiKey, setApiKey } = useApiKey();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState('');
  const [subject, setSubject] = useState('');

  const loadReport = async () => {
    if (!apiKey) { setError('Please enter your API key'); return; }
    setLoading(true);
    setError('');
    try {
      const response = await api.getReport(evaluationId, 'markdown', apiKey);
      setReport(response.data.content);
      setSubject(response.data.subject);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (apiKey && evaluationId) loadReport();
  }, [apiKey, evaluationId]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
          style={{ background: 'rgba(201, 160, 255, 0.1)', border: '1px solid rgba(201, 160, 255, 0.2)', color: 'var(--cosmic-accent)' }}
        >
          <FileText size={12} />
          Report Viewer
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          {subject || 'Evaluation Report'}
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Evaluation ID:{' '}
          <code className="text-xs px-1.5 py-0.5 rounded font-mono" style={{ background: 'rgba(201,160,255,0.1)', color: 'var(--cosmic-gold)' }}>
            {evaluationId}
          </code>
        </p>
      </motion.div>

      {/* API Key + Load */}
      <div className="glass-card p-6 mb-6 max-w-xl">
        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(201, 160, 255, 0.12)', border: '1px solid rgba(201, 160, 255, 0.2)' }}
          >
            <Key size={16} style={{ color: 'var(--cosmic-accent)' }} />
          </div>
          <h3 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--cosmic-accent)' }}>
            AUTHENTICATION
          </h3>
        </div>
        <ApiKeyInput value={apiKey} onChange={setApiKey} />
        <button onClick={loadReport} disabled={loading || !apiKey}
          className="cosmic-btn mt-4 flex items-center gap-2 text-sm"
        >
          {loading ? <><Loader2 size={16} className="animate-spin" /> Loading…</> : <><FileText size={16} /> Load Report</>}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl flex items-start gap-3 mb-6"
          style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)' }}
        >
          <AlertTriangle size={18} className="text-red-400 mt-0.5 shrink-0" />
          <p className="text-sm" style={{ color: '#fca5a5' }}>{error}</p>
        </div>
      )}

      {/* Report Content */}
      {report && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass-card p-6 sm:p-8"
        >
          <div className="prose prose-invert max-w-none
            prose-headings:text-[var(--cosmic-accent)]
            prose-h1:text-2xl prose-h1:mb-4
            prose-h2:text-lg prose-h2:mt-8 prose-h2:mb-3
            prose-h3:text-base prose-h3:mt-6
            prose-p:text-sm prose-p:leading-relaxed
            prose-table:text-sm
            prose-th:text-xs prose-th:uppercase prose-th:tracking-wider
            prose-td:text-sm
            prose-code:text-xs prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
            prose-code:bg-white/5
            prose-strong:text-[var(--cosmic-gold-light)]
            prose-a:text-[var(--cosmic-accent)] prose-a:no-underline hover:prose-a:underline
          ">
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </motion.div>
      )}
    </div>
  );
}
