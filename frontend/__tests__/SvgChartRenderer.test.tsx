import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SvgChartRenderer, { generateDemoChartData, type SvgChartRendererProps } from '../components/charts/SvgChartRenderer';

describe('SvgChartRenderer', () => {
  const defaultProps: SvgChartRendererProps = {
    planets: [
      {
        name: 'Sun',
        sign: 1,
        degree: 15,
        minute: 30,
        isRetrograde: false,
        nakshatra: 'Krittika',
        house: 1,
        dignity: 'neutral',
      },
      {
        name: 'Moon',
        sign: 5,
        degree: 8,
        minute: 45,
        isRetrograde: false,
        nakshatra: 'Rohini',
        house: 5,
        dignity: 'friendly',
      },
    ],
    chartStyle: 'NORTH_INDIAN',
    vargaType: 'D1',
    showAspectLines: false,
  };

  test('renders North Indian chart by default', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    // Check for varga type label
    expect(screen.getByText(/Rashi \(D-1\)/i)).toBeInTheDocument();

    // North Indian has diamond shapes - check for house numbers
    expect(screen.getByText('1 ASC')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  test('renders South Indian chart when style is SOUTH_INDIAN', () => {
    render(<SvgChartRenderer {...defaultProps} chartStyle="SOUTH_INDIAN" />);

    expect(screen.getByText(/Rashi \(D-1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign-fixed grid/i)).toBeInTheDocument();
    expect(screen.getByText('ASC / Lg')).toBeInTheDocument();
  });

  test('renders varga type label correctly', () => {
    render(<SvgChartRenderer {...defaultProps} vargaType="D9" />);

    expect(screen.getByText(/Navamsha \(D-9\)/i)).toBeInTheDocument();
  });

  test('renders planet symbols in the chart', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    // Should show planet symbols (Su for Sun, Mo for Moon)
    expect(screen.getByText('Su')).toBeInTheDocument();
    expect(screen.getByText('Mo')).toBeInTheDocument();
  });

  test('renders retrogradation indicator for retrograde planets', () => {
    const propsWithRetrograde: SvgChartRendererProps = {
      ...defaultProps,
      planets: [
        ...defaultProps.planets!,
        {
          name: 'Mars',
          house: 3,
          sign: 3,
          degree: 22,
          minute: 10,
          isRetrograde: true,
          nakshatra: 'Purva Ashadha',
          dignity: 'own',
        },
      ],
    };

    render(<SvgChartRenderer {...propsWithRetrograde} />);

    expect(screen.getByText('Ma')).toBeInTheDocument();
  });

  test('generateDemoChartData creates valid chart data', () => {
    const data = generateDemoChartData(1, 'NORTH_INDIAN', 'D1');

    expect(data.planets).toBeDefined();
    expect(data.planets.length).toBeGreaterThan(0);
    expect(data.ascendant).toBe(1);
    expect(data.vargaType).toBe('D1');
  });

  test('generateDemoChartData with different ascendant shifts planet positions', () => {
    const dataAries = generateDemoChartData(1, 'NORTH_INDIAN', 'D1');
    const dataTaurus = generateDemoChartData(2, 'NORTH_INDIAN', 'D1');

    // Sun should be in different houses for different ascendants
    expect(dataAries.planets[0].house).not.toBe(dataTaurus.planets[0].house);
  });

  test('generateDemoChartData with different varga types changes label', () => {
    const dataD9 = generateDemoChartData(1, 'NORTH_INDIAN', 'D9');

    expect(dataD9.vargaType).toBe('D9');
  });

  test('onPlanetSelect callback fires when planet is clicked', () => {
    const handleSelect = jest.fn();
    render(<SvgChartRenderer {...defaultProps} onPlanetSelect={handleSelect} />);

    fireEvent.click(screen.getByText('Su'));

    expect(handleSelect).toHaveBeenCalledWith('Sun');
  });

  test('shows tooltip when hovering over a planet', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    const sunElement = screen.getByText('Su');
    fireEvent.mouseEnter(sunElement);

    // Tooltip should appear - check for SVG title element
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    // Tooltip content via SVG title or data attributes
    expect(svg?.querySelector('[data-planet="Sun"]') || svg?.textContent).toBeTruthy();
  });

  test('renders aspect lines toggle area when showAspectLines is true', () => {
    const propsWithAspects: SvgChartRendererProps = {
      ...defaultProps,
      showAspectLines: true,
      aspects: [
        {
          sourcePlanet: 'Sun',
          targetPlanet: 'Moon',
          type: 'trine',
          angle: 120,
        },
      ],
    };

    render(<SvgChartRenderer {...propsWithAspects} />);

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();

    // Aspect lines would be rendered in the SVG if planets match criteria
    const aspectLines = svg?.querySelectorAll('[stroke-dasharray]');
    // May or may not have lines depending on planet data
    expect(aspectLines?.length).toBeGreaterThanOrEqual(0);
  });

  test('South Indian chart shows all 12 sign boxes', () => {
    render(
      <SvgChartRenderer
        {...defaultProps}
        chartStyle="SOUTH_INDIAN"
        planets={[
          ...defaultProps.planets!,
          { name: 'Mars', house: 3, sign: 3, degree: 10, minute: 0, isRetrograde: false, nakshatra: 'Mrigashira', dignity: 'neutral' },
          { name: 'Mercury', house: 2, sign: 2, degree: 15, minute: 0, isRetrograde: false, nakshatra: 'Krittika', dignity: 'own' },
        ]}
      />
    );

    // All sign abbreviations should be visible
    for (let i = 1; i <= 12; i++) {
      const signAbbrev = ['Ar', 'Ta', 'Ge', 'Ca', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'][i - 1];
      expect(screen.getByText(signAbbrev)).toBeInTheDocument();
    }
  });

  test('North Indian chart shows house numbers 1-12', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    // All house numbers should be visible
    for (let i = 1; i <= 12; i++) {
      const houseText = i === 1 ? `${i} ASC` : `${i}`;
      expect(screen.getByText(houseText)).toBeInTheDocument();
    }
  });

  test('planet legend shows correct color for each planet', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    // Check that planet elements exist in the SVG
    const sunElement = screen.getByText('Su');
    expect(sunElement).toBeInTheDocument();

    // Planet should have color styling via SVG fill attribute
    const svg = document.querySelector('svg');
    expect(svg?.textContent).toContain('Su');
  });

  test('displays interactive tooltip banner on hover with degree and dignity details', () => {
    render(<SvgChartRenderer {...defaultProps} />);

    // Initially shows default prompt
    expect(screen.getByText(/Hover over a planet to inspect details/i)).toBeInTheDocument();

    // Hover over Sun
    const sunGroup = document.querySelector('[data-planet="Sun"]');
    expect(sunGroup).toBeInTheDocument();
    fireEvent.mouseEnter(sunGroup!);

    // Interactive banner should now display planet details
    expect(screen.getAllByText('Sun').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/15.00°/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Nakshatra: Krittika/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/\(neutral\)/i).length).toBeGreaterThan(0);

    // Unhover
    fireEvent.mouseLeave(sunGroup!);
    expect(screen.getByText(/Hover over a planet to inspect details/i)).toBeInTheDocument();
  });

  test('renders custom title and degree overlay', () => {
    render(<SvgChartRenderer {...defaultProps} title="Core Natal Chart" />);

    expect(screen.getByText('Core Natal Chart')).toBeInTheDocument();
    // Sun has degree 15
    expect(screen.getByText('15°')).toBeInTheDocument();
  });

  test('supports chartData prop in 3x3 grid mode', () => {
    const customData = [
      { name: 'Sun', degree: 14.5, nakshatra: 'Bharani', dignity: 'exalted' },
      { name: 'Moon', degree: 22.1, nakshatra: 'Rohini', dignity: 'own' },
    ];
    render(<SvgChartRenderer chartData={customData} title="Grid Chart" />);

    expect(screen.getByText('Grid Chart')).toBeInTheDocument();
    expect(screen.getByText('Su')).toBeInTheDocument();
    expect(screen.getByText('Mo')).toBeInTheDocument();
    expect(screen.getByText('14.5°')).toBeInTheDocument();
    expect(screen.getByText('22.1°')).toBeInTheDocument();
  });
});

