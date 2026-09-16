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
  altitude?: number;
}

const LOCATION_PRESETS: LocationPreset[] = [
  { name: 'Chennai', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { name: 'New Delhi', latitude: 28.6139, longitude: 77.2090, timezone: 'Asia/Kolkata' },
  { name: 'London', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { name: 'New York', latitude: 40.7128, longitude: -74.0060, timezone: 'America/New_York' },
  { name: 'Tokyo', latitude: 35.6762, longitude: 139.6503, timezone: 'Asia/Tokyo' },
  { name: 'Sydney', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
  { name: 'Los Angeles', latitude: 34.0522, longitude: -118.2437, timezone: 'America/Los_Angeles' },
  { name: 'Cape Town', latitude: -33.9249, longitude: 18.4241, timezone: 'Africa/Johannesburg' },
];

interface ControlPanelProps {
  onSubmit: (payload: ChartRequestPayload) => void;
  isLoading: boolean;
}

export const ChartInputForm: React.FC<ChartInputFormProps> = ({
  onSubmit,
  isLoading,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Tab A — Analytical Overview Placeholder */}
      <div className="lg:col-span-1">
        <DASHBOARD_TAB_A onSubmit={onSubmit} isLoading={isLoading} />
      </div>
      {/* Tabs B, C, D consolidated in right panel */}
      <div className="lg:col-span-3">
        <DASHBOARD_TAB_B_EPHEMERIS onSubmit={onSubmit} isLoading={isLoading} />
      </div>
    </div>
  );
};

// ── Tab A: Analytical Overview ──────────────────────────────────────────────
function DASHBOARD_TAB_A({ onSubmit, isLoading }: ControlPanelProps) {
  const [date, setDate] = useState('1990-01-01');
  const [time, setTime] = useState('12:00:00');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [latitude, setLatitude] = useState<number>(13.0827);
  const [longitude, setLongitude] = useState<number>(80.2707);
  const [altitude, setAltitude] = useState<number>(0);
  const [utcOffset, setUtcOffset] = useState<number>(0);

  const applyPreset = (preset: LocationPreset) => {
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setTimezone(preset.timezone);
    if (preset.altitude !== undefined) setAltitude(preset.altitude);
  };

  return (
    <div className="p-5 bg-white border rounded-lg shadow-sm space-y-4 h-fit">
      <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
        <span className="text-blue-600">📊</span> Analytical Overview
      </h2>

      {/* Location Presets */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Quick Locations
        </label>
        <div className="flex flex-wrap gap-1.5">
          {LOCATION_PRESETS.map((p) => (
            <button
              key={p.name}
              type="button"
              onClick={() => applyPreset(p)}
              className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full border border-gray-200"
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Space-Time Data */}
      <div className="space-y-2">
        <div>
          <label className="block text-xs font-medium text-gray-600">Date (YYYY-MM-DD)</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Time (HH:MM:SS)</label>
          <input
            type="time"
            step="1"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Timezone (IANA)</label>
          <input
            type="text"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">UTC Offset Override (hrs)</label>
          <input
            type="number"
            step="0.25"
            value={utcOffset}
            onChange={(e) => setUtcOffset(parseFloat(e.target.value))}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Latitude</label>
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            value={latitude}
            onChange={(e) => setLatitude(parseFloat(e.target.value))}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Longitude</label>
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            value={longitude}
            onChange={(e) => setLongitude(parseFloat(e.target.value))}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600">Altitude (m)</label>
          <input
            type="number"
            step="any"
            value={altitude}
            onChange={(e) => setAltitude(parseFloat(e.target.value))}
            className="w-full mt-0.5 p-1.5 border rounded text-sm"
          />
        </div>
      </div>

      {/* Submit */}
      <button
        type="button"
        disabled={isLoading}
        onClick={() => onSubmit({
          date,
          time,
          latitude,
          longitude,
          altitude,
          timezone,
          utc_offset: utcOffset,
          ayanamsha: 'lahiri',
          node_type: 'mean',
          house_system: 'equal',
          transit_orb_tolerance: 1.0,
          shadbala_threshold: 1.0,
          divisional_focus: 'D1',
          dasha_depth: 'MD',
        })}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium text-sm rounded transition-colors"
      >
        {isLoading ? 'Calculating...' : 'Calculate Chart'}
      </button>

      {/* Placeholder badges */}
      <div className="text-xs text-gray-500 space-y-1 pt-2 border-t">
        <div className="flex justify-between"><span>D1 Chart</span><span className="text-gray-400">—</span></div>
        <div className="flex justify-between"><span>Planetary Dignities</span><span className="text-gray-400">—</span></div>
        <div className="flex justify-between"><span>Active Dasha</span><span className="text-gray-400">—</span></div>
      </div>
    </div>
  );
}

// ── Tab B: Ephemeris & Bhava Table ──────────────────────────────────────────
function DASHBOARD_TAB_B_EPHEMERIS({ onSubmit, isLoading }: ControlPanelProps) {
  const [ayanamsha, setAyanamsha] = useState<ChartRequestPayload['ayanamsha']>('lahiri');
  const [nodeType, setNodeType] = useState<'mean' | 'true'>('mean');
  const [houseSystem, setHouseSystem] = useState<ChartRequestPayload['house_system']>('equal');
  const [transitOrbTolerance, setTransitOrbTolerance] = useState<number>(1.0);
  const [shadbalaThreshold, setShadbalaThreshold] = useState<number>(1.0);
  const [divisionalFocus, setDivisionalFocus] = useState<ChartRequestPayload['divisional_focus']>('D1');
  const [dashaDepth, setDashaDepth] = useState<ChartRequestPayload['dasha_depth']>('MD');

  return (
    <div className="p-5 bg-white border rounded-lg shadow-sm space-y-5">
      <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
        <span className="text-purple-600">🌌</span> Ephemeris & Bhava Settings
      </h2>

      {/* Ayanamsha Models */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Ayanamsha Model
        </label>
        <div className="grid grid-cols-2 gap-2">
          {(['lahiri', 'raman', 'kp', 'pushya', 'tropical'] as const).map((val) => (
            <label
              key={val}
              className={`cursor-pointer px-3 py-1.5 text-xs rounded border transition-colors ${
                ayanamsha === val
                  ? 'bg-blue-100 border-blue-300 text-blue-800 font-medium'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="ayanamsha"
                value={val}
                checked={ayanamsha === val}
                onChange={() => setAyanamsha(val)}
                className="sr-only"
              />
              {val === 'lahiri' && 'Lahiri (Chitrapaksha)'}
              {val === 'raman' && 'BV Raman'}
              {val === 'kp' && 'KP (Krishnamurti)'}
              {val === 'pushya' && 'Pushya Paksha'}
              {val === 'tropical' && 'Tropical (Sayana)'}
            </label>
          ))}
        </div>
      </div>

      {/* Node Calculation Type */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Node Calculation
        </label>
        <div className="flex gap-2">
          {(['mean', 'true'] as const).map((val) => (
            <label
              key={val}
              className={`cursor-pointer px-3 py-1.5 text-xs rounded border transition-colors ${
                nodeType === val
                  ? 'bg-blue-100 border-blue-300 text-blue-800 font-medium'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="node"
                value={val}
                checked={nodeType === val}
                onChange={() => setNodeType(val)}
                className="sr-only"
              />
              {val === 'mean' ? 'Mean Node' : 'True Node'}
            </label>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          True Node affects exact Nakshatra boundary transitions and Rahu/Ketu Dasha balance.
        </p>
      </div>

      {/* House System */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          House System (Bhava Chalit)
        </label>
        <select
          value={houseSystem}
          onChange={(e) => setHouseSystem(e.target.value as ChartRequestPayload['house_system'])}
          className="w-full mt-1 p-1.5 border rounded text-sm bg-white"
        >
          <option value="equal">Equal (Sripati/Pripacha)</option>
          <option value="placidus">Placidus</option>
          <option value="koch">Koch</option>
          <option value="whole_sign">Whole Sign</option>
          <option value="alcabitius">Alcabitius</option>
        </select>
      </div>

      {/* Transit Orb Tolerance */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Transit Orb Tolerance: {transitOrbTolerance.toFixed(1)}°
        </label>
        <input
          type="range"
          min="0.5"
          max="3.0"
          step="0.1"
          value={transitOrbTolerance}
          onChange={(e) => setTransitOrbTolerance(parseFloat(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-0.5">
          <span>0.5° (tight)</span>
          <span>3.0° (loose)</span>
        </div>
      </div>

      {/* Shadbala Strength Threshold */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Shadbala Threshold: {shadbalaThreshold.toFixed(1)}
        </label>
        <input
          type="range"
          min="0.8"
          max="1.5"
          step="0.05"
          value={shadbalaThreshold}
          onChange={(e) => setShadbalaThreshold(parseFloat(e.target.value))}
          className="w-full accent-purple-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-0.5">
          <span>0.8 (permissive)</span>
          <span>1.5 (strict)</span>
        </div>
      </div>

      {/* Divisional Chart Focus */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Divisional Chart Focus (Varga)
        </label>
        <div className="flex gap-2">
          {(['D1', 'D9', 'D10', 'D60'] as const).map((val) => (
            <label
              key={val}
              className={`cursor-pointer px-3 py-1.5 text-xs rounded border transition-colors ${
                divisionalFocus === val
                  ? 'bg-purple-100 border-purple-300 text-purple-800 font-medium'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="varga"
                value={val}
                checked={divisionalFocus === val}
                onChange={() => setDivisionalFocus(val)}
                className="sr-only"
              />
              {val}
            </label>
          ))}
        </div>
      </div>

      {/* Dasha Hierarchy Depth */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Dasha Hierarchy Depth
        </label>
        <select
          value={dashaDepth}
          onChange={(e) => setDashaDepth(e.target.value as ChartRequestPayload['dasha_depth'])}
          className="w-full mt-1 p-1.5 border rounded text-sm bg-white"
        >
          <option value="MD">Mahadasha (MD) only</option>
          <option value="MD_AD">MD + Antardasha (AD)</option>
          <option value="MD_AD_PD">MD + AD + Pratyantardasha (PD)</option>
          <option value="MD_AD_PD_SD">MD + AD + PD + Sookshma (SD)</option>
        </select>
      </div>

      {/* Submit */}
      <button
        type="button"
        disabled={isLoading}
        onClick={() => onSubmit({
          date: '1990-01-01',
          time: '12:00:00',
          latitude: 13.0827,
          longitude: 80.2707,
          altitude: 0,
          timezone: 'Asia/Kolkata',
          utc_offset: 0,
          ayanamsha,
          node_type: nodeType,
          house_system: houseSystem,
          transit_orb_tolerance: transitOrbTolerance,
          shadbala_threshold: shadbalaThreshold,
          divisional_focus: divisionalFocus,
          dasha_depth: dashaDepth,
        })}
        className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium text-sm rounded transition-colors"
      >
        {isLoading ? 'Applying Settings...' : 'Apply Ephemeris Settings'}
      </button>
    </div>
  );
}
