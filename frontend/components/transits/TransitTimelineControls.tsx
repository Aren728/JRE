'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Calendar } from 'lucide-react';

interface TransitTimelineProps {
  currentDate: Date;
  onChangeDate: (newDate: Date) => void;
}

export default function TransitTimelineControls({
  currentDate,
  onChangeDate,
}: TransitTimelineProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<'DAYS' | 'MONTHS' | 'YEARS'>('DAYS');

  // Live Gochara Playback Loop
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying) {
      interval = setInterval(() => {
        stepDate(1);
      }, 800);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, playbackSpeed]);

  const stepDate = useCallback((amount: number) => {
    const updated = new Date(currentDate);
    if (playbackSpeed === 'DAYS') {
      updated.setDate(updated.getDate() + amount);
    } else if (playbackSpeed === 'MONTHS') {
      updated.setMonth(updated.getMonth() + amount);
    } else if (playbackSpeed === 'YEARS') {
      updated.setFullYear(updated.getFullYear() + amount);
    }
    onChangeDate(updated);
  }, [currentDate, playbackSpeed, onChangeDate]);

  const goToNow = () => {
    onChangeDate(new Date());
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 flex flex-col gap-3">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold">
          <Calendar size={14} />
          <span>Gochara Date: {currentDate.toISOString().split('T')[0]}</span>
        </div>

        {/* Step Granularity Selectors */}
        <div className="flex bg-slate-800 rounded p-0.5">
          {(['DAYS', 'MONTHS', 'YEARS'] as const).map((step) => (
            <button
              key={step}
              onClick={() => setPlaybackSpeed(step)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                playbackSpeed === step
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {step}
            </button>
          ))}
        </div>
      </div>

      {/* Playback Controls & Date Input */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => stepDate(-1)}
          className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 transition-colors"
          title="Step Backward"
          type="button"
        >
          <SkipBack size={14} />
        </button>

        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className={`p-1.5 rounded text-white transition-colors ${
            isPlaying ? 'bg-rose-600 hover:bg-rose-500' : 'bg-emerald-600 hover:bg-emerald-500'
          }`}
          title={isPlaying ? 'Pause Playback' : 'Play Timeline'}
          type="button"
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} />}
        </button>

        <button
          onClick={() => stepDate(1)}
          className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 transition-colors"
          title="Step Forward"
          type="button"
        >
          <SkipForward size={14} />
        </button>

        {/* Direct Date Input */}
        <input
          type="date"
          value={currentDate.toISOString().split('T')[0]}
          onChange={(e) => {
            if (e.target.value) {
              onChangeDate(new Date(e.target.value));
            }
          }}
          className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 flex-1 transition-colors"
        />

        <button
          onClick={goToNow}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[10px] text-slate-300 transition-colors"
          type="button"
        >
          Now
        </button>
      </div>
    </div>
  );
}
