'use client';

import { useState } from 'react';
import { BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';

const CASE_STUDIES = [
  { name: 'kohli', subject: 'Virat Kohli', domain: 'Sports', description: 'Indian cricket legend, former captain', icon: '🏏' },
  { name: 'williams', subject: 'Serena Williams', domain: 'Sports', description: 'Tennis champion, 23 Grand Slams', icon: '🎾' },
  { name: 'ronaldo', subject: 'Cristiano Ronaldo', domain: 'Sports', description: 'Football legend, 5 Ballon d\'Or', icon: '⚽' },
  { name: 'tendulkar', subject: 'Sachin Tendulkar', domain: 'Sports', description: 'Cricket god, 100 international centuries', icon: '🏏' },
  { name: 'musk', subject: 'Elon Musk', domain: 'Business', description: 'Tesla, SpaceX, Twitter acquisition', icon: '🚀' },
  { name: 'bezos', subject: 'Jeff Bezos', domain: 'Business', description: 'Amazon founder, Blue Origin', icon: '📦' },
  { name: 'pichai', subject: 'Sundar Pichai', domain: 'Business', description: 'Google/Alphabet CEO', icon: '🔍' },
  { name: 'ambani', subject: 'Mukesh Ambani', domain: 'Business', description: 'Reliance Industries chairman', icon: '🏗' },
  { name: 'khan_srk', subject: 'Shah Rukh Khan', domain: 'Arts', description: 'Bollywood king, 80+ films', icon: '🎬' },
  { name: 'dicaprio', subject: 'Leonardo DiCaprio', domain: 'Arts', description: 'Oscar-winning actor, climate activist', icon: '🎭' },
  { name: 'chopra', subject: 'Priyanka Chopra', domain: 'Arts', description: 'Miss World, Hollywood crossover', icon: '🌟' },
  { name: 'rajinikanth', subject: 'Rajinikanth', domain: 'Arts', description: 'Tamil cinema superstar', icon: '🎬' },
  { name: 'vijay', subject: 'Joseph Vijay', domain: 'Arts', description: 'Tamil cinema mass hero', icon: '🎬' },
  { name: 'modi', subject: 'Narendra Modi', domain: 'Politics', description: 'Prime Minister of India', icon: '🏛' },
  { name: 'meloni', subject: 'Giorgia Meloni', domain: 'Politics', description: 'Italian Prime Minister', icon: '🏛' },
  { name: 'rowling', subject: 'J.K. Rowling', domain: 'Literature', description: 'Harry Potter author', icon: '📚' },
  { name: 'roy', subject: 'Arundhati Roy', domain: 'Literature', description: 'Booker Prize winner', icon: '📚' },
  { name: 'rahman', subject: 'A.R. Rahman', domain: 'Music', description: 'Oscar-winning composer', icon: '🎵' },
  { name: 'singh', subject: 'Arijit Singh', domain: 'Music', description: 'Playback singing sensation', icon: '🎶' },
  { name: 'beyonce', subject: 'Beyoncé', domain: 'Music', description: 'Global music icon', icon: '🎤' },
];

const DOMAIN_STYLES: Record<string, { color: string; bg: string }> = {
  Sports:    { color: '#93c5fd', bg: 'rgba(59, 130, 246, 0.1)' },
  Business:  { color: '#86efac', bg: 'rgba(34, 197, 94, 0.1)' },
  Arts:      { color: '#c9a0ff', bg: 'rgba(201, 160, 255, 0.1)' },
  Politics:  { color: '#fca5a5', bg: 'rgba(239, 68, 68, 0.1)' },
  Literature:{ color: '#fcd34d', bg: 'rgba(234, 179, 8, 0.1)' },
  Music:     { color: '#f9a8d4', bg: 'rgba(236, 72, 153, 0.1)' },
};

export default function CaseStudiesPage() {
  const [filter, setFilter] = useState('All');
  const domains = ['All', ...new Set(CASE_STUDIES.map((c) => c.domain))];
  const filtered = filter === 'All' ? CASE_STUDIES : CASE_STUDIES.filter((c) => c.domain === filter);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-4"
          style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)', color: '#86efac' }}
        >
          <BookOpen size={12} />
          Case Studies
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
          Modern Personality Case Studies
        </h1>
        <p className="text-base max-w-xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
          20 contemporary figures demonstrating how classical yogas map to real-world life events.
        </p>
      </motion.div>

      {/* Filter Pills */}
      <div className="flex flex-wrap gap-2 mb-8 justify-center">
        {domains.map((d) => {
          const active = filter === d;
          const style = d !== 'All' ? DOMAIN_STYLES[d] : null;
          return (
            <button
              key={d}
              onClick={() => setFilter(d)}
              className="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200"
              style={{
                background: active
                  ? (style?.bg || 'rgba(201, 160, 255, 0.15)')
                  : 'rgba(255, 255, 255, 0.04)',
                border: `1px solid ${active
                  ? (style?.color || 'var(--cosmic-accent)') + '40'
                  : 'rgba(255, 255, 255, 0.08)'}`,
                color: active
                  ? (style?.color || 'var(--cosmic-accent)')
                  : 'var(--text-secondary)',
              }}
            >
              {d}
            </button>
          );
        })}
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((cs, i) => {
          const ds = DOMAIN_STYLES[cs.domain] || DOMAIN_STYLES['Sports'];
          return (
            <motion.div
              key={cs.name}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="glass-card p-5 flex flex-col"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-xl">{cs.icon}</span>
                  <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                    {cs.subject}
                  </h3>
                </div>
                <span
                  className="text-[10px] font-medium px-2 py-0.5 rounded-md"
                  style={{ background: ds.bg, color: ds.color, border: `1px solid ${ds.color}25` }}
                >
                  {cs.domain}
                </span>
              </div>
              <p className="text-sm mb-3 flex-1" style={{ color: 'var(--text-secondary)' }}>
                {cs.description}
              </p>
              <div className="text-[11px] font-mono pt-2" style={{ color: 'var(--text-secondary)', opacity: 0.5, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                chart_051_{cs.name} → chart_070_{cs.name}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Note */}
      <div className="mt-10 glass-card-static p-5 text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
        <strong style={{ color: 'var(--cosmic-accent)' }}>Note:</strong>{' '}
        Full case study Markdown files are available in{' '}
        <code className="text-[11px] px-1 py-0.5 rounded" style={{ background: 'rgba(201,160,255,0.1)' }}>
          docs/case_studies/modern_personalities/
        </code>.
        Each includes Life Event Alignment, Natal Yoga Analysis, Event-Specific Dasha Analysis, and Methodology sections.
      </div>
    </div>
  );
}
