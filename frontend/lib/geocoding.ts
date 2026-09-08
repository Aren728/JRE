export interface GeocodingResult {
  latitude: number;
  longitude: number;
  displayName: string;
  timezone?: string;
}

// Common timezone mapping from country codes
const COUNTRY_TIMEZONE_MAP: Record<string, string> = {
  IN: 'Asia/Kolkata',
  US: 'America/New_York',
  GB: 'Europe/London',
  DE: 'Europe/Berlin',
  FR: 'Europe/Paris',
  JP: 'Asia/Tokyo',
  CN: 'Asia/Shanghai',
  AU: 'Australia/Sydney',
  BR: 'America/Sao_Paulo',
  CA: 'America/Toronto',
  SG: 'Asia/Singapore',
  AE: 'Asia/Dubai',
  SA: 'Asia/Riyadh',
  ZA: 'Africa/Johannesburg',
  NG: 'Africa/Lagos',
  KE: 'Africa/Nairobi',
  MX: 'America/Mexico_City',
  AR: 'America/Argentina/Buenos_Aires',
  RU: 'Europe/Moscow',
  IT: 'Europe/Rome',
  ES: 'Europe/Madrid',
  NL: 'Europe/Amsterdam',
  SE: 'Europe/Stockholm',
  KR: 'Asia/Seoul',
  TH: 'Asia/Bangkok',
  ID: 'Asia/Jakarta',
  MY: 'Asia/Kuala_Lumpur',
  PH: 'Asia/Manila',
  NZ: 'Pacific/Auckland',
  PK: 'Asia/Karachi',
  BD: 'Asia/Dhaka',
  LK: 'Asia/Colombo',
  NP: 'Asia/Kathmandu',
  EG: 'Africa/Cairo',
  TR: 'Europe/Istanbul',
  IL: 'Asia/Jerusalem',
  PT: 'Europe/Lisbon',
  PL: 'Europe/Warsaw',
  AT: 'Europe/Vienna',
  CH: 'Europe/Zurich',
  BE: 'Europe/Brussels',
  DK: 'Europe/Copenhagen',
  FI: 'Europe/Helsinki',
  NO: 'Europe/Oslo',
  IE: 'Europe/Dublin',
  CZ: 'Europe/Prague',
};

function inferTimezone(countryCode?: string): string | undefined {
  if (countryCode && COUNTRY_TIMEZONE_MAP[countryCode.toUpperCase()]) {
    return COUNTRY_TIMEZONE_MAP[countryCode.toUpperCase()];
  }
  return undefined;
}

export async function getCoordinatesFromPlaceName(
  placeName: string
): Promise<GeocodingResult> {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(placeName)}&limit=1&addressdetails=1`,
    {
      headers: {
        'User-Agent': 'JRE-Beta-Frontend/1.0 (jyotish-reasoning-engine)',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Geocoding service error: ${response.status}`);
  }

  const data = await response.json();

  if (!data || data.length === 0) {
    throw new Error(
      `Location "${placeName}" not found. Try entering a city name instead.`
    );
  }

  const result = data[0];
  const countryCode: string | undefined = result.address?.country_code;

  return {
    latitude: parseFloat(result.lat),
    longitude: parseFloat(result.lon),
    displayName: result.display_name,
    timezone: inferTimezone(countryCode),
  };
}
