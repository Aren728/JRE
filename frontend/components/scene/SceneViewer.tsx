'use client';

/**
 * SceneViewer — Phase 4 3D celestial scene viewport.
 *
 * Ingests the deterministic JSON from `lib/threeExporter.ts` via
 * `THREE.ObjectLoader.parse()`, renders it with OrbitControls (damped,
 * resize-aware), raycasts `Planet-*` meshes for hover/select, and surfaces
 * the focused body in a metadata HUD. Selection syncs bidirectionally
 * through `lib/useSharedBody.ts` — a scene click focuses the body
 * everywhere; an external focus (yoga card / dasha node) mirrors into the
 * HUD with an EXTERNAL badge.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  exportScene,
  sceneAngleFor,
  SIGN_ORDER,
  type SceneExportInput,
} from '@/lib/threeExporter';
import { useSharedBody, type SharedBodySource } from '@/lib/useSharedBody';
import type { EvaluationResponse } from '@/lib/api';

const BACKGROUND_HEX = '#050510';
const CAMERA_START: [number, number, number] = [0, 14, 18];
const DAMPING = 0.08;

export interface SceneViewerProps {
  /** The full evaluation payload (planets + lagna). */
  data: EvaluationResponse;
  /** Optional parent-owned shared-body channel (defaults to an internal one). */
  sharedBodyChannel?: ReturnType<typeof useSharedBody>;
  /** Fired when the user selects a body in the scene. */
  onSelectionChange?: (body: string | null) => void;
  className?: string;
}

interface HudBody {
  body: string;
  longitude: number;
  retrograde: boolean;
  sceneAngleDeg: number;
  source: SharedBodySource | null;
}

function detectWebgl(): boolean {
  if (typeof document === 'undefined') return false;
  try {
    const canvas = document.createElement('canvas');
    return Boolean(
      canvas.getContext('webgl2') ||
        canvas.getContext('webgl') ||
        canvas.getContext('experimental-webgl'),
    );
  } catch {
    return false;
  }
}

function disposeGroup(root: THREE.Object3D): void {
  root.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.isMesh) {
      mesh.geometry?.dispose();
      const material = mesh.material;
      if (Array.isArray(material)) material.forEach((m) => m.dispose());
      else material?.dispose();
    }
  });
}

