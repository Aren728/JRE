"use client";

import { useState, useEffect } from "react";

interface RashiPrediction { sign: string; symbol: string; prediction: string; }
interface NakshatraPrediction { name: string; parent_sign: string; lord: string; deity: string; prediction: string; }
interface PredictionsData { date: string; rashis: RashiPrediction[]; nakshatras: NakshatraPrediction[]; }
type TimePeriod = "daily" | "weekly" | "biweekly" | "monthly" | "yearly";

export default function GocharPredictions() {
  const [data, setData] = useState<PredictionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"rashis" | "nakshatras">("rashis");
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("daily");

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8000/api/v1/gochar/predictions?period=${timePeriod}`)
      .then((res) => res.json())
      .then((data) => { if (data.success) setData(data.data); setLoading(false); })
      .catch((err) => { console.error("Gochar fetch error:", err); setLoading(false); });
  }, [timePeriod]);

  if (loading) return <div className="bg-slate-900 p-6 rounded-xl text-center text-purple-400 font-['Cinzel']">Loading Predictions...</div>;
  if (!data) return <div className="bg-slate-900 p-6 rounded-xl text-center text-red-400 font-['Cinzel']">Failed to load</div>;

  const nakshatrasBySign = data.nakshatras.reduce((acc, nak) => {
    if (!acc[nak.parent_sign]) acc[nak.parent_sign] = [];
    acc[nak.parent_sign].push(nak);
    return acc;
  }, {} as Record<string, NakshatraPrediction[]>);

  return (
    <div className="bg-slate-900 rounded-xl p-5 shadow-2xl border border-slate-700">
      <h2 className="font-['Cinzel'] text-xl font-bold text-purple-400 mb-4 flex items-center gap-2 tracking-wide">
        <span>✨</span> Gochar Predictions
      </h2>
      
      {/* Period Selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {(["daily", "weekly", "biweekly", "monthly", "yearly"] as TimePeriod[]).map((p) => (
          <button key={p} onClick={() => setTimePeriod(p)}
            className={`px-3 py-1 rounded text-xs font-['Space_Mono'] font-semibold capitalize transition ${timePeriod === p ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}>
            {p}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-5">
        <button onClick={() => setActiveTab("rashis")} className={`px-4 py-1.5 rounded text-xs font-['Cinzel'] font-semibold transition ${activeTab === "rashis" ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-400"}`}>12 Rashis</button>
        <button onClick={() => setActiveTab("nakshatras")} className={`px-4 py-1.5 rounded text-xs font-['Cinzel'] font-semibold transition ${activeTab === "nakshatras" ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-400"}`}>27 Nakshatras</button>
      </div>

      {/* Rashis */}
      {activeTab === "rashis" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.rashis.map((r) => (
            <div key={r.sign} className="bg-slate-800 rounded-lg p-4 border border-slate-700 hover:border-purple-500/50 transition">
              <h3 className="font-['Cinzel'] text-base font-bold text-white mb-2 flex items-center gap-2">
                <span className="text-xl">{r.symbol}</span> {r.sign}
              </h3>
              <p className="font-sans text-xs text-gray-300 leading-relaxed">{r.prediction}</p>
            </div>
          ))}
        </div>
      )}

      {/* Nakshatras */}
      {activeTab === "nakshatras" && (
        <div className="space-y-4">
          {Object.entries(nakshatrasBySign).map(([sign, naks]) => (
            <div key={sign} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="font-['Cinzel'] text-base font-bold text-purple-300 mb-3 uppercase tracking-wider">{sign}</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {naks.map((nak) => (
                  <div key={nak.name} className="border-l-2 border-purple-500 pl-3 bg-slate-900/50 rounded p-2">
                    <h4 className="font-['MedievalSharp'] text-sm text-purple-200">{nak.name}</h4>
                    <p className="font-['Space_Mono'] text-[10px] text-slate-400 mb-1">Lord: {nak.lord} | Deity: {nak.deity}</p>
                    <p className="font-sans text-xs text-gray-300 leading-relaxed">{nak.prediction}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
