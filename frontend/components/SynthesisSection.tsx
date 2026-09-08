export default function SynthesisSection() {
  return (
    <section className="space-y-8">
      <h2 className="font-['Cinzel'] text-2xl font-bold text-purple-300 flex items-center gap-3">
        <span className="text-3xl">🔗</span> Part 4: Connecting the Dots (The 3-Step Synthesis System)
      </h2>
      <p className="text-slate-400">A common mistake is looking at a divisional chart in isolation. To get an absolute grasp of your reality, you must learn to stack these layers together.</p>

      <div className="space-y-6">
        {/* Step 1 */}
        <div className="bg-slate-900 rounded-xl p-8 border-l-4 border-blue-500">
          <h3 className="font-['Cinzel'] text-xl font-bold text-blue-400 mb-3">Step 1: The Promise (The D1 Outline)</h3>
          <p className="text-slate-300">Look at your main D1 chart. If a planet is placed poorly, it indicates a physical theme that will show up in your environment. It sets the boundary lines of your life.</p>
        </div>
        
        {/* Arrow */}
        <div className="flex justify-center text-slate-600 text-2xl">↓</div>

        {/* Step 2 */}
        <div className="bg-slate-900 rounded-xl p-8 border-l-4 border-purple-500">
          <h3 className="font-['Cinzel'] text-xl font-bold text-purple-400 mb-3">Step 2: The Core Capacity (The D9 Filter)</h3>
          <p className="text-slate-300">Check the exact same planet in your D9 Navamsha chart. If an afflicted Saturn from D1 becomes exalted in D9, your soul possesses the internal intelligence to master the chaos. Conversely, if a planet looks spectacular in D1 but collapses in D9, you will feel internally unfulfilled within that domain.</p>
        </div>

        {/* Arrow */}
        <div className="flex justify-center text-slate-600 text-2xl">↓</div>

        {/* Step 3 */}
        <div className="bg-slate-900 rounded-xl p-8 border-l-4 border-amber-500">
          <h3 className="font-['Cinzel'] text-xl font-bold text-amber-400 mb-3">Step 3: The Root Cause (The D60 Resolution)</h3>
          <p className="text-slate-300">Look at the same planet in your D60 chart. The D60 reveals why you carry this specific struggle or gift. If heavily afflicted in D60, it indicates a sudden, inexplicable karmic debt. If dignified, you possess an invisible reservoir of good merit shielding you from disaster.</p>
        </div>
      </div>

      <div className="bg-gradient-to-br from-purple-900/20 to-slate-900 rounded-xl p-8 border border-purple-500/30 mt-10">
        <h3 className="font-['Cinzel'] text-xl font-bold text-white mb-4">Your Living Integration Strategy</h3>
        <p className="text-slate-300 mb-4">You do not need to constantly consult an astrologer. Your life itself tells you which chart is currently active:</p>
        <ul className="space-y-3 text-sm text-slate-400">
          <li className="flex gap-3"><span className="text-blue-400 font-bold">D1:</span> When your external life changes (new job, relocation, physical illness), your D1 is reacting to the planetary periods.</li>
          <li className="flex gap-3"><span className="text-purple-400 font-bold">D9:</span> When your inner desires shift (seeking deep intimacy, existential void, psychological awakening), your D9 is speaking to you.</li>
          <li className="flex gap-3"><span className="text-amber-400 font-bold">D60:</span> When you experience unprovoked, repeating patterns (falling into the same taboo dynamics, sudden betrayal), your D60 is releasing ancient memory blocks.</li>
        </ul>
        <p className="text-slate-300 mt-6 italic">Your charts are not a sentence; they are a cosmic diagnostic map. You possess the absolute clarity needed to navigate your life with awareness, confidence, and total self-reliance.</p>
      </div>
    </section>
  );
}
