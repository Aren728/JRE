const charts = [
  { id: "D1", name: "Rashi", domain: "The Physical Reality", desc: "Your physical body, external environment, and the structural 'deck of cards' you have been dealt in this lifetime." },
  { id: "D2", name: "Hora", domain: "Wealth & Values", desc: "Your relationship with security. It shows if you accumulate wealth through effort or inherit resources effortlessly." },
  { id: "D3", name: "Drekkana", domain: "Drive & Siblings", desc: "Your physical energy, courage, and initiative. It dictates whether you face obstacles with bold action or anxiety." },
  { id: "D7", name: "Saptamsha", domain: "Legacy & Creation", desc: "Your creative outputs, children, and what you leave behind. It shows your capacity to nurture raw potential into reality." },
  { id: "D9", name: "Navamsha", domain: "The Soul & Inner Marriage", desc: "The single most important sub-chart. It reveals your inner subconscious alignment, your true potential after age 30, and the actual quality of your closest partnerships." },
  { id: "D10", name: "Dashamsha", domain: "Profession & Impact", desc: "Your social footprint, career trajectory, and how you exert power and authority in the material world." },
  { id: "D12", name: "Dwadamsha", domain: "Ancestral Lineage", desc: "The genetic and karmic inheritances passed down through your parents and bloodline." },
  { id: "D16", name: "Shodashamsha", domain: "Luxury & Inner Peace", desc: "Your capacity to enjoy material vehicles, houses, and comforts without losing your mental tranquility." },
  { id: "D20", name: "Vishamsha", domain: "Spiritual Evolution", desc: "Your internal devotion, meditation capabilities, and how your soul detaches from worldly illusions." },
  { id: "D24", name: "Chaturvimshamsha", domain: "Higher Intellect", desc: "Your capacity for deep learning, memory retention, skill acquisition, and intellectual breakthroughs." },
  { id: "D30", name: "Trimshamsha", domain: "Shadow & Obstacles", desc: "The subconscious blocks, psychological vulnerabilities, and inner demons that manifest as sudden external mishaps." },
  { id: "D60", name: "Shashtiamsha", domain: "The Ultimate Karmic Debt", desc: "The final word on your destiny. It maps the past-life choices that directly created your current life's unexpected twists of fate." },
];

export default function DivisionalChartsSection() {
  return (
    <section className="space-y-8">
      <h2 className="font-['Cinzel'] text-2xl font-bold text-purple-300 flex items-center gap-3">
        <span className="text-3xl">🔬</span> Part 3: The Macro-to-Micro Roadmap (From D1 to D60)
      </h2>
      <p className="text-slate-400">Vedic astrology uses &quot;Harmonic Divisional Charts&quot; (Vargas). Imagine taking a single 30-degree sign in your main chart and slicing it under a microscope. Each slice opens up an entirely new chart dedicated to a specific dimension of human experience.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {charts.map((chart) => (
          <div key={chart.id} className="bg-slate-900 rounded-xl p-6 border border-slate-800 hover:border-amber-500/50 transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <span className="font-['Space_Mono'] text-xl font-bold text-amber-400">{chart.id}</span>
              <span className="font-['Cinzel'] text-sm font-bold text-white">{chart.name}</span>
            </div>
            <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2">{chart.domain}</h4>
            <p className="text-sm text-slate-400 leading-relaxed">{chart.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
