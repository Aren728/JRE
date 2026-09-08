import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChartInputForm } from '../components/ChartInputForm';

describe('ChartInputForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders form title and core inputs', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    expect(screen.getByText(/Chart Parameters/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Date \(YYYY-MM-DD\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Time \(HH:MM:SS\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Timezone \(IANA\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Latitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Longitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Ayanamsha/i)).toBeInTheDocument();
  });

  test('applies preset location values when clicked', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    const londonBtn = screen.getByRole('button', { name: /London/i });
    fireEvent.click(londonBtn);

    expect(screen.getByLabelText(/Latitude/i)).toHaveValue(51.5074);
    expect(screen.getByLabelText(/Longitude/i)).toHaveValue(-0.1278);
    expect(screen.getByLabelText(/Timezone/i)).toHaveValue('Europe/London');
  });

  test('submits numeric latitude and longitude with ayanamsha', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    const submitBtn = screen.getByRole('button', { name: /Calculate Chart/i });
    fireEvent.click(submitBtn);

    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    const payload = mockOnSubmit.mock.calls[0][0];

    expect(typeof payload.latitude).toBe('number');
    expect(typeof payload.longitude).toBe('number');
    expect(payload.ayanamsha).toBe('lahiri');
  });
});
