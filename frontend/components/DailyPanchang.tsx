"use client";

import { useState, useEffect } from "react";

interface PanchangData {
  date: string;
  weekday: string;
  tithi: { name: string; paksha: string; full_name: string; number: number };
  nakshatra: { name: string; lord: string; index: number; pada: number };
  yoga: { name: string; index: number };
  karana: string;
  sunrise: string;
  sunset: string;
  moonrise: string;
  moonset: string;
  rahu_kaalam: string;
  yamagandam: string;
  gulika_kaalam: string;
  abhijit_muhurta: string;
  varjya: string;
}

export default function DailyPanchang() {
  const [panchang, setPanchang] = useState<PanchangData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/panchang/daily")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setPanchang(data.data);
        setLoading(false);
      })
      .catch((err) => { console.error("Panchang fetch error:", err); setLoading(false); });
  }, []);

  if (loading) return <div className="bg-slate-900 p-6 rounded-xl text-center text-amber-400 font-['Cinzel']">Loading Panchang...</div>;
  if (!panchang) return <div className="bg-slate-900 p-6 rounded-xl text-center text-red-400 font-['Cinzel']">Failed to load</div>;

  return (
    <div className="bg-slate-900 rounded-xl p-5 shadow-2xl border border-slate-700">
      <h2 className="font-['Cinzel'] text-xl font-bold text-amber-400 mb-1 flex items-center gap-2 tracking-wide">
        <span>🕉️</span> Daily Panchang
      </h2>
      <p className="font-['Space_Mono'] text-xs text-slate-400 mb-5">{panchang.weekday}, {panchang.date}</p>
      
      {/* Main Elements */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {[
          { label: "Tithi", val: panchang.tithi.full_name, sub: `#${panchang.tithi.number}` },
          { label: "Nakshatra", val: panchang.nakshatra.name, sub: `Lord: ${panchang.nakshatra.lord} | Pada: ${panchang.nakshatra.pada}` },
          { label: "Yoga", val: panchang.yoga.name, sub: `#${panchang.yoga.index}` },
          { label: "Karana", val: panchang.karana, sub: "" }
        ].map((item) => (
          <div key={item.label} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
            <h3 className="font-['Cinzel'] text-xs font-semibold text-amber-500 uppercase tracking-wider mb-1">{item.label}</h3>
            <p className="font-['Space_Mono'] text-sm font-bold text-white">{item.val}</p>
            {item.sub && <p className="font-['Space_Mono'] text-[10px] text-slate-400 mt-1">{item.sub}</p>}
          </div>
        ))}
      </div>

      {/* Celestial Times */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
          <h3 className="font-['Cinzel'] text-xs font-semibold text-amber-500 uppercase tracking-wider mb-2">☀️ Sun</h3>
          <div className="flex justify-between">
            <div><p className="font-['Space_Mono'] text-[10px] text-slate-400">Rise</p><p className="font-['Space_Mono'] text-sm text-white">{panchang.sunrise}</p></div>
            <div className="text-right"><p className="font-['Space_Mono'] text-[10px] text-slate-400">Set</p><p className="font-['Space_Mono'] text-sm text-white">{panchang.sunset}</p></div>
          </div>
        </div>
        <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
          <h3 className="font-['Cinzel'] text-xs font-semibold text-amber-500 uppercase tracking-wider mb-2">🌙 Moon</h3>
          <div className="flex justify-between">
            <div><p className="font-['Space_Mono'] text-[10px] text-slate-400">Rise</p><p className="font-['Space_Mono'] text-sm text-white">{panchang.moonrise}</p></div>
            <div className="text-right"><p className="font-['Space_Mono'] text-[10px] text-slate-400">Set</p><p className="font-['Space_Mono'] text-sm text-white">{panchang.moonset}</p></div>
          </div>
        </div>
      </div>

      {/* Muhurtas */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="font-['Cinzel'] text-sm font-semibold text-amber-400 mb-3 uppercase tracking-wider">⏰ Muhurtas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div className="bg-emerald-900/30 border-l-2 border-emerald-500 rounded p-2">
            <h4 className="font-['Cinzel'] text-[10px] text-emerald-400 uppercase">Abhijit (Auspicious)</h4>
            <p className="font-['Space_Mono'] text-xs text-white">{panchang.abhijit_muhurta}</p>
          </div>
          <div className="bg-red-900/30 border-l-2 border-red-500 rounded p-2">
            <h4 className="font-['Cinzel'] text-[10px] text-red-400 uppercase">Rahu Kaalam</h4>
            <p className="font-['Space_Mono'] text-xs text-white">{panchang.rahu_kaalam}</p>
          </div>
          <div className="bg-purple-900/30 border-l-2 border-purple-500 rounded p-2">
            <h4 className="font-['Cinzel'] text-[10px] text-purple-400 uppercase">Yamagandam</h4>
            <p className="font-['Space_Mono'] text-xs text-white">{panchang.yamagandam}</p>
          </div>
          <div className="bg-amber-900/30 border-l-2 border-amber-500 rounded p-2">
            <h4 className="font-['Cinzel'] text-[10px] text-amber-400 uppercase">Gulika Kaalam</h4>
            <p className="font-['Space_Mono'] text-xs text-white">{panchang.gulika_kaalam}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
