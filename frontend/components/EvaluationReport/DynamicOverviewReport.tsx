"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface EvaluationResponse {
  evaluation_id: string;
  subject: string;
  lagna: string;
  moon_nakshatra: string;
  yogas: any[];
  yoga_count: number;
  formed_count: number;
  processing_time_ms: number;
  engine_version: string;
  disclaimer: string;
  elemental_balance?: Record<string, number>;
  dignity_map?: Record<string, string>;
  planet_details?: Record<string, any>;
  birth_data_display?: Record<string, string>;
}

interface ChartDataForReport {
  lagna: string;
  moon_nakshatra: string;
  nakshatra_ruler?: string;
  nakshatra_symbol?: string;
  planet_details?: Record<string, any>;
}

interface ReportResponse {
  success: boolean;
  data?: {
    narrative: string;
  };
  error?: string;
}

export default function DynamicOverviewReport({ data }: { data: EvaluationResponse | null }) {
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(!data);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) {
      setLoading(false);
      return;
    }

    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);

        // Extract chart data from the actual evaluation results - NO MOCK DATA
        const chartData: ChartDataForReport = {
          lagna: data.lagna || "Unknown",
          moon_nakshatra: data.moon_nakshatra || "Unknown",
          nakshatra_ruler: data.planet_details?.MOON?.nakshatra_ruler || "Unknown",
          nakshatra_symbol: data.planet_details?.MOON?.nakshatra_symbol || "Unknown",
          planet_details: data.planet_details
        };

        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        const response = await fetch(`${apiBaseUrl}/api/v1/report/generate-overview`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': '', // Will use rate limit
          },
          body: JSON.stringify(chartData),
        });

        const result: ReportResponse = await response.json();

        if (result.success && result.data?.narrative) {
          setReportContent(result.data.narrative);
        } else {
          setError(result.error || 'Failed to generate report');
        }
      } catch (err) {
        setError('Failed to connect to report engine');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [data]);

  if (!data) {
    return (
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-700 text-center">
        <p className="text-slate-400">No evaluation data available.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-700 animate-pulse">
        <div className="h-8 w-64 bg-slate-800 rounded mb-6"></div>
        <div className="space-y-4">
          <div className="h-4 bg-slate-800 rounded w-full"></div>
          <div className="h-4 bg-slate-800 rounded w-3/4"></div>
          <div className="h-4 bg-slate-800 rounded w-1/2"></div>
          <div className="h-4 bg-slate-800 rounded w-full mt-4"></div>
          <div className="h-4 bg-slate-800 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error || !reportContent) {
    return (
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-700 text-center">
        <p className="text-red-400 mb-2">{error || 'Failed to generate report'}</p>
        <p className="text-slate-400 text-sm">The report engine is unavailable. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-xl p-6 md:p-10 border border-slate-700 shadow-2xl">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-slate-700">
        <h2 className="font-['Cinzel'] text-2xl font-bold text-amber-400 mb-2">
          Psychological & Karmic Blueprint
        </h2>
        <p className="text-sm text-slate-400">
          Generated from actual evaluated data • {data.evaluation_id}
        </p>
      </div>
      
      {/* Content - Rendered with react-markdown */}
      <div className="font-sans text-sm md:text-base">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <h1 className="font-['Cinzel'] text-2xl font-bold text-amber-400 mt-8 mb-4">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="font-['Cinzel'] text-xl font-bold text-purple-300 mt-6 mb-3">
                {children}
              </h2>
            ),
            strong: ({ children }) => (
              <strong className="text-white font-semibold">{children}</strong>
            ),
            p: ({ children }) => (
              <p className="mb-3 text-gray-300 leading-relaxed">
                {children}
              </p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-inside mb-3 text-gray-300 pl-4">
                {children}
              </ul>
            ),
            li: ({ children }) => (
              <li className="mb-1">{children}</li>
            ),
            table: ({ children }) => (
              <div className="my-6 overflow-x-auto">
                <table className="w-full text-sm">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead>
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody>
                {children}
              </tbody>
            ),
            tr: ({ children }) => (
              <tr className="border-b border-slate-700">
                {children}
              </tr>
            ),
            th: ({ children }) => (
              <th className="text-left py-2 px-3 text-purple-400 font-medium text-xs uppercase tracking-wider">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="py-2 px-3 text-slate-300 text-xs">
                {children}
              </td>
            ),
          }}
        >
          {reportContent}
        </ReactMarkdown>
      </div>
      
      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-slate-700 text-xs text-slate-500 text-center">
        <p>This is a dynamic report generated from your actual chart data.</p>
        <p className="mt-1">Evaluation ID: {data.evaluation_id}</p>
      </div>
    </div>
  );
}
