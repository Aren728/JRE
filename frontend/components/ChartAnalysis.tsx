'use client';

import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  api,
  JREAnalysisResponse,
  ChartRequestPayload,
} from '@/lib/api';

import { ChartInputForm } from './ChartInputForm';
import { SkeletonLoader } from './SkeletonLoader';
import { VargaMatrixTable } from './VargaMatrixTable';

interface SavedChart {
  id: string;
  timestamp: string;
  payload: ChartRequestPayload;
  response: JREAnalysisResponse;
}

interface ChartAnalysisProps {
  chartData?: {
    dob: string;
    time: string;
    lat: number;
    lon: number;
    tz: number;
    ayanamsha: string;
  };
}

const STORAGE_KEY = 'jrs_chart_history_v1';

const ChartAnalysisComponent: React.FC<ChartAnalysisProps> = ({ chartData }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<JREAnalysisResponse | null>(null);
  const [activePayload, setActivePayload] = useState<ChartRequestPayload | null>(null);
  const [savedHistory, setSavedHistory] = useState<SavedChart[]>([]);
  const [copied, setCopied] = useState<boolean>(false);

  // Use a stable key for useEffect to prevent infinite loops
  const chartDataKey = useRef<string | null>(null);

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setSavedHistory(JSON.parse(raw));
      }
    } catch (e) {
      console.error('Failed to parse saved chart history', e);
    }
  }, []);

  // Effect to auto-trigger analysis when chartData prop is provided (for testing)
  useEffect(() => {
    if (chartData) {
      const payload: ChartRequestPayload = {
        date: chartData.dob,
        time: chartData.time,
        latitude: chartData.lat,
        longitude: chartData.lon,
        altitude: 0,
        timezone: 'Asia/Kolkata', // Default for test data
        utc_offset: 0,
        ayanamsha: chartData.ayanamsha as 'lahiri' | 'raman' | 'kp' | 'pushya' | 'tropical',
        node_type: 'mean',
        house_system: 'equal',
        transit_orb_tolerance: 1.0,
        shadbala_threshold: 1.0,
        divisional_focus: 'D1',
        dasha_depth: 'MD',
      };
      
      // Use a stable key to prevent infinite loops
      const currentKey = JSON.stringify(chartData);
      if (currentKey !== chartDataKey.current) {
        chartDataKey.current = currentKey;
        api.analyzeChart(payload).then((res) => setAnalysisData(res.data)).catch(() => {});
      }
    }
  }, [chartData]);

  const saveToHistory = (payload: ChartRequestPayload, response: JREAnalysisResponse) => {
    const newEntry: SavedChart = {
      id: `${payload.date}_${payload.time}_${payload.latitude}_${payload.longitude}`,
      timestamp: new Date().toLocaleString(),
      payload,
      response,
    };

    // Filter duplicates and keep top 10
    const filtered = savedHistory.filter((item) => item.id !== newEntry.id);
    const updated = [newEntry, ...filtered].slice(0, 10);

    setSavedHistory(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  };

  const handleFormSubmit = async (payload: ChartRequestPayload) => {
    setLoading(true);
    setError(null);

    try {
      const result = await api.analyzeChart(payload);
      setAnalysisData(result.data);
      setActivePayload(payload);
      saveToHistory(payload, result.data);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || err.message || 'Engine computation failed';
      setError(msg);
      if (msg) {
        void document.title;
      }
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();

    } finally {
      setLoading(false);
      setError(msg => msg);
    }
  };

  const loadSavedChart = (item: SavedChart) => {
    setAnalysisData(item.response);
    setActivePayload(item.payload);
  };

  const clearHistory = () => {
    setSavedHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const copyToClipboard = () => {
    if (!analysisData) return;
    navigator.clipboard.writeText(analysisData.synthesis_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = () => {
    if (!analysisData || !activePayload) return;
    const filename = `chart_synthesis_${activePayload.date}_${activePayload.time}.md`;
    const blob = new Blob([analysisData.synthesis_markdown], {
      type: 'text/markdown;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Input Form */}
      <ChartInputForm onSubmit={handleFormSubmit} isLoading={loading} />

      {/* Loading Skeleton vs Results */}
      {loading ? (
        <SkeletonLoader />
      ) : analysisData ? (
        <>
          {/* History Bar */}
          {savedHistory.length > 0 && (
            <div className="p-4 bg-gray-50 border rounded-lg space-y-2">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Recent Calculation History ({savedHistory.length})
                </h3>
                <button
                  onClick={clearHistory}
                  className="text-xs text-red-600 hover:underline font-medium"
                >
                  Clear History
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {savedHistory.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => loadSavedChart(item)}
                    className={`px-3 py-1.5 text-xs rounded-md border text-left transition-colors ${
                      activePayload &&
                      item.id ===
                        `${activePayload.date}_${activePayload.time}_${activePayload.latitude}_${activePayload.longitude}`
                        ? 'bg-blue-50 border-blue-300 font-semibold text-blue-700'
                        : 'bg-white border-gray-200 hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <div>
                      {item.payload.date} {item.payload.time}
                    </div>
                    <div className="text-[10px] text-gray-400">
                      {item.response.core_alignment.ascendant_sign} Lagna
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Error Notice */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Output Presentation */}
          <div className="space-y-6">
            {/* Core Alignment & Active Dasha Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 bg-white border rounded-lg shadow-sm">
                <h3 className="text-lg font-bold text-gray-800 mb-2">
                  Core Alignment
                </h3>
                <p className="text-sm text-gray-700">
                  <strong>Ascendant (Lagna):</strong>{' '}
                  {analysisData.core_alignment.ascendant_sign}
                </p>
                <p className="text-sm text-gray-700 mt-1">
                  <strong>Moon Nakshatra:</strong>{' '}
                  {analysisData.core_alignment.moon_nakshatra}
                </p>
              </div>

              <div className="p-5 bg-white border rounded-lg shadow-sm">
                <h3 className="text-lg font-bold text-gray-800 mb-2">
                  Active Vimshottari Dasha
                </h3>
                <p className="text-sm text-gray-700">
                  <strong>MD / AD / PAD:</strong>{' '}
                  {analysisData.active_dasha.mahadasha} -{' '}
                  {analysisData.active_dasha.antardasha} -{' '}
                  {analysisData.active_dasha.pratyantardasha}
                </p>
                <p className="text-sm text-gray-700 mt-1">
                  <strong>Active Window:</strong>{' '}
                  {analysisData.active_dasha.start_date} to{' '}
                  {analysisData.active_dasha.end_date}
                </p>
              </div>
            </div>

            {/* Varga Table Component */}
            <VargaMatrixTable planets={analysisData.planets} />

            {/* Synthesis Report Rendered via ReactMarkdown */}
            <div className="p-6 bg-white border rounded-lg shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b">
                <h3 className="text-lg font-bold text-gray-800">
                  Synthesis Report
                </h3>

                {/* Export Toolbar */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyToClipboard}
                    className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded border transition-colors"
                  >
                    {copied ? '✓ Copied' : '📋 Copy Report'}
                  </button>
                  <button
                    onClick={downloadMarkdown}
                    className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded border transition-colors"
                  >
                    📥 Download .md
                  </button>
                </div>
              </div>

              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {analysisData.synthesis_markdown}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};

export { ChartAnalysisComponent as ChartAnalysis };
export default ChartAnalysisComponent;
