"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface DynamicKarmicReportProps {
  chartData: any; // The evaluated JSON data from the parent component
}

export default function DynamicKarmicReport({ chartData }: DynamicKarmicReportProps) {
  const [narrative, setNarrative] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/report/generate-karmic-blueprint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chartData),
      });
      const result = await res.json();
      if (result.success) {
        setNarrative(result.data.narrative);
      }
    } catch (error) {
      console.error("Report generation failed:", error);
    }
    setLoading(false);
  };

  return (
    <div className="mt-8 bg-slate-900 rounded-xl p-8 border border-amber-500/20 shadow-2xl">
      <div className="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
        <h3 className="font-['Cinzel'] text-2xl font-bold text-amber-400">
          ✨ Definitive Astro-Karmic Blueprint
        </h3>
        <button
          onClick={handleGenerate}
          disabled={loading || !chartData}
          className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2 px-6 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "Consulting the Cosmos..." : "Generate Full Report"}
        </button>
      </div>

      {narrative && (
        <div className="prose prose-invert prose-lg max-w-none font-sans text-slate-300">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{narrative}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
