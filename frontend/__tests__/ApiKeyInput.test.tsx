import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import '@testing-library/jest-dom';
import ApiKeyInput, { useApiKey } from '@/components/ApiKeyInput';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('ApiKeyInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (initialKey = 'jre-beta-key-alpha') => {
    localStorageMock.getItem.mockReturnValue(initialKey);
    render(<ApiKeyInput value={initialKey} onChange={jest.fn()} />);
  };

  test('renders default key on initial mount', () => {
    renderComponent();
    const input = screen.getByPlaceholderText('jre-beta-key-alpha');
    expect(input).toHaveValue('jre-beta-key-alpha');
  });

  test('renders with custom value prop when provided', () => {
    render(<ApiKeyInput value="custom-key-123" onChange={jest.fn()} />);
    const input = screen.getByPlaceholderText('jre-beta-key-alpha');
    expect(input).toHaveValue('custom-key-123');
  });

  test('calls onChange when user types in input', () => {
    const onChange = jest.fn();
    render(<ApiKeyInput value="test-key" onChange={onChange} />);
    const input = screen.getByPlaceholderText('jre-beta-key-alpha');

    fireEvent.change(input, { target: { value: 'new-key' } });

    expect(onChange).toHaveBeenCalledWith('new-key');
  });

  test('eye icon toggles input type from password to text', () => {
    renderComponent();
    const toggleBtn = screen.getByTitle('Show key');
    const input = screen.getByPlaceholderText('jre-beta-key-alpha');

    expect(input).toHaveAttribute('type', 'password');

    fireEvent.click(toggleBtn);

    expect(input).toHaveAttribute('type', 'text');
    expect(toggleBtn.title).toBe('Hide key');
  });

  test('eye icon toggles input type from text back to password', () => {
    renderComponent();
    const toggleBtn = screen.getByTitle('Show key');
    const input = screen.getByPlaceholderText('jre-beta-key-alpha');

    // First toggle to show
    fireEvent.click(toggleBtn);
    expect(input).toHaveAttribute('type', 'text');

    // Second toggle to hide
    fireEvent.click(toggleBtn);
    expect(input).toHaveAttribute('type', 'password');
    expect(toggleBtn.title).toBe('Show key');
  });

  test('displays storage notice below input', () => {
    renderComponent();
    expect(screen.getByText(/Stored in your browser localStorage/i)).toBeInTheDocument();
  });

  test('renders label with key icon', () => {
    renderComponent();
    expect(screen.getByText('API Key')).toBeInTheDocument();
    // The key icon is an SVG with aria-hidden, so we check the label text contains the icon context
    const label = screen.getByText('API Key');
    expect(label).toBeInTheDocument();
  });
});

describe('useApiKey hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns default key when localStorage is empty', () => {
    localStorageMock.getItem.mockReturnValue(null);

    const { result } = renderHook(() => useApiKey());

    expect(result.current.apiKey).toBe('jre-beta-key-alpha');
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'jre_api_key',
      'jre-beta-key-alpha'
    );
  });

  test('returns stored key from localStorage when available', () => {
    const storedKey = 'my-stored-key-123';
    localStorageMock.getItem.mockReturnValue(storedKey);

    const { result } = renderHook(() => useApiKey());

    expect(result.current.apiKey).toBe(storedKey);
    expect(localStorageMock.setItem).not.toHaveBeenCalled();
  });

  test('setApiKey updates state and localStorage', () => {
    localStorageMock.getItem.mockReturnValue(null);

    const { result } = renderHook(() => useApiKey());

    act(() => {
      result.current.setApiKey('updated-key-456');
    });

    expect(result.current.apiKey).toBe('updated-key-456');
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'jre_api_key',
      'updated-key-456'
    );
  });

  test('setApiKey persists changes across hook calls', () => {
    localStorageMock.getItem.mockReturnValue('initial-key');

    const { result } = renderHook(() => useApiKey());

    expect(result.current.apiKey).toBe('initial-key');

    act(() => {
      result.current.setApiKey('changed-key');
    });

    expect(result.current.apiKey).toBe('changed-key');
  });
});
