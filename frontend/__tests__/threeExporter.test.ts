import {
  exportScene,
  sceneAngleFor,
  houseForSign,
  CLASSICAL_PLANET_BODIES,
  PLANET_PALETTE,
  RING_RADII,
  type ExportedScene,
} from '@/lib/threeExporter';

function signLon(signIndex: number, degree: number): number {
  return (signIndex * 30 + degree) % 360;
}

describe('threeExporter — helpers', () => {
  test('sceneAngleFor pins the ascendant to +Z (90)', () => {
    expect(sceneAngleFor(137.0, 137.0)).toBe(90);
    expect(sceneAngleFor(137.0, 47.0)).toBe(180);
    expect(sceneAngleFor(47.0, 137.0)).toBe(0);
  });

  test('sceneAngleFor wraps negatives into [0, 360)', () => {
    expect(sceneAngleFor(10.0, 20.0)).toBe(80);
    expect(sceneAngleFor(0.0, 181.0)).toBe(269);
  });

  test('houseForSign follows the whole-sign formula', () => {
    expect(houseForSign('MESHA', 'MESHA')).toBe(1);
    expect(houseForSign('KANYA', 'MESHA')).toBe(6);
    expect(houseForSign('MEENA', 'MESHA')).toBe(12);
    expect(houseForSign('VRISHABHA', 'KANYA')).toBe(9);
    expect(houseForSign('unknown', 'MESHA')).toBe(0);
  });

  test('palette colors are unique per body', () => {
    const colors = CLASSICAL_PLANET_BODIES.map((b) => PLANET_PALETTE[b]);
    expect(new Set(colors).size).toBe(CLASSICAL_PLANET_BODIES.length);
  });
});

describe('threeExporter — exportScene', () => {
  const asc = signLon(4, 12.5); // SIMHA rising
  const input = {
    planets: [
      { body: 'SUN', longitude: signLon(4, 12.5) }, // conjunct lagna
      { body: 'MOON', longitude: signLon(9, 3.0) },
      { body: 'MARS', longitude: signLon(0, 27.75), retrograde: true },
    ],
    ascendantLongitude: asc,
  };

  let scene: ExportedScene;
  beforeAll(() => {
    scene = exportScene(input);
  });

  test('emits ObjectLoader-compatible metadata', () => {
    expect(scene.metadata.type).toBe('Object');
    expect(scene.metadata.version).toBeGreaterThan(4);
  });

  test('root is a Scene with the five top-level groups', () => {
    expect(scene.object.type).toBe('Scene');
    expect(scene.object.name).toBe('JreScene');
    const names = (scene.object.children ?? []).map((c) => c.name);
    expect(names).toEqual([
      'SignRing',
      'NakshatraRing',
      'HouseMarkers',
      'Planets',
      'Hub',
    ]);
    expect(scene.object.matrix).toHaveLength(16);
  });

  test('sign ring: 12 nodes at sign-start longitudes; lagna degree pins to +Z', () => {
    const ring = scene.object.children![0].children!;
    expect(ring).toHaveLength(12);
    const lagnaSign = ring[4]; // index 4 = SIMHA (starts at its own longitude)
    expect(lagnaSign.name).toBe('Sign-SIMHA');
    // Sign markers sit at sign START longitudes (SIMHA starts at 120°);
    // the exact lagna degree (132.5°) is what maps to +Z (90°).
    expect(lagnaSign.userData?.sceneAngleDeg).toBeCloseTo(77.5, 6);
    expect(ring[5].userData?.sceneAngleDeg).toBeCloseTo(107.5, 6);
    expect(ring[3].userData?.sceneAngleDeg).toBe(47.5);
  });

  test('nakshatra ring: 27 nodes on the outer radius', () => {
    const ring = scene.object.children![1].children!;
    expect(ring).toHaveLength(27);
    expect(ring[0].name).toBe('Nakshatra-ASHWINI');
    expect(RING_RADII.nakshatraRing).toBeGreaterThan(RING_RADII.signRing);
  });

  test('house markers: 12 nodes, whole-sign centers, house 1 spans the lagna degree', () => {
    const houses = scene.object.children![2].children!;
    expect(houses).toHaveLength(12);
    expect(houses[0].userData?.house).toBe(1);
    // House 1 center (SIMHA midpoint 135°) sits just past the lagna degree.
    expect(houses[0].userData?.sceneAngleDeg).toBeCloseTo(92.5, 6);
  });

  test('planet meshes carry metadata and palette colors', () => {
    const planets = scene.object.children![3].children!;
    expect(planets).toHaveLength(3);
    const sun = planets.find((n) => n.name === 'Planet-SUN');
    expect(sun).toBeDefined();
    expect(sun!.userData?.longitude).toBeCloseTo(132.5, 6);
    expect(sun!.userData?.sceneAngleDeg).toBeCloseTo(90, 6);
    const mars = planets.find((n) => n.name === 'Planet-MARS');
    expect(mars!.userData?.retrograde).toBe(true);
  });

  test('planet names pair with their body metadata', () => {
    const planets = scene.object.children![3].children!;
    for (const node of planets) {
      expect(node.name.startsWith('Planet-')).toBe(true);
      expect(node.name).toBe(`Planet-${String(node.userData?.body)}`);
    }
  });

  test('geometries are deduped to one per distinct shape', () => {
    // sign box + house box + nakshatra box + planet orb (r=0.6)
    // + hub orb (r=0.8) = 5 distinct shapes.
    expect(scene.geometries).toHaveLength(5);
    const uuids = scene.geometries.map((g) => g.uuid);
    expect(new Set(uuids).size).toBe(5);
  });

  test('materials are shared when colors repeat', () => {
    // Sign/house/nakshatra rings share one material color; planets add
    // their own per-body colors (3 distinct here: SUN, MOON, MARS).
    const colors = scene.materials.map((m) => m.color);
    expect(new Set(colors).size).toBe(colors.length);
    expect(colors.length).toBeGreaterThanOrEqual(4);
  });

  test('UUIDs are deterministic: byte-identical JSON across runs', () => {
    const a = exportScene(input);
    const b = exportScene(input);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  test('UUIDs are unique within one scene', () => {
    const uuids: string[] = [
      ...scene.geometries.map((g) => g.uuid),
      ...scene.materials.map((m) => m.uuid),
    ];
    const walk = (node: { uuid: string; children?: unknown[] }): void => {
      uuids.push(node.uuid);
      for (const child of node.children ?? []) {
        walk(child as { uuid: string; children?: unknown[] });
      }
    };
    walk(scene.object);
    expect(new Set(uuids).size).toBe(uuids.length);
  });
});
