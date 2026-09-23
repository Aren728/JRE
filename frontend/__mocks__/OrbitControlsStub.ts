/**
 * Jest-only stub for three's ESM-only OrbitControls.
 *
 * next/jest prepends /node_modules/ to transformIgnorePatterns, so ESM-only
 * node_modules files can never be transformed — tests map this stub over
 * the real module (jest.config.js moduleNameMapper).
 */

export class OrbitControls {
  enableDamping = false;
  dampingFactor = 1;
  minDistance = 0;
  maxDistance = Infinity;
  target = { x: 0, y: 0, z: 0 };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(_camera: unknown, _domElement: unknown) {}

  update(): void {}
  dispose(): void {}
}
