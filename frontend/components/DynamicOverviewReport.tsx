"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface DynamicOverviewReportProps {
  chartData: {
    lagna: string;
    moon_nakshatra: string;
    nakshatra_ruler?: string;
    nakshatra_symbol?: string;
  };
}

export default function DynamicOverviewReport({ chartData }: DynamicOverviewReportProps) {
  const [narrative, setNarrative] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/report/generate-overview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chartData),
      });
      const data = await res.json();
      if (data.success) {
        setNarrative(data.data.narrative);
      }
    } catch (err) {
      console.error("Failed to generate report:", err);
    }
    setLoading(false);
  };

  return (
    <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 mt-6">
      <button
        onClick={generateReport}
        disabled={loading}
        className="bg-amber-500 text-slate-900 px-6 py-2 rounded-lg font-bold mb-4 hover:bg-amber-400 disabled:opacity-50"
      >
        {loading ? "Generating Report..." : "Generate Humanized Overview"}
      </button>
      
      {narrative && (
        <div className="prose prose-invert max-w-none">
          <ReactMarkdown>{narrative}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
