'use client';

/**
 * useSharedBody — Phase 4 bidirectional selection sync.
 *
 * The 3D scene, YogaInspector, and DashaTreeViewer share one focused body.
 * `source` records who set the current value ('SCENE' | 'YOGA' | 'DASHA')
 * so the scene can ignore echo-updates of its own clicks while still
 * mirroring external selections into its HUD.
 */

import { useCallback, useState } from 'react';

export type SharedBodySource = 'SCENE' | 'YOGA' | 'DASHA';

export interface SharedBodyState {
  /** Focused body key, e.g. "JUPITER", or null when nothing is focused. */
  body: string | null;
  /** Which surface set it last. */
  source: SharedBodySource | null;
}

export interface UseSharedBodyResult {
  sharedBody: SharedBodyState;
  /** Set the focused body from any surface. */
  setSharedBody: (body: string | null, source: SharedBodySource) => void;
  /** Clear focus entirely (e.g. on new analysis). */
  clearSharedBody: () => void;
}

export function useSharedBody(): UseSharedBodyResult {
  const [sharedBody, setSharedBodyState] = useState<SharedBodyState>({
    body: null,
    source: null,
  });

  const setSharedBody = useCallback((body: string | null, source: SharedBodySource) => {
    setSharedBodyState(
      body
        ? { body: body.toUpperCase(), source }
        : { body: null, source: null },
    );
  }, []);

  const clearSharedBody = useCallback(() => {
    setSharedBodyState({ body: null, source: null });
  }, []);

  return { sharedBody, setSharedBody, clearSharedBody };
}
