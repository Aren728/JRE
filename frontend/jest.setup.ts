import '@testing-library/jest-dom';

// Deterministic fetch mock for jsdom (jsdom does not provide fetch)
const fetchMockFn = jest.fn();
Object.defineProperty(globalThis, 'fetch', { value: fetchMockFn, writable: true });

// ResizeObserver shim (jsdom does not implement it; SceneViewer uses it)
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
type ResizeObserverCtor = new (cb: ResizeObserverCallback) => ResizeObserver;
const g = globalThis as unknown as { ResizeObserver?: ResizeObserverCtor };
if (!g.ResizeObserver) {
  g.ResizeObserver = ResizeObserverStub as unknown as ResizeObserverCtor;
}

// requestAnimationFrame fallback (older jsdom)
const gRaf = globalThis as unknown as {
  requestAnimationFrame?: (cb: (t: number) => void) => number;
};
if (!gRaf.requestAnimationFrame) {
  gRaf.requestAnimationFrame = (cb: (t: number) => void) =>
    setTimeout(() => cb(Date.now()), 16) as unknown as number;
}
