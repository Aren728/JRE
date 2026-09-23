import { renderHook, act } from '@testing-library/react';
import { useSharedBody } from '@/lib/useSharedBody';

describe('useSharedBody', () => {
  test('starts empty', () => {
    const { result } = renderHook(() => useSharedBody());
    expect(result.current.sharedBody).toEqual({ body: null, source: null });
  });

  test('setSharedBody records body and source', () => {
    const { result } = renderHook(() => useSharedBody());
    act(() => result.current.setSharedBody('JUPITER', 'YOGA'));
    expect(result.current.sharedBody).toEqual({ body: 'JUPITER', source: 'YOGA' });
    act(() => result.current.setSharedBody('sun', 'SCENE'));
    expect(result.current.sharedBody).toEqual({ body: 'SUN', source: 'SCENE' });
  });

  test('setSharedBody(null) clears body and source', () => {
    const { result } = renderHook(() => useSharedBody());
    act(() => result.current.setSharedBody('MARS', 'DASHA'));
    act(() => result.current.setSharedBody(null, 'SCENE'));
    expect(result.current.sharedBody).toEqual({ body: null, source: null });
  });

  test('clearSharedBody resets the channel', () => {
    const { result } = renderHook(() => useSharedBody());
    act(() => result.current.setSharedBody('VENUS', 'YOGA'));
    act(() => result.current.clearSharedBody());
    expect(result.current.sharedBody).toEqual({ body: null, source: null });
  });

  test('source transitions between surfaces are visible', () => {
    const { result } = renderHook(() => useSharedBody());
    act(() => result.current.setSharedBody('SATURN', 'DASHA'));
    expect(result.current.sharedBody.source).toBe('DASHA');
    act(() => result.current.setSharedBody('SATURN', 'SCENE'));
    expect(result.current.sharedBody.source).toBe('SCENE');
  });
});
