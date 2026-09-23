/**
 * threeExporter — dependency-free Three.js scene-graph builder.
 *
 * Emits the JSON shape consumed by `THREE.ObjectLoader.parse()`:
 * a top-level `geometries` / `materials` registry plus an `object` tree
 * of Group/Mesh nodes referencing them by uuid. No `three` import here —
 * the output is plain serializable data, unit-testable without WebGL.
 *
 * Conventions (Phase 4):
 *  - Ascendant (lagna) longitude is pinned to +Z; longitudes increase
 *    counter-clockwise (`sceneAngleDeg = (lon - ascLon + 90) mod 360`).
 *  - Sign ring: 12 segments · nakshatra ring: 27 · house markers: 12 ·
 *    planet orbs on the inner circle · center hub.
 *  - UUIDs are deterministic (per-instance ordinal counters), so the same
 *    chart produces byte-identical JSON across runs.
 */

// ── Catalogs (Sanskrit names, matching components/NorthIndianChart.tsx) ────

export const SIGN_ORDER = [
  'MESHA', 'VRISHABHA', 'MITHUNA', 'KARKA', 'SIMHA', 'KANYA',
  'TULA', 'VRISHCHIKA', 'DHANUSHA', 'MAKARA', 'KUMBHA', 'MEENA',
] as const;

export const NAKSHATRA_ORDER = [
  'ASHWINI', 'BHARANI', 'KRITTIKA', 'ROHINI', 'MRIGASHIRA', 'ARDRA',
  'PUNARVASU', 'PUSHYA', 'ASHLESHA', 'MAGHA', 'PURVA_PHALGUNI', 'UTTARA_PHALGUNI',
  'HASTA', 'CHITRA', 'SWATI', 'VISHAKHA', 'ANURADHA', 'JYESHTA',
  'MULA', 'PURVA_ASHADHA', 'UTTARA_ASHADHA', 'SHRAVANA', 'DHANISHTA', 'SHATABHISHA',
  'PURVA_BHADRAPADA', 'UTTARA_BHADRAPADA', 'REVATI',
] as const;

/** Classical nine bodies (grahas) with their palette colors. */
export const CLASSICAL_PLANET_BODIES = [
  'SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU',
] as const;

export type ClassicalBody = (typeof CLASSICAL_PLANET_BODIES)[number];

export const PLANET_PALETTE: Record<ClassicalBody, number> = {
  SUN: 0xf59e0b,
  MOON: 0xcbd5e1,
  MARS: 0xef4444,
  MERCURY: 0x34d399,
  JUPITER: 0xa78bfa,
  VENUS: 0xf472b6,
  SATURN: 0x94a3b8,
  RAHU: 0x8b5cf6,
  KETU: 0x64748b,
};

// ── Ring geometry constants ────────────────────────────────────────────────

export const RING_RADII = {
  signRing: 10,
  nakshatraRing: 12,
  houseMarkers: 8,
  planetOrbit: 6.5,
  hub: 0.8,
} as const;

// ── Scene input/output types ───────────────────────────────────────────────

export interface ScenePlanetInput {
  /** Body key, e.g. "JUPITER" (case-insensitive on input). */
  body: string;
  /** Sidereal longitude in degrees, [0, 360). */
  longitude: number;
  retrograde?: boolean;
}

export interface SceneExportInput {
  planets: ScenePlanetInput[];
  /** Ascendant (lagna) sidereal longitude in degrees. */
  ascendantLongitude: number;
}

export interface SceneGeometry {
  uuid: string;
  type: 'BoxGeometry' | 'BufferGeometry';
  data?: {
    attributes: {
      position: { itemSize: number; type: 'Float32Array'; array: number[] };
    };
  };
  width?: number;
  height?: number;
  depth?: number;
}

export interface SceneMaterial {
  uuid: string;
  type: 'MeshStandardMaterial';
  color: number;
  metalness?: number;
  roughness?: number;
  transparent?: boolean;
  opacity?: number;
}

export interface SceneNode {
  uuid: string;
  name: string;
  type: 'Scene' | 'Group' | 'Mesh';
  matrix: number[];
  userData?: Record<string, unknown>;
  geometry?: string;
  material?: string;
  children?: SceneNode[];
}

export interface ExportedScene {
  metadata: { version: number; type: 'Object'; generator: string };
  geometries: SceneGeometry[];
  materials: SceneMaterial[];
  object: SceneNode;
}

// ── Helpers (exported for tests and callers) ───────────────────────────────

/** Scene angle (deg, [0,360)) for a longitude given the ascendant. */
export function sceneAngleFor(longitude: number, ascendantLongitude: number): number {
  return (((longitude - ascendantLongitude + 90) % 360) + 360) % 360;
}

