// frontend/lib/astrology/aspects.ts

export interface AspectDefinition {
  transitPlanet: string;
  natalPlanet: string;
  type: 'CONJUNCTION' | 'OPPOSITION' | 'TRINE' | 'SQUARE' | 'SEXTILE' | 'SPECIAL';
  angle: number;       // Exact angle difference (0 - 180)
  exactness: number;   // Deviation from exact aspect angle (Orb error in degrees)
  isApplying: boolean; // Transit approaching exact aspect
}

// Classical Vedic special house aspects (from transit planet to target house relative distance)
const VEDIC_SPECIAL_ASPECTS: Record<string, number[]> = {
  Mars: [4, 7, 8],     // 4th, 7th, 8th house aspects
  Jupiter: [5, 7, 9],  // 5th, 7th, 9th house aspects
  Saturn: [3, 7, 10],  // 3rd, 7th, 10th house aspects
  Rahu: [5, 7, 9],
  Ketu: [5, 7, 9],
};

/**
 * Calculates shortest angular distance between two degree points (0° - 360°)
 */
export function getAngularDistance(deg1: number, deg2: number): number {
  const diff = Math.abs(deg1 - deg2) % 360;
  return diff > 180 ? 360 - diff : diff;
}

/**
 * Evaluates active aspect intersections between Transit and Natal planet sets.
 * @param natalPlanets Record of natal planet positions with longitude and house
 * @param transitPlanets Array of transit planet positions with longitude and house
 * @param orb Max allowed orb tolerance in degrees (default: 3.5°)
 */
export function calculateTransitAspects(
  natalPlanets: Record<string, { longitude: number; house: number }>,
  transitPlanets: Array<{ name: string; longitude: number; house: number }>,
  orb: number = 3.5
): AspectDefinition[] {
  const aspects: AspectDefinition[] = [];

  for (const tPlanet of transitPlanets) {
    for (const [nName, nPlanet] of Object.entries(natalPlanets)) {
      const distance = getAngularDistance(tPlanet.longitude, nPlanet.longitude);

      // Check standard geometric aspects
      let type: AspectDefinition['type'] | null = null;
      let targetAngle = 0;

      if (distance <= orb) {
        type = 'CONJUNCTION';
        targetAngle = 0;
      } else if (Math.abs(distance - 60) <= orb) {
        type = 'SEXTILE';
        targetAngle = 60;
      } else if (Math.abs(distance - 90) <= orb) {
        type = 'SQUARE';
        targetAngle = 90;
      } else if (Math.abs(distance - 120) <= orb) {
        type = 'TRINE';
        targetAngle = 120;
      } else if (Math.abs(distance - 180) <= orb) {
        type = 'OPPOSITION';
        targetAngle = 180;
      }

      // Check Parasari Special Aspects by house offset
      const houseDiff = ((nPlanet.house - tPlanet.house + 12) % 12) || 12;
      const specialHouses = VEDIC_SPECIAL_ASPECTS[tPlanet.name] || [7];
      const isSpecialVedic = specialHouses.includes(houseDiff);

      if (type || isSpecialVedic) {
        const exactness = type ? Math.abs(distance - targetAngle) : 0;
        aspects.push({
          transitPlanet: tPlanet.name,
          natalPlanet: nName,
          type: type || 'SPECIAL',
          angle: distance,
          exactness,
          isApplying: tPlanet.longitude < nPlanet.longitude,
        });
      }
    }
  }

  return aspects;
}
