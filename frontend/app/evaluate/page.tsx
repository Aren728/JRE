'use client';

import React, { useState, useEffect } from 'react';
import EvaluationReportTabs from '@/components/EvaluationReportTabs';

interface BirthDataInput {
  date: string;
  time: string;
  ampm: 'AM' | 'PM';
  locationName: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

interface GeocodingResult {
  display_name: string;
  lat: string;
  lon: string;
}

export default function EvaluatePage() {
  const [formData, setFormData] = useState<BirthDataInput>({
    date: '1995-09-28',
    time: '02:30',
    ampm: 'PM',
    locationName: 'New Delhi, India',
    latitude: 28.6139,
    longitude: 77.2090,
    timezone: 'Asia/Kolkata',
  });

  const [locationQuery, setLocationQuery] = useState('New Delhi, India');
  const [searchResults, setSearchResults] = useState<GeocodingResult[]>([]);
  const [isSearchingLocation, setIsSearchingLocation] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [synthesisMarkdown, setSynthesisMarkdown] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  useEffect(() => {
    if (!locationQuery || locationQuery.length < 3) {
      setSearchResults([]);
      return;
    }

    // Skip the geocode lookup when the text already matches the resolved
    // location (initial mount, or after picking a result). Otherwise the
    // dropdown re-opens on mount and can intercept clicks on the form below.
    if (locationQuery === formData.locationName) {
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearchingLocation(true);
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
            locationQuery
          )}&limit=5`
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data);
          setShowDropdown(true);
        }
      } catch (err) {
        console.error('Location search failed:', err);
      } finally {
        setIsSearchingLocation(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [locationQuery, formData.locationName]);

  const handleSelectLocation = (place: GeocodingResult) => {
    setFormData((prev) => ({
      ...prev,
      locationName: place.display_name,
      latitude: parseFloat(place.lat),
      longitude: parseFloat(place.lon),
    }));
    setLocationQuery(place.display_name);
    setShowDropdown(false);
  };

  // Strictly ensures YYYY-MM-DD with 3 parts regardless of regional input
  const normalizeDate = (rawDate: string): { formatted: string; year: number; month: number; day: number } => {
    let year = 1995, month = 9, day = 28;

    if (rawDate.includes('/')) {
      const parts = rawDate.split('/');
      if (parts.length === 3) {
        // Handle DD/MM/YYYY vs YYYY/MM/DD
        if (parts[0].length === 4) {
          year = parseInt(parts[0], 10);
          month = parseInt(parts[1], 10);
          day = parseInt(parts[2], 10);
        } else {
          day = parseInt(parts[0], 10);
          month = parseInt(parts[1], 10);
          year = parseInt(parts[2], 10);
        }
      }
    } else if (rawDate.includes('-')) {
      const parts = rawDate.split('-');
      if (parts.length === 3) {
        if (parts[0].length === 4) {
          year = parseInt(parts[0], 10);
          month = parseInt(parts[1], 10);
          day = parseInt(parts[2], 10);
        } else {
          day = parseInt(parts[0], 10);
          month = parseInt(parts[1], 10);
          year = parseInt(parts[2], 10);
        }
      }
    }

    const yStr = year.toString().padStart(4, '0');
    const mStr = month.toString().padStart(2, '0');
    const dStr = day.toString().padStart(2, '0');

    return {
      formatted: `${yStr}-${mStr}-${dStr}`,
      year,
      month,
      day,
    };
  };

  // Strictly guarantees HH:mm:ss (3 parts)
  const normalizeTime = (timeStr: string, ampm: 'AM' | 'PM'): string => {
    const clean = timeStr.trim();
    const parts = clean.split(':');
    let hours = parseInt(parts[0], 10) || 12;
    let minutes = parseInt(parts[1], 10) || 0;
    let seconds = parts[2] ? parseInt(parts[2], 10) || 0 : 0;

    if (ampm === 'PM' && hours < 12) hours += 12;
    if (ampm === 'AM' && hours === 12) hours = 0;

    const hStr = hours.toString().padStart(2, '0');
    const mStr = minutes.toString().padStart(2, '0');
    const sStr = seconds.toString().padStart(2, '0');

    return `${hStr}:${mStr}:${sStr}`;
  };

  const handleRunEvaluation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorMsg(null);

    if (!formData.date || new Date(formData.date) < new Date('1582-10-15')) {
      setErrorMsg('Date must be on or after October 15, 1582 (Gregorian boundary limit).');
      return;
    }

    setIsEvaluating(true);

    const dateObj = normalizeDate(formData.date);
    const timeWithSeconds = normalizeTime(formData.time, formData.ampm);

    const payload = {
      date: dateObj.formatted,                         // "1995-09-28"
      time: timeWithSeconds,                           // "14:30:00"
      year: dateObj.year,
      month: dateObj.month,
      day: dateObj.day,
      latitude: Number(formData.latitude),
      longitude: Number(formData.longitude),
      lat: Number(formData.latitude),
      lon: Number(formData.longitude),
      timezone: formData.timezone,
    };

    try {
      const res = await fetch('http://localhost:8000/api/v1/evaluate/custom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'jre-beta-key-alpha',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          typeof errorData.detail === 'string'
            ? errorData.detail
            : errorData.detail?.[0]?.msg
              ? `Validation Error: ${(errorData.detail[0].loc ?? []).join('.')} - ${errorData.detail[0].msg}`
              : `Evaluation error (${res.status})`
        );
      }

      const data = await res.json();
      setEvaluationData(data);
    } catch (err: any) {
      console.error('Evaluation Error:', err);
      setErrorMsg(err.message || 'Failed to complete chart calculation.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleGenerateReport = async () => {
    setIsSynthesizing(true);
    setErrorMsg(null);

    const dateObj = normalizeDate(formData.date);
    const timeWithSeconds = normalizeTime(formData.time, formData.ampm);

    const payload = {
      date: dateObj.formatted,
      time: timeWithSeconds,
      latitude: Number(formData.latitude),
      longitude: Number(formData.longitude),
      timezone: formData.timezone,
    };

    try {
      const res = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Report synthesis failed (${res.status})`);
      }

