import '@testing-library/jest-dom';

// Deterministic fetch mock for jsdom (jsdom does not provide fetch)
const fetchMockFn = jest.fn();
Object.defineProperty(globalThis, 'fetch', { value: fetchMockFn, writable: true });
