export default function ChartFormatsSection() {
  return (
    <section className="space-y-8">
      <h2 className="font-['Cinzel'] text-2xl font-bold text-purple-300 flex items-center gap-3">
        <span className="text-3xl">🗺️</span> Part 2: Visualizing the Heavens (The Three Classical Formats)
      </h2>
      <p className="text-slate-400">Ancient India developed three primary spatial maps to project the 360-degree zodiac onto a flat surface. Each reflects a regional mindset, yet all contain the exact same cosmic data.</p>

      {/* North Indian */}
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-800">
        <h3 className="font-['Cinzel'] text-xl font-bold text-amber-400 mb-4">1. The North Indian Diamond Format (House-Centric)</h3>
        <p className="mb-4 text-slate-300">The houses are permanently fixed, while the zodiac signs rotate based on your Ascendant. The top-center diamond is always the 1st House. Read counter-clockwise.</p>
        <div className="bg-slate-950 p-6 rounded-lg border border-slate-700 mb-4 flex justify-center">
          <div className="grid grid-cols-3 gap-2 w-full max-w-md aspect-square">
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">12</div>
            <div className="bg-amber-500/10 border-2 border-amber-500 rounded flex flex-col items-center justify-center"><span className="text-amber-400 text-xs">1st House</span><span className="text-white font-bold">Lagna</span></div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">2</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">11</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-500 text-xs">Center</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">3</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">10</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">9</div>
            <div className="bg-slate-800 rounded flex items-center justify-center text-slate-400">4</div>
          </div>
        </div>
        <div className="bg-slate-800/50 p-4 rounded-lg border-l-4 border-purple-500">
          <p className="text-sm text-slate-300"><strong className="text-purple-300">💡 Layman&apos;s Analogy:</strong> Think of this as an arena where the stages (Houses) are bolted to the floor, and the actors (Signs and Planets) move from stage to stage depending on the hour of your birth.</p>
        </div>
      </div>

      {/* South Indian */}
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-800">
        <h3 className="font-['Cinzel'] text-xl font-bold text-amber-400 mb-4">2. The South Indian Square Format (Sign-Centric)</h3>
        <p className="mb-4 text-slate-300">The signs are permanently fixed in a clockwise pattern. Aries is always in the second box from the top left. The houses move depending on your Ascendant.</p>
        <div className="bg-slate-950 p-6 rounded-lg border border-slate-700 mb-4 flex justify-center">
          <div className="grid grid-cols-4 gap-1 w-full max-w-md aspect-square">
            {["Pisces", "Aries", "Taurus", "Gemini", "Aquarius", "Lagna", "", "Cancer", "Capricorn", "", "", "Leo", "Sagittarius", "Scorpio", "Libra", "Virgo"].map((s, i) => (
              <div key={i} className={`rounded flex flex-col items-center justify-center text-xs ${s === 'Lagna' ? 'bg-amber-500/20 border-2 border-amber-500 text-amber-400 font-bold' : 'bg-slate-800 text-slate-400'}`}>{s}</div>
            ))}
          </div>
        </div>
        <div className="bg-slate-800/50 p-4 rounded-lg border-l-4 border-purple-500">
          <p className="text-sm text-slate-300"><strong className="text-purple-300">💡 Layman&apos;s Analogy:</strong> This is a permanent map of the sky. The celestial neighborhoods never move. You simply place your personal &quot;Home Base&quot; (Lagna) pin into one of these twelve neighborhoods.</p>
        </div>
      </div>

      {/* East Indian */}
      <div className="bg-slate-900 rounded-xl p-8 border border-slate-800">
        <h3 className="font-['Cinzel'] text-xl font-bold text-amber-400 mb-4">3. The East Indian Sunburst Format (Hybrid)</h3>
        <p className="mb-4 text-slate-300">Popular in Bengal and Odisha, this format combines elements of both. The signs are fixed in layout, but it uses a distinct radiant geometry where the central space is divided into triangles.</p>
        <div className="bg-slate-800/50 p-4 rounded-lg border-l-4 border-purple-500">
          <p className="text-sm text-slate-300"><strong className="text-purple-300">💡 How to read it:</strong> It is tracked in a zig-zag or pinwheel manner. You identify the Lagna marker and trace the houses relative to the fixed sign boundaries.</p>
        </div>
      </div>
    </section>
  );
}
