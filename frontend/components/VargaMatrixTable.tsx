'use client';

import React from 'react';
import { PlanetPosition } from '@/lib/api';

interface VargaMatrixTableProps {
  planets: PlanetPosition[];
}

export const VargaMatrixTable: React.FC<VargaMatrixTableProps> = ({
  planets,
}) => {
  return (
    <div className="bg-white p-6 rounded-lg border shadow-sm space-y-4">
      <h3 className="text-lg font-bold text-gray-800">
        Planetary Varga Positions
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="border-b bg-gray-50 text-gray-600 uppercase text-xs">
              <th className="p-3">Planet</th>
              <th className="p-3">D1 Degree</th>
              <th className="p-3">D1 (Rasi)</th>
              <th className="p-3">D3 (Drekkana)</th>
              <th className="p-3">D9 (Navamsha)</th>
              <th className="p-3">D10 (Dashamsha)</th>
              <th className="p-3">D60 (Shashtiamsha)</th>
              <th className="p-3">Nakshatra</th>
              <th className="p-3">Pada</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {planets.map((planet) => (
              <tr key={planet.name} className="hover:bg-gray-50 transition-colors">
                <td className="p-3 font-semibold text-gray-900">{planet.name}</td>
                <td className="p-3 font-mono text-xs text-gray-600">
                  {planet.d1?.degree != null ? planet.d1.degree.toFixed(2) + '°' : 'N/A'}
                </td>
                <td className="p-3">
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-md">
                    {planet.d1?.sign ?? 'N/A'}
                  </span>
                </td>
                <td className="p-3">
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-rose-50 text-rose-700 rounded-md">
                    {planet.d3?.sign ?? 'N/A'}
                  </span>
                </td>
                <td className="p-3">
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-purple-50 text-purple-700 rounded-md">
                    {planet.d9?.sign ?? 'N/A'}
                  </span>
                </td>
                <td className="p-3">
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-amber-50 text-amber-700 rounded-md">
                    {planet.d10?.sign ?? 'N/A'}
                  </span>
                </td>
                <td className="p-3">
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-md">
                    {planet.d60?.sign ?? 'N/A'}
                  </span>
                </td>
                <td className="p-3 font-medium text-gray-800">{planet.nakshatra}</td>
                <td className="p-3">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-xs font-semibold text-gray-700">
                    {planet.pada}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
