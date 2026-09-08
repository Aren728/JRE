"use client";
import { useState, useEffect } from "react";

type ChartFormat = "north" | "south" | "east";

export default function VedicChartViewer() {
  const [activeFormat, setActiveFormat] = useState<ChartFormat>("north");
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/charts/birth-chart")
      .then((res) => res.json())
      .then((res) => { if (res.success) setData(res.data); })
      .catch((err) => console.error("Chart fetch error:", err));
  }, []);

  if (!data) return <div className="bg-slate-900 p-8 rounded-xl text-center text-amber-400">Loading Cosmic Blueprint...</div>;

  return (
    <div className="bg-slate-900 rounded-xl p-6 md:p-8 shadow-2xl border border-slate-700 max-w-6xl mx-auto my-8">
      {/* Header with Format Switcher */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h2 className="font-['Cinzel'] text-2xl font-bold text-amber-400 mb-1">Your Birth Chart (D1)</h2>
          <p className="font-['Space_Mono'] text-xs text-slate-400">Select your preferred classical format</p>
        </div>
        <div className="flex gap-2">
          {(["north", "south", "east"] as ChartFormat[]).map((fmt) => (
            <button key={fmt} onClick={() => setActiveFormat(fmt)}
              className={`px-4 py-2 rounded-lg font-['Cinzel'] text-xs transition-all ${activeFormat === fmt ? "bg-amber-500 text-slate-900 font-bold" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>
              {fmt === "north" ? "North Indian" : fmt === "south" ? "South Indian" : "East Indian"}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Visuals */}
      <div className="mb-8 flex justify-center">
        {activeFormat === "north" && (
          <div className="w-full max-w-md aspect-square bg-slate-800 rounded-lg p-4 border-2 border-amber-500/30 grid grid-cols-3 grid-rows-3 gap-1">
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">12</div>
            <div className="bg-amber-500/20 border-2 border-amber-500 rounded p-2 text-center flex flex-col justify-center">
              <span className="text-[10px] text-amber-400">1st House</span>
              <span className="text-lg font-bold text-white">{data.lagna}</span>
            </div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">2</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">11</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">Center</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">3</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">10</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">9</div>
            <div className="bg-slate-900/50 rounded p-2 text-center text-xs text-slate-400">4</div>
          </div>
        )}
        {activeFormat === "south" && (
          <div className="w-full max-w-md aspect-square bg-slate-800 rounded-lg p-4 border-2 border-amber-500/30 grid grid-cols-4 grid-rows-4 gap-1">
            {["Pisces", "Aries", "Taurus", "Gemini", "Aquarius", "", "", "Cancer", "Capricorn", "", "", "Leo", "Sagittarius", "Scorpio", "Libra", "Virgo"].map((sign, i) => (
              <div key={i} className={`rounded p-2 text-center flex flex-col justify-center ${sign === data.lagna ? "bg-amber-500/20 border-2 border-amber-500" : "bg-slate-900/50"}`}>
                <span className="text-[10px] text-slate-400">{sign || "Center"}</span>
                {sign === data.lagna && <span className="text-[8px] text-amber-400 font-bold">Lagna</span>}
              </div>
            ))}
          </div>
        )}
        {activeFormat === "east" && (
          <div className="w-full max-w-md aspect-square bg-slate-800 rounded-lg p-4 border-2 border-amber-500/30 flex items-center justify-center">
            <div className="w-64 h-64 rounded-full border-4 border-amber-500/30 relative flex items-center justify-center">
              <div className="w-32 h-32 rounded-full bg-amber-500/20 border-2 border-amber-500 flex items-center justify-center">
                <span className="text-amber-400 font-bold">{data.lagna}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reading Guide */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="font-['Cinzel'] text-lg font-bold text-purple-300 mb-3">How to Read This Chart</h3>
        <div className="font-sans text-sm text-gray-300 space-y-2">
          {activeFormat === "north" && (
            <>
              <p><strong className="text-amber-400">House-Centric Format:</strong> The houses are fixed, signs rotate.</p>
              <p>• The top-center diamond is always your <strong className="text-white">1st House (Lagna)</strong>. Read counter-clockwise.</p>
              <p className="italic text-slate-400 mt-2">💡 <strong>Analogy:</strong> Think of this as an arena where the stages (Houses) are bolted to the floor, and the actors (Signs and Planets) move from stage to stage.</p>
            </>
          )}
          {activeFormat === "south" && (
            <>
              <p><strong className="text-amber-400">Sign-Centric Format:</strong> The signs are fixed, houses move.</p>
              <p>• Aries is always in the second box from top-left. Find the box marked <strong className="text-white">Lagna</strong> to find your 1st House.</p>
              <p className="italic text-slate-400 mt-2">💡 <strong>Analogy:</strong> This is a permanent map of the sky. You simply place your personal &quot;Home Base&quot; pin into one of these twelve neighborhoods.</p>
            </>
          )}
          {activeFormat === "east" && (
            <>
              <p><strong className="text-amber-400">Hybrid Sunburst Format:</strong> Combines spatial direction with elemental focus.</p>
              <p>• Popular in Bengal/Odisha. Locate the Lagna marker and trace houses relative to the fixed sign boundaries.</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
