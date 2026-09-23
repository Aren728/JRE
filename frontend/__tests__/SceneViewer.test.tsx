import { render, screen, fireEvent } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import SceneViewer from '@/components/scene/SceneViewer';
import { useSharedBody } from '@/lib/useSharedBody';
import type { EvaluationResponse } from '@/lib/api';

// ── Minimal `three` mock (WebGL is unavailable in jsdom) ────────────────────
jest.mock('three', () => {
  class Color {
    constructor(public hex: number | string) {}
  }
  class Vector2 {
    x = 0;
    y = 0;
    set(x: number, y: number) {
      this.x = x;
      this.y = y;
      return this;
    }
  }
  class Vector3 {
    x = 0;
    y = 0;
    z = 0;
    set(x: number, y: number, z: number) {
      this.x = x;
      this.y = y;
      this.z = z;
      return this;
    }
  }
  class Object3D {
    name = '';
    children: unknown[] = [];
    add(..._children: unknown[]) {
      void _children;
    }
    remove(..._objects: unknown[]) {
      void _objects;
    }
    traverse(cb: (o: unknown) => void) {
      cb(this);
    }
  }
  class Group extends Object3D {}
  class Mesh extends Object3D {
    isMesh = true;
    geometry: unknown = null;
    material: unknown = null;
  }
  class Scene extends Object3D {}
  class PerspectiveCamera {
    aspect = 1;
    position = { set() {} };
    updateProjectionMatrix() {}
  }
  class WebGLRenderer {
    domElement = document.createElement('div');
    setClearColor() {}
    setPixelRatio() {}
    setSize() {}
    render() {}
    dispose() {}
  }
  class ObjectLoader {
    parse(_json?: unknown) {
      void _json;
      const root = new Group();
      root.name = 'JreScene';
      return root;
    }
  }
  class Raycaster {
    setFromCamera() {}
    intersectObjects(): { object: { name: string } }[] {
      const hits = (globalThis as { __jreRayHits?: { object: { name: string } }[] }).__jreRayHits ?? [];
      return hits;
    }
  }
  class AmbientLight extends Object3D {}
  class DirectionalLight extends Object3D {
    position = { set() {} };
  }
  return {
    Color,
    Vector2,
    Vector3,
    Object3D,
    Group,
    Mesh,
    Scene,
    PerspectiveCamera,
    WebGLRenderer,
    ObjectLoader,
    Raycaster,
    AmbientLight,
    DirectionalLight,
  };
});

const data = {
  lagna: 'SIMHA',
  planet_details: {
    SUN: { sign: 'SIMHA', element: 'fire', modality: 'fixed', dignity: 'neutral', degree_in_sign: 12.5 },
    MARS: { sign: 'MESHA', element: 'fire', modality: 'movable', dignity: 'own', degree_in_sign: 27.75 },
  },
} as unknown as EvaluationResponse;

beforeEach(() => {
  delete (globalThis as { __jreRayHits?: { object: { name: string } }[] }).__jreRayHits;
});

// jsdom has no WebGL; stub a truthy 2D context so detectWebgl() passes.
// Safe because `three` itself is fully mocked above.
function enableWebglStub(): jest.SpyInstance {
  return jest
    .spyOn(HTMLCanvasElement.prototype, 'getContext')
    .mockReturnValue({} as CanvasRenderingContext2D);
}

describe('SceneViewer', () => {
  test('renders the fallback card when WebGL is unavailable', () => {
    const original = document.createElement('canvas').getContext;
    const getContextSpy = jest
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(null);
    render(<SceneViewer data={data} />);
    expect(screen.getByTestId('scene-fallback')).toBeInTheDocument();
    expect(screen.getByText(/WebGL is disabled/)).toBeInTheDocument();
    getContextSpy.mockRestore();
    void original;
  });

  test('renders the viewer container and ingests the exported scene', () => {
    const ctxStub = enableWebglStub();
    render(<SceneViewer data={data} />);
    expect(screen.getByTestId('scene-viewer')).toBeInTheDocument();
    // The mocked ObjectLoader.parse built a root named JreScene; the viewer
    // appended the mocked renderer's dom element as its last child.
    const viewer = screen.getByTestId('scene-viewer');
    expect(viewer.lastElementChild).not.toBeNull();
    expect(screen.getByText(/drag to orbit/)).toBeInTheDocument();
    ctxStub.mockRestore();
  });

  test('HUD mirrors an externally focused body with an EXTERNAL badge', () => {
    const ctxStub = enableWebglStub();
    const { result } = renderHook(() => useSharedBody());
    const { rerender } = render(
      <SceneViewer data={data} sharedBodyChannel={result.current} />,
    );
    expect(screen.queryByTestId('scene-hud')).not.toBeInTheDocument();

    act(() => result.current.setSharedBody('MARS', 'YOGA'));
    rerender(<SceneViewer data={data} sharedBodyChannel={result.current} />);

    const hud = screen.getByTestId('scene-hud');
    expect(hud).toHaveTextContent('MARS');
    expect(hud).toHaveTextContent('EXTERNAL');
    ctxStub.mockRestore();
  });

  test('clicking a planet focuses it with the SCENE source', () => {
    const ctxStub = enableWebglStub();
    const onSelectionChange = jest.fn();
    const { container } = render(
      <SceneViewer data={data} onSelectionChange={onSelectionChange} />,
    );
    // Ray hits are controlled via the mock's global hook.
    (globalThis as { __jreRayHits?: { object: { name: string } }[] }).__jreRayHits = [
      { object: { name: 'Planet-MARS' } },
    ];
    const viewer = container.querySelector('[data-testid="scene-viewer"]')!;
    const canvas = viewer.lastElementChild as HTMLElement;
    fireEvent.pointerMove(canvas);
    fireEvent.click(canvas);

    expect(onSelectionChange).toHaveBeenCalledWith('MARS');
    const hud = screen.getByTestId('scene-hud');
    expect(hud).toHaveTextContent('MARS');
    expect(hud).toHaveTextContent('SCENE');
    ctxStub.mockRestore();
  });
});
