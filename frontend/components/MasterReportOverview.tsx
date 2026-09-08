"use client";
import { useState, useEffect } from "react";

export default function MasterReportOverview() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/report/overview")
      .then((res) => res.json())
      .then((res) => {
        if (res.success) setData(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="bg-slate-900 p-8 rounded-xl text-center text-amber-400">Loading Cosmic Blueprint...</div>;
  if (!data) return <div className="bg-slate-900 p-8 rounded-xl text-center text-red-400">Failed to load Overview</div>;

  // Simple text parser to handle bolding and headers without external libraries
  const renderContent = (text: string) => {
    return text.split('\n').map((line, i) => {
      if (line.startsWith('# ')) return <h1 key={i} className="font-['Cinzel'] text-2xl font-bold text-amber-400 mt-6 mb-4">{line.replace('# ', '')}</h1>;
      if (line.startsWith('## ')) return <h2 key={i} className="font-['Cinzel'] text-xl font-bold text-purple-300 mt-5 mb-3">{line.replace('## ', '')}</h2>;
      if (line.startsWith('### ')) return <h3 key={i} className="font-['Cinzel'] text-lg font-bold text-white mt-4 mb-2">{line.replace('### ', '')}</h3>;
      
      // Handle inline bold **text**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={i} className="mb-3 text-gray-300 leading-relaxed">
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
    <div className="bg-slate-900 rounded-xl p-6 md:p-10 shadow-2xl border border-slate-700 max-w-5xl mx-auto my-6">
      <div className="font-sans text-sm md:text-base">
        {renderContent(data.narrative)}
      </div>
    </div>
  );
}