      const data = await res.json();
      setSynthesisMarkdown(data.synthesis_markdown);
    } catch (err: any) {
      console.error('Synthesis Error:', err);
      setErrorMsg(err.message || 'Error executing AI report synthesis.');
    } finally {
      setIsSynthesizing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-amber-400 mb-2">Chart Evaluation Input</h1>
        <p className="text-xs text-slate-400 mb-6">
          Provide birth parameters to compute cosmic positions, house strengths, and planetary dignities.
        </p>

        <form onSubmit={handleRunEvaluation} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Date</label>
              <input
                type="date"
                min="1582-10-15"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Time (12-hour)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="02:30"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                  required
                />
                <select
                  value={formData.ampm}
                  onChange={(e) =>
                    setFormData({ ...formData, ampm: e.target.value as 'AM' | 'PM' })
                  }
                  className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-amber-400 font-bold focus:outline-none focus:border-amber-500"
                >
                  <option value="AM">AM</option>
                  <option value="PM">PM</option>
                </select>
              </div>
            </div>

            <div className="relative md:col-span-2">
              <label className="block text-slate-400 font-medium mb-1">
                Birth Location (City Search)
              </label>
              <input
                type="text"
                placeholder="Search city (e.g. New Delhi, London, Tokyo)..."
                value={locationQuery}
                onChange={(e) => {
                  setLocationQuery(e.target.value);
                  setShowDropdown(true);
                }}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
              />
              {isSearchingLocation && (
                <span className="absolute right-3 top-8 text-[10px] text-amber-400">
                  Searching...
                </span>
              )}

              {showDropdown && searchResults.length > 0 && (
                <ul className="absolute z-50 w-full bg-slate-900 border border-slate-700 rounded-lg mt-1 max-h-48 overflow-y-auto shadow-2xl">
                  {searchResults.map((place, index) => (
                    <li
                      key={index}
                      onClick={() => handleSelectLocation(place)}
                      className="px-3 py-2 text-xs hover:bg-slate-800 text-slate-300 cursor-pointer border-b border-slate-800 last:border-b-0"
                    >
                      {place.display_name}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Timezone</label>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
              >
                <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                <option value="Europe/London">Europe/London (GMT/BST)</option>
                <option value="Europe/Paris">Europe/Paris (CET)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                <option value="Australia/Sydney">Australia/Sydney (AEST)</option>
                <option value="UTC">UTC</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Latitude (°N)</label>
                <input
                  type="number"
                  step="any"
                  value={formData.latitude}
                  onChange={(e) =>
                    setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-medium mb-1">Longitude (°E)</label>
                <input
                  type="number"
                  step="any"
                  value={formData.longitude}
                  onChange={(e) =>
                    setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-950/80 border border-red-500/50 rounded-lg text-red-300 text-xs font-medium">
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={isEvaluating}
            className="w-full bg-amber-500 hover:bg-amber-600 font-bold text-slate-950 py-3 rounded-lg transition-colors text-sm shadow-md mt-4"
          >
            {isEvaluating ? 'Evaluating Chart Data...' : 'Run Evaluation'}
          </button>
        </form>
      </div>

      {evaluationData && (
        <EvaluationReportTabs
          evaluationData={evaluationData}
          birthDisplay={{
            ...formData,
            time: `${formData.time} ${formData.ampm}`,
          }}
          synthesisMarkdown={synthesisMarkdown}
          synthesisError={errorMsg}
          isSynthesizing={isSynthesizing}
          onGenerateReport={handleGenerateReport}
        />
      )}
    </div>
  );
}
