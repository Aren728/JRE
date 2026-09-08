"use client";
import { useState } from "react";

const mainTabs = [
  { id: "blueprint", label: "My Blueprint", icon: "" },
  { id: "timeline", label: "My Cosmic Timeline", icon: "" },
  { id: "lifepaths", label: "My Life Paths", icon: "🧭" },
  { id: "circle", label: "My Circle", icon: "💖" },
  { id: "alignment", label: "My Alignment", icon: "🕊️" },
];

const subTabs: Record<string, { id: string; label: string }[]> = {
  blueprint: [
    { id: "overview", label: "Overview" },
    { id: "charts", label: "Charts (Kundli)" },
    { id: "horas", label: "Horas" },
    { id: "inner-traits", label: "Inner Traits" },
  ],
  timeline: [
    { id: "shadbala", label: "Shadbala (Inner Powers)" },
    { id: "ashtakavarga", label: "Ashtakavarga (Pillars)" },
    { id: "gochar", label: "Gochar (Transits)" },
  ],
  lifepaths: [
    { id: "yogas", label: "Yogas" },
    { id: "parivartana", label: "Parivartana Yogas" },
    { id: "drishti", label: "Planetary Aspects" },
    { id: "nakshatra-aspects", label: "Nakshatra Aspects" },
  ],
  circle: [
    { id: "relationships", label: "Relationship Analysis" },
    { id: "compatibility", label: "Compatibility (Gunamilan)" },
  ],
  alignment: [
    { id: "parihara", label: "Parihara (Remedies)" },
    { id: "lucky-elements", label: "Lucky Elements" },
  ],
};

