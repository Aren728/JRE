import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChartInputForm } from '../components/ChartInputForm';

describe('ChartInputForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders Tab A with analytical overview and core inputs', () => {
    const { container } = render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    // Tab A: Analytical Overview
    expect(screen.getByText(/Analytical Overview/i)).toBeInTheDocument();

    // Check inputs exist by querying the container
    const inputs = container.querySelectorAll('input');
    expect(inputs.length).toBeGreaterThan(0);

    // Check for date, time, and other input types
    const dateInput = container.querySelector('input[type="date"]');
    expect(dateInput).toBeInTheDocument();

    const timeInput = container.querySelector('input[type="time"]');
    expect(timeInput).toBeInTheDocument();
  });

  test('renders Tab B with ephemeris settings', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    // Tab B: Ephemeris & Bhava Settings
    expect(screen.getByText(/Ephemeris & Bhava Settings/i)).toBeInTheDocument();
    expect(screen.getByText(/Ayanamsha Model/i)).toBeInTheDocument();
    expect(screen.getByText(/Node Calculation/i)).toBeInTheDocument();
    expect(screen.getByText(/House System/i)).toBeInTheDocument();
    expect(screen.getByText(/Transit Orb Tolerance/i)).toBeInTheDocument();
    expect(screen.getByText(/Shadbala Threshold/i)).toBeInTheDocument();
    expect(screen.getByText(/Divisional Chart Focus/i)).toBeInTheDocument();
    expect(screen.getByText(/Dasha Hierarchy Depth/i)).toBeInTheDocument();
  });

  test('applies preset location values when clicked', () => {
    const { container } = render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    const londonBtn = screen.getByRole('button', { name: /London/i });
    fireEvent.click(londonBtn);

    // After clicking London, the Tab A inputs should update
    // Check all inputs and map by their preceding label
    const inputs = container.querySelectorAll('input[type="number"], input[type="text"]');
    const valueMap = new Map<string, string>();
    inputs.forEach(input => {
      const labelEl = input.previousElementSibling as HTMLElement | null;
      const labelText = labelEl?.querySelector('label')?.textContent || labelEl?.textContent || '';
      if (labelText) valueMap.set(labelText.trim(), input.getAttribute('value') || '');
    });

    expect(valueMap.get('Latitude')).toBe('51.5074');
    expect(valueMap.get('Longitude')).toBe('-0.1278');
    // The timezone input is a text input
    const timezoneInput = container.querySelector('input[type="text"]');
    expect(timezoneInput?.getAttribute('value')).toBe('Europe/London');
  });

  test('submits payload with all new fields from Tab A', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    const submitBtn = screen.getByRole('button', { name: /Calculate Chart/i });
    fireEvent.click(submitBtn);

    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    const payload = mockOnSubmit.mock.calls[0][0];

    // Tab A fields
    expect(typeof payload.latitude).toBe('number');
    expect(typeof payload.longitude).toBe('number');
    expect(payload.altitude).toBe(0);
    expect(payload.utc_offset).toBe(0);
    expect(payload.ayanamsha).toBe('lahiri');
    expect(payload.node_type).toBe('mean');
    expect(payload.house_system).toBe('equal');
    expect(payload.transit_orb_tolerance).toBe(1.0);
    expect(payload.shadbala_threshold).toBe(1.0);
    expect(payload.divisional_focus).toBe('D1');
    expect(payload.dasha_depth).toBe('MD');
  });

  test('applies ephemeris settings from Tab B on submit', () => {
    render(<ChartInputForm onSubmit={mockOnSubmit} isLoading={false} />);

    // Change a Tab B setting
    const kpRadio = screen.getByLabelText(/KP/i);
    fireEvent.click(kpRadio);

    const trueNodeRadio = screen.getByLabelText(/True Node/i);
    fireEvent.click(trueNodeRadio);

    const d9Radio = screen.getByLabelText(/D9/i);
    fireEvent.click(d9Radio);

    const submitBtn = screen.getByRole('button', { name: /Apply Ephemeris Settings/i });
    fireEvent.click(submitBtn);

    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    const payload = mockOnSubmit.mock.calls[0][0];

    expect(payload.ayanamsha).toBe('kp');
    expect(payload.node_type).toBe('true');
    expect(payload.divisional_focus).toBe('D9');
  });
});
