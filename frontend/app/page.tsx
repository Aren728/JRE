"use client";

import { useEffect, useState } from "react";
import DailyPanchang from "@/components/DailyPanchang";
import CurrentDayDetails from "@/components/CurrentDayDetails";
import GocharPredictions from "@/components/GocharPredictions";

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">
            🕉️ Jyotish Dashboard
          </h1>
          <p className="text-lg text-gray-600">Your Daily Cosmic Guide</p>
        </div>

        {/* Section 1: Daily Panchang */}
        <section>
          <DailyPanchang />
        </section>

        {/* Section 2: Current Day Planetary Positions */}
        <section>
          <CurrentDayDetails />
        </section>

        {/* Section 3: Gochar Predictions */}
        <section>
          <GocharPredictions />
        </section>
      </div>
    </div>
  );
}