/** House number (1..12) of a sign given the ascendant's sign. */
export function houseForSign(sign: string, ascendantSign: string): number {
  const p = SIGN_ORDER.indexOf(sign.toUpperCase() as (typeof SIGN_ORDER)[number]);
  const l = SIGN_ORDER.indexOf(ascendantSign.toUpperCase() as (typeof SIGN_ORDER)[number]);
  if (p < 0 || l < 0) return 0;
  return (((p - l) % 12) + 12) % 12 + 1;
}

/** Column-major 4x4 translation matrix (three.js layout). */
function translationMatrix(x: number, y: number, z: number): number[] {
  return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1];
}

/** 36-entry box position array (12 triangles, flat normals omitted). */
function boxPositions(w: number, h: number, d: number): number[] {
  const x = w / 2, y = h / 2, z = d / 2;
  const v = [
    [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z], // front (+z)
    [x, -y, z], [x, -y, -z], [x, y, -z], [x, y, z], // right (+x)
    [x, -y, -z], [-x, -y, -z], [-x, y, -z], [x, y, -z], // back (-z)
    [-x, -y, -z], [-x, -y, z], [-x, y, z], [-x, y, -z], // left (-x)
    [-x, y, z], [x, y, z], [x, y, -z], [-x, y, -z], // top (+y)
    [-x, -y, -z], [x, -y, -z], [x, -y, z], [-x, -y, z], // bottom (-y)
  ];
  const faces = [
    [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
    [8, 9, 10], [8, 10, 11], [12, 13, 14], [12, 14, 15],
    [16, 17, 18], [16, 18, 19], [20, 21, 22], [20, 22, 23],
  ];
  const out: number[] = [];
  for (const [a, b, c] of faces) {
    out.push(...v[a], ...v[b], ...v[c]);
  }
  return out;
}

/** 24-entry octahedron position array (8 triangles). */
function octahedronPositions(r: number): number[] {
  const t = [
    [0, r, 0], [r, 0, 0], [0, 0, r],
    [0, r, 0], [0, 0, r], [-r, 0, 0],
    [0, r, 0], [-r, 0, 0], [0, 0, -r],
    [0, r, 0], [0, 0, -r], [r, 0, 0],
    [0, -r, 0], [0, 0, r], [r, 0, 0],
    [0, -r, 0], [-r, 0, 0], [0, 0, r],
    [0, -r, 0], [0, 0, -r], [-r, 0, 0],
    [0, -r, 0], [r, 0, 0], [0, 0, -r],
  ];
  const out: number[] = [];
  for (const p of t) out.push(...p);
  return out;
}

// ── The exporter ───────────────────────────────────────────────────────────

class UuidFactory {
  private n = 0;
  next(): string {
    this.n += 1;
    const h = this.n.toString(16).padStart(12, '0');
    return `7e0f0000-0000-4000-8000-${h}`;
  }
}

export function exportScene(input: SceneExportInput): ExportedScene {
  const { planets, ascendantLongitude } = input;
  const uuid = new UuidFactory();
  const geometries: SceneGeometry[] = [];
  const materials: SceneMaterial[] = [];
  const usedGeometry = new Map<string, string>(); // geometry key -> uuid
  const usedMaterial = new Map<string, string>(); // material key -> uuid

  const geo = (
    key: string,
    make: () => SceneGeometry['data'],
    meta: Omit<SceneGeometry, 'uuid' | 'data'>,
  ): string => {
    const existing = usedGeometry.get(key);
    if (existing) return existing;
    const g: SceneGeometry = { uuid: uuid.next(), ...meta, data: make() };
    geometries.push(g);
    usedGeometry.set(key, g.uuid);
    return g.uuid;
  };

  const mat = (key: string, make: () => SceneMaterial): string => {
    const existing = usedMaterial.get(key);
    if (existing) return existing;
    const m = make();
    materials.push(m);
    usedMaterial.set(key, m.uuid);
    return m.uuid;
  };

  const boxGeo = (w: number, h: number, d: number) =>
    geo(`box:${w}:${h}:${d}`, () => ({
      attributes: { position: { itemSize: 3, type: 'Float32Array' as const, array: boxPositions(w, h, d) } },
    }), { type: 'BufferGeometry' });

  const orbGeo = (r: number) =>
    geo(`orb:${r}`, () => ({
      attributes: { position: { itemSize: 3, type: 'Float32Array' as const, array: octahedronPositions(r) } },
    }), { type: 'BufferGeometry' });

  const stdMat = (color: number, keyExtra = '') =>
    mat(`std:${color}${keyExtra}`, () => ({
      uuid: uuid.next(),
      type: 'MeshStandardMaterial' as const,
      color,
      metalness: 0.1,
      roughness: 0.6,
    }));

  const place = (radius: number, angleDeg: number): { matrix: number[]; x: number; z: number } => {
    const a = (angleDeg * Math.PI) / 180;
    const x = radius * Math.cos(a);
    const z = radius * Math.sin(a);
    return { matrix: translationMatrix(x, 0, z), x, z };
  };

  const signRing: SceneNode = {
    uuid: uuid.next(), name: 'SignRing', type: 'Group',
    matrix: translationMatrix(0, 0, 0),
    children: SIGN_ORDER.map((sign, i) => {
      const angle = sceneAngleFor(i * 30, ascendantLongitude);
      const { matrix } = place(RING_RADII.signRing, angle);
      return {
        uuid: uuid.next(), name: `Sign-${sign}`, type: 'Mesh' as const, matrix,
        geometry: boxGeo(2.8, 0.4, 1.2),
        material: stdMat(0xc5a880),
        userData: { kind: 'sign', sign, signIndex: i, sceneAngleDeg: angle },
      };
    }),
  };

  const nakshatraRing: SceneNode = {
    uuid: uuid.next(), name: 'NakshatraRing', type: 'Group',
    matrix: translationMatrix(0, 0, 0),
    children: NAKSHATRA_ORDER.map((nak, i) => {
      // A nakshatra spans 13°20'; center it inside its arc.
      const centerLon = i * (360 / 27) + 360 / 54;
      const angle = sceneAngleFor(centerLon, ascendantLongitude);
      const { matrix } = place(RING_RADII.nakshatraRing, angle);
      return {
        uuid: uuid.next(), name: `Nakshatra-${nak}`, type: 'Mesh' as const, matrix,
        geometry: boxGeo(1.2, 0.3, 0.7),
        material: stdMat(0x60a5fa),
        userData: { kind: 'nakshatra', nakshatra: nak, index: i, sceneAngleDeg: angle },
      };
    }),
  };

  const houseMarkers: SceneNode = {
    uuid: uuid.next(), name: 'HouseMarkers', type: 'Group',
    matrix: translationMatrix(0, 0, 0),
    children: Array.from({ length: 12 }, (_, h) => {
      // Whole-sign houses: house h occupies the sign (ascSignIdx + h - 1);
      // its marker sits at that sign's central longitude.
      const ascSignIdx = Math.floor((((ascendantLongitude % 360) + 360) % 360) / 30);
      const houseSignIdx = (ascSignIdx + h) % 12;
      const lon = houseSignIdx * 30 + 15;
      const angle = sceneAngleFor(lon, ascendantLongitude);
      const { matrix } = place(RING_RADII.houseMarkers, angle);
      return {
        uuid: uuid.next(), name: `House-${h + 1}`, type: 'Mesh' as const, matrix,
        geometry: boxGeo(0.9, 0.25, 0.9),
        material: stdMat(0x22d3ee),
        userData: { kind: 'house', house: h + 1, sceneAngleDeg: angle },
      };
    }),
  };

  const planetNodes: SceneNode[] = planets.map((p) => {
    const body = p.body.toUpperCase();
    const color = PLANET_PALETTE[body as ClassicalBody] ?? 0xe2e8f0;
    const angle = sceneAngleFor(p.longitude, ascendantLongitude);
    const { matrix } = place(RING_RADII.planetOrbit, angle);
    return {
      uuid: uuid.next(), name: `Planet-${body}`, type: 'Mesh' as const, matrix,
      geometry: orbGeo(0.6),
      material: stdMat(color),
      userData: {
        kind: 'planet',
        body,
        longitude: p.longitude,
        retrograde: p.retrograde ?? false,
        sceneAngleDeg: angle,
        color,
      },
    };
  });

  const planetsGroup: SceneNode = {
    uuid: uuid.next(), name: 'Planets', type: 'Group',
    matrix: translationMatrix(0, 0, 0),
    children: planetNodes,
  };

  const hub: SceneNode = {
    uuid: uuid.next(), name: 'Hub', type: 'Mesh',
    matrix: translationMatrix(0, 0, 0),
    geometry: orbGeo(RING_RADII.hub),
    material: stdMat(0xf59e0b),
    userData: { kind: 'hub' },
  };

  const root: SceneNode = {
    uuid: uuid.next(), name: 'JreScene', type: 'Scene',
    matrix: translationMatrix(0, 0, 0),
    children: [signRing, nakshatraRing, houseMarkers, planetsGroup, hub],
  };

  return {
    metadata: { version: 4.5, type: 'Object', generator: 'jre-threeExporter' },
    geometries,
    materials,
    object: root,
  };
}