// Content from Knowledge Base
const tabContent: Record<string, Record<string, React.ReactNode>> = {
  blueprint: {
    overview: (
      <div className="space-y-6 max-w-4xl">
        <h2 className="font-['Cinzel'] text-3xl font-bold text-amber-400 mb-6">
          The Definitive Astro-Karmic Blueprint
        </h2>
        
        <div className="prose prose-invert prose-lg">
          <p className="text-slate-300 text-lg leading-relaxed">
            Welcome to your complete, definitive Vedic Astrological synthesis. This document is crafted to serve as an exhaustive, standalone manual of your life. It bypasses cold, automated templates to speak directly to the living, breathing human experience behind the symbols.
          </p>
        
          <h3 className="font-['Cinzel'] text-2xl font-bold text-purple-300 mt-8 mb-4">
            Part 1: Visualizing the Heavens (The Three Classical Formats)
          </h3>
        
          <p className="text-slate-300">
            To understand your destiny, you must first know how to look at it. Ancient India developed three primary spatial maps to project the 360-degree zodiac onto a flat surface. Each format reflects a regional mindset, yet all contain the exact same cosmic data.
          </p>

          <div className="bg-slate-800/50 rounded-lg p-6 border-l-4 border-amber-500 mt-6">
            <h4 className="font-['Cinzel'] text-lg font-bold text-amber-400 mb-3">
              1. The North Indian Diamond Format (House-Centric)
            </h4>
            <p className="text-slate-300 mb-3">
              The North Indian chart is structured entirely around the Houses (Bhavas). The positions of the houses are permanently fixed, while the zodiac signs (Rashis) rotate based on your Ascendant (Lagna). The top-center diamond is always the 1st House. You read this chart counter-clockwise.
            </p>
            <p className="text-sm text-slate-400 italic">
              <strong className="text-purple-300">💡 Layman's Analogy:</strong> Think of this as an arena where the stages (Houses) are bolted to the floor, and the actors (Signs and Planets) move from stage to stage depending on the hour of your birth.
            </p>
          </div>

          <div className="bg-slate-800/50 rounded-lg p-6 border-l-4 border-purple-500 mt-6">
            <h4 className="font-['Cinzel'] text-lg font-bold text-purple-400 mb-3">
              2. The South Indian Square Format (Sign-Centric)
            </h4>
            <p className="text-slate-300 mb-3">
              The South Indian chart is structured entirely around the Zodiac Signs (Rashis). The signs are permanently fixed in a clockwise pattern. Aries is always in the second box from the top left. The houses move depending on your Ascendant.
            </p>
            <p className="text-sm text-slate-400 italic">
              <strong className="text-purple-300">💡 Layman's Analogy:</strong> This is a permanent map of the sky. The celestial neighborhoods never move. You simply place your personal "Home Base" (Lagna) pin into one of these twelve neighborhoods.
            </p>
          </div>

          <div className="bg-slate-800/50 rounded-lg p-6 border-l-4 border-emerald-500 mt-6">
            <h4 className="font-['Cinzel'] text-lg font-bold text-emerald-400 mb-3">
              3. The East Indian Sunburst Format (Hybrid)
            </h4>
            <p className="text-slate-300 mb-3">
              Popular in Bengal and Odisha, this format combines elements of both. The signs are fixed in layout, but it uses a distinct radiant geometry where the central space is divided into triangles.
            </p>
          </div>
        </div>
      </div>
    ),
    charts: <div className="text-slate-400">Charts (Kundli) content coming soon...</div>,
    horas: <div className="text-slate-400">Horas content coming soon...</div>,
    "inner-traits": <div className="text-slate-400">Inner Traits content coming soon...</div>,
  },
  timeline: {
    shadbala: <div className="text-slate-400">Shadbala content coming soon...</div>,
    ashtakavarga: <div className="text-slate-400">Ashtakavarga content coming soon...</div>,
    gochar: <div className="text-slate-400">Gochar (Transits) content coming soon...</div>,
  },
  lifepaths: {
    yogas: <div className="text-slate-400">Yogas content coming soon...</div>,
    parivartana: <div className="text-slate-400">Parivartana Yogas content coming soon...</div>,
    drishti: <div className="text-slate-400">Planetary Aspects content coming soon...</div>,
    "nakshatra-aspects": <div className="text-slate-400">Nakshatra Aspects content coming soon...</div>,
  },
  circle: {
    relationships: <div className="text-slate-400">Relationship Analysis content coming soon...</div>,
    compatibility: <div className="text-slate-400">Compatibility (Gunamilan) content coming soon...</div>,
  },
  alignment: {
    parihara: <div className="text-slate-400">Parihara (Remedies) content coming soon...</div>,
    "lucky-elements": <div className="text-slate-400">Lucky Elements content coming soon...</div>,
  },
};

export default function ReportTabs() {
  const [activeMain, setActiveMain] = useState("blueprint");
  const [activeSub, setActiveSub] = useState("overview");

  const handleMainChange = (id: string) => {
    setActiveMain(id);
    setActiveSub(subTabs[id][0].id);
  };

  return (
    <div className="w-full bg-slate-900 rounded-xl border border-slate-800 shadow-2xl overflow-hidden mt-8">
      {/* Main Tabs */}
      <div className="flex flex-wrap border-b border-slate-800 bg-slate-950/50">
        {mainTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleMainChange(tab.id)}
            className={`flex-1 min-w-[140px] px-4 py-4 font-['Cinzel'] text-xs md:text-sm transition-all flex items-center justify-center gap-2 ${
              activeMain === tab.id
                ? "text-amber-400 border-b-2 border-amber-400 bg-slate-900"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <span>{tab.icon}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* Sub Tabs */}
      <div className="flex flex-wrap gap-2 p-4 border-b border-slate-800 bg-slate-900">
        {subTabs[activeMain].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSub(tab.id)}
            className={`px-4 py-2 rounded-lg font-['Space_Mono'] text-xs transition-all ${
              activeSub === tab.id
                ? "bg-amber-500 text-slate-900 font-bold"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="p-8 min-h-[400px]">
        {tabContent[activeMain][activeSub]}
      </div>
    </div>
  );
}
