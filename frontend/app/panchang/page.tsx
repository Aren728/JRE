'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import DailyPanchang from '@/components/DailyPanchang';

export default function PanchangPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:py-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1
          className="text-2xl sm:text-3xl font-bold"
          style={{
            color: 'var(--cosmic-text)',
            fontFamily: 'var(--font-playfair), Georgia, serif',
          }}
        >
          Daily Panchang
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--cosmic-muted)' }}>
          Vedic daily horoscope metrics — Tithi, Nakshatra, Yoga, Karana, and auspicious/inauspicious timings
        </p>
      </motion.div>

      <DailyPanchang />
    </div>
  );
}
