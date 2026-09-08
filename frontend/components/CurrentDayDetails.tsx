"use client";
import { useState, useEffect } from "react";

interface PlanetaryPosition { planet: string; symbol: string; sign: string; degree: string; nakshatra: string; retrograde: boolean; combust: boolean; }

export default function CurrentDayDetails() {
  const [positions, setPositions] = useState<PlanetaryPosition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/dashboard/collective")
      .then((res) => res.json())
      .then((data) => { if (data.success && data.data?.planets) setPositions(data.data.planets); setLoading(false); })
      .catch((err) => { console.error("Dashboard fetch error:", err); setLoading(false); });
  }, []);

  if (loading) return <div className="bg-slate-900 p-6 rounded-xl text-center text-blue-400 font-['Cinzel']">Loading Positions...</div>;

  const today = new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  return (
    <div className="bg-slate-900 rounded-xl p-5 shadow-2xl border border-slate-700">
      <h2 className="font-['Cinzel'] text-xl font-bold text-blue-400 mb-1 flex items-center gap-2 tracking-wide">
        <span>📅</span> Today's Cosmic Weather
      </h2>
      <p className="font-['Space_Mono'] text-xs text-slate-400 mb-4">{today}</p>

      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="font-['Cinzel'] text-xs font-semibold text-blue-300 uppercase tracking-wider mb-3">Planetary Positions (Sidereal Lahiri)</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                {["Planet", "Sign", "Degree", "Nakshatra", "Status"].map(h => (
                  <th key={h} className="font-['Space_Mono'] text-[10px] text-slate-400 uppercase text-left py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.planet} className="border-b border-slate-800 hover:bg-slate-700/30">
                  <td className="py-2 font-['Space_Mono'] text-xs text-white"><span className="text-sm mr-1">{pos.symbol}</span>{pos.planet}</td>
                  <td className="py-2 font-['Cinzel'] text-xs font-semibold text-blue-200">{pos.sign}</td>
                  <td className="py-2 font-['Space_Mono'] text-xs text-gray-300">{pos.degree}</td>
                  <td className="py-2 font-['MedievalSharp'] text-xs text-purple-200">{pos.nakshatra}</td>
                  <td className="py-2">
                    {pos.retrograde && <span className="inline-block bg-red-900/50 text-red-300 text-[10px] px-1.5 py-0.5 rounded mr-1 font-['Space_Mono']">℞</span>}
                    {pos.combust && <span className="inline-block bg-orange-900/50 text-orange-300 text-[10px] px-1.5 py-0.5 rounded font-['Space_Mono']">🔥</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
