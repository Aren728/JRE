"use client";

import { useState, useEffect } from "react";

interface OverviewReportData {
  success: boolean;
  data?: {
    narrative: string;
    evaluation_id: string;
    subject?: string;
  };
  error?: string;
}

export default function OverviewReport({ evaluationId }: { evaluationId?: string }) {
  const [reportData, setReportData] = useState<OverviewReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const url = evaluationId 
          ? `${apiBaseUrl}/api/v1/report/overview?fixture_id=${evaluationId}`
          : `${apiBaseUrl}/api/v1/report/overview`;
        
        const response = await fetch(url, {
          headers: {
            'X-API-Key': '', // Will use rate limit or no auth for now
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          setReportData(data);
        } else {
          setError(data.error || 'Failed to generate report');
        }
      } catch (err) {
        setError('Failed to connect to report engine');
      } finally {
        setLoading(false);
      }
    };

    if (evaluationId) {
      fetchReport();
    }
  }, [evaluationId]);

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

  if (error || !reportData?.success) {
    return (
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-700 text-center">
        <p className="text-red-400 mb-2">{error || 'Failed to load report'}</p>
        <p className="text-slate-400 text-sm">The report engine is unavailable. Please try again later.</p>
      </div>
    );
  }

  // Parse markdown-like content and render it
  const renderNarrative = (narrative: string) => {
    const lines = narrative.split('\n');
    
    return lines.map((line, index) => {
      // Headers
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className="font-['Cinzel'] text-2xl font-bold text-amber-400 mt-8 mb-4">
            {line.replace('# ', '')}
          </h1>
        );
      }
      
      if (line.startsWith('## ')) {
        return (
          <h2 key={index} className="font-['Cinzel'] text-xl font-bold text-purple-300 mt-6 mb-3">
            {line.replace('## ', '')}
          </h2>
        );
      }
      
      // Table detection
      if (line.includes('|') && line.includes('---')) {
        return null; // Skip separator lines
      }
      
      if (line.includes('|') && index > 0) {
        const cells = line.split('|').filter(c => c.trim());
        if (cells.length >= 3) {
          return (
            <div key={index} className="flex flex-wrap gap-4 py-2 border-b border-slate-700">
              <div className="flex-1 min-w-[100px]">
                <span className="text-xs text-purple-400 font-medium">{cells[0].trim()}</span>
              </div>
              <div className="flex-1 min-w-[150px]">
                <span className="text-xs text-slate-400">{cells[1].trim()}</span>
              </div>
              <div className="flex-1">
                <span className="text-xs text-slate-300">{cells[2].trim()}</span>
              </div>
            </div>
          );
        }
      }
      
      // Empty lines
      if (line.trim() === '') {
        return <div key={index} className="h-4"></div>;
      }
      
      // Bold text **text**
      const parts = line.split(/(\*\*.*?\\*\*)/g);
      return (
        <p key={index} className="mb-3 text-gray-300 leading-relaxed">
          {parts.map((part, j) => 
            part.startsWith('**') && part.endsWith('**') 
              ? <strong key={j} className="text-white font-semibold">{part.replace(/\*\*/g, '')}</strong> 
              : part
          )}
        </p>
      );
    });
  };

  return (
    <div className="bg-slate-900 rounded-xl p-6 md:p-10 border border-slate-700 shadow-2xl">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-slate-700">
        <h2 className="font-['Cinzel'] text-2xl font-bold text-amber-400 mb-2">
          Psychological & Karmic Blueprint
        </h2>
        <p className="text-sm text-slate-400">
          Generated from actual evaluated data • {reportData.data?.evaluation_id}
        </p>
      </div>
      
      {/* Content */}
      <div className="font-sans text-sm md:text-base">
        {renderNarrative(reportData.data?.narrative || '')}
      </div>
      
      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-slate-700 text-xs text-slate-500 text-center">
        <p>This is a dynamic report generated from your actual chart data.</p>
      </div>
    </div>
  );
}