export default function SceneViewer({
  data,
  sharedBodyChannel,
  onSelectionChange,
  className = '',
}: SceneViewerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [webglAvailable] = useState<boolean>(detectWebgl);
  const [hovered, setHovered] = useState<string | null>(null);

  // Own the channel when the parent didn't provide one.
  const ownChannel = useSharedBody();
  const channel = sharedBodyChannel ?? ownChannel;
  const { sharedBody, setSharedBody } = channel;

  const onSelectionRef = useRef(onSelectionChange);
  useEffect(() => {
    onSelectionRef.current = onSelectionChange;
  }, [onSelectionChange]);

  // ── Build the scene input from the evaluation payload ─────────────────
  const sceneInput: SceneExportInput = useMemo(() => {
    const planets = Object.entries(data.planet_details ?? {}).map(([body, detail]) => {
      const signIdx = SIGN_ORDER.indexOf((detail.sign ?? '').toUpperCase() as (typeof SIGN_ORDER)[number]);
      const lon = (((Math.max(signIdx, 0)) * 30 + (detail.degree_in_sign ?? 0)) % 360 + 360) % 360;
      return { body, longitude: lon, retrograde: false };
    });
    // Ascendant: exact longitude when present, else the lagna sign's midpoint.
    const lagnaLon = (data as { lagna_longitude?: number }).lagna_longitude;
    const lagnaIdx = SIGN_ORDER.indexOf((data.lagna ?? '').toUpperCase() as (typeof SIGN_ORDER)[number]);
    const ascendantLongitude =
      typeof lagnaLon === 'number'
        ? lagnaLon
        : lagnaIdx >= 0
          ? lagnaIdx * 30 + 15
          : 0;
    return { planets, ascendantLongitude };
  }, [data]);

  // Deterministic scene JSON (memoized per chart).
  const sceneJson = useMemo(() => exportScene(sceneInput), [sceneInput]);

  // ── HUD body derived from the shared selection ────────────────────────
  const hudBody: HudBody | null = useMemo(() => {
    if (!sharedBody.body) return null;
    const planet = sceneInput.planets.find(
      (p) => p.body.toUpperCase() === sharedBody.body,
    );
    if (!planet) return null;
    return {
      body: planet.body.toUpperCase(),
      longitude: planet.longitude,
      retrograde: planet.retrograde ?? false,
      sceneAngleDeg: sceneAngleFor(planet.longitude, sceneInput.ascendantLongitude),
      source: sharedBody.source,
    };
  }, [sharedBody, sceneInput]);

  // ── three.js lifecycle ─────────────────────────────────────────────────
  useEffect(() => {
    if (!webglAvailable) return;
    const mount = mountRef.current;
    if (!mount) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setClearColor(new THREE.Color(BACKGROUND_HEX), 1);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.display = 'block';
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
    camera.position.set(...CAMERA_START);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = DAMPING;
    controls.minDistance = 8;
    controls.maxDistance = 60;

    const syncSize = () => {
      const w = mount.clientWidth || 1;
      const h = mount.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    syncSize();
    const resizeObserver = new ResizeObserver(syncSize);
    resizeObserver.observe(mount);

    const loader = new THREE.ObjectLoader();
    let root: THREE.Object3D | null = null;
    const ingest = () => {
      if (root) {
        scene.remove(root);
        disposeGroup(root);
      }
      root = loader.parse(sceneJson as unknown as Record<string, unknown>);
      scene.add(root);
    };
    ingest();

    // ── Raycasting against Planet-* meshes ──────────────────────────────
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let pointerInside = false;

    const planetMeshes = (): THREE.Mesh[] => {
      if (!root) return [];
      const found: THREE.Mesh[] = [];
      root.traverse((child) => {
        if (child.name.startsWith('Planet-')) found.push(child as THREE.Mesh);
      });
      return found;
    };

    const updatePointer = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    };

    const onPointerMove = (event: PointerEvent) => {
      pointerInside = true;
      updatePointer(event);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(planetMeshes(), false);
      setHovered(hits.length > 0 ? hits[0].object.name.replace(/^Planet-/, '') : null);
    };

    const onClick = (event: PointerEvent) => {
      if (!pointerInside) return;
      updatePointer(event);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(planetMeshes(), false);
      if (hits.length === 0) return;
      const body = hits[0].object.name.replace(/^Planet-/, '');
      setSharedBody(body, 'SCENE');
      onSelectionRef.current?.(body);
    };

    renderer.domElement.addEventListener('pointermove', onPointerMove);
    renderer.domElement.addEventListener('click', onClick);

    // ── Lights + render loop ────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
    keyLight.position.set(10, 18, 8);
    scene.add(keyLight);

    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('pointermove', onPointerMove);
      renderer.domElement.removeEventListener('click', onClick);
      controls.dispose();
      if (root) {
        scene.remove(root);
        disposeGroup(root);
      }
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [sceneJson, webglAvailable, setSharedBody]);

  // ── Fallback card when WebGL is unavailable ────────────────────────────
  if (!webglAvailable) {
    return (
      <div
        className={`rounded-2xl p-6 text-center ${className}`}
        data-testid="scene-fallback"
        style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
      >
        <p className="text-sm" style={{ color: 'var(--cosmic-muted)' }}>
          3D scene unavailable — WebGL is disabled in this browser.
        </p>
        <div className="mt-3 space-y-1 text-xs" style={{ color: 'var(--cosmic-muted)' }}>
          {sceneInput.planets.map((p) => (
            <div key={p.body} className="flex justify-between max-w-xs mx-auto">
              <span>{p.body}</span>
              <span>{p.longitude.toFixed(2)}°</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div
      ref={mountRef}
      className={`relative rounded-2xl overflow-hidden ${className}`}
      style={{
        background: BACKGROUND_HEX,
        border: '1px solid var(--glass-border)',
        minHeight: 420,
      }}
      data-testid="scene-viewer"
    >
      {hudBody && (
        <div
          className="absolute top-3 right-3 z-10 rounded-xl px-4 py-3 text-xs"
          style={{
            background: 'rgba(5,5,16,0.85)',
            border: '1px solid var(--glass-border)',
            minWidth: 200,
          }}
          data-testid="scene-hud"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold" style={{ color: 'var(--cosmic-gold)' }}>
              {hudBody.body}
            </span>
            <span
              className="px-1.5 rounded"
              style={{ background: 'rgba(34,211,238,0.15)', color: '#22d3ee' }}
            >
              {hudBody.source === 'SCENE' ? 'SCENE' : 'EXTERNAL'}
              {hovered && hovered !== hudBody.body ? ' · hover' : ''}
            </span>
          </div>
          <div style={{ color: 'var(--cosmic-text)' }}>
            λ {hudBody.longitude.toFixed(2)}° sidereal
          </div>
          <div style={{ color: 'var(--cosmic-muted)' }}>
            scene angle {hudBody.sceneAngleDeg.toFixed(1)}°
          </div>
          <div style={{ color: 'var(--cosmic-muted)' }}>
            retrograde: {hudBody.retrograde ? 'yes' : 'no'}
          </div>
        </div>
      )}

      <div
        className="absolute bottom-3 left-3 z-10 text-[10px]"
        style={{ color: 'rgba(255,255,255,0.4)' }}
      >
        drag to orbit · scroll to zoom · click a planet to focus
      </div>
    </div>
  );
}
