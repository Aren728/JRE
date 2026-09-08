'use client';

import React, { useState } from 'react';
import { ChartRequestPayload } from '@/lib/api';

interface ChartInputFormProps {
  onSubmit: (payload: ChartRequestPayload) => void;
  isLoading: boolean;
}

interface LocationPreset {
  name: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

const LOCATION_PRESETS: LocationPreset[] = [
  { name: 'Chennai', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { name: 'New Delhi', latitude: 28.6139, longitude: 77.2090, timezone: 'Asia/Kolkata' },
  { name: 'London', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { name: 'New York', latitude: 40.7128, longitude: -74.0060, timezone: 'America/New_York' },
  { name: 'Tokyo', latitude: 35.6762, longitude: 139.6503, timezone: 'Asia/Tokyo' },
];

export const ChartInputForm: React.FC<ChartInputFormProps> = ({
  onSubmit,
  isLoading,
}) => {
  const [date, setDate] = useState('1990-01-01');
  const [time, setTime] = useState('12:00:00');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [latitude, setLatitude] = useState<number>(13.0827);
  const [longitude, setLongitude] = useState<number>(80.2707);
  const [ayanamsha, setAyanamsha] = useState<'lahiri' | 'raman' | 'kp'>('lahiri');

  const applyPreset = (preset: LocationPreset) => {
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setTimezone(preset.timezone);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    onSubmit({
      date,
      time,
      timezone,
      latitude: Number(latitude),
      longitude: Number(longitude),
      ayanamsha,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-6 bg-white border rounded-lg shadow-sm space-y-4"
    >
      <h2 className="text-xl font-bold text-gray-800">Chart Parameters</h2>

      {/* Location Presets Bar */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Quick Location Presets
        </label>
        <div className="flex flex-wrap gap-2">
          {LOCATION_PRESETS.map((preset) => (
            <button
              key={preset.name}
              type="button"
              onClick={() => applyPreset(preset)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-full transition-colors border border-gray-200"
            >
              📍 {preset.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
          <label htmlFor="dob-input" className="block text-sm font-medium text-gray-700">
            Date (YYYY-MM-DD)
          </label>
          <input
            id="dob-input"
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 w-full p-2 border rounded-md text-sm"
          />
        </div>

        <div>
          <label htmlFor="time-input" className="block text-sm font-medium text-gray-700">
            Time (HH:MM:SS)
          </label>
          <input
            id="time-input"
            type="time"
            step="1"
            required
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="mt-1 w-full p-2 border rounded-md text-sm"
          />
        </div>

        <div>
          <label htmlFor="tz-input" className="block text-sm font-medium text-gray-700">
            Timezone (IANA)
          </label>
          <input
            id="tz-input"
            type="text"
            required
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="mt-1 w-full p-2 border rounded-md text-sm"
          />
        </div>

        <div>
          <label htmlFor="lat-input" className="block text-sm font-medium text-gray-700">
            Latitude (-90 to 90)
          </label>
          <input
            id="lat-input"
            type="number"
            step="any"
            min="-90"
            max="90"
            required
            value={latitude}
            onChange={(e) => setLatitude(parseFloat(e.target.value))}
            className="mt-1 w-full p-2 border rounded-md text-sm"
          />
        </div>

        <div>
          <label htmlFor="lon-input" className="block text-sm font-medium text-gray-700">
            Longitude (-180 to 180)
          </label>
          <input
            id="lon-input"
            type="number"
            step="any"
            min="-180"
            max="180"
            required
            value={longitude}
            onChange={(e) => setLongitude(parseFloat(e.target.value))}
            className="mt-1 w-full p-2 border rounded-md text-sm"
          />
        </div>

        <div>
          <label htmlFor="ayanamsha-select" className="block text-sm font-medium text-gray-700">
            Ayanamsha
          </label>
          <select
            id="ayanamsha-select"
            value={ayanamsha}
            onChange={(e) => setAyanamsha(e.target.value as 'lahiri' | 'raman' | 'kp')}
            className="mt-1 w-full p-2 border rounded-md text-sm bg-white"
          >
            <option value="lahiri">Lahiri (Chitra Paksha)</option>
            <option value="raman">BV Raman</option>
            <option value="kp">Krishnamurti Paddhati (KP)</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full md:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-md transition-colors disabled:opacity-50"
      >
        {isLoading ? 'Calculating...' : 'Calculate Chart'}
      </button>
    </form>
  );
};
