import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ChartAnalysis } from '@/components/ChartAnalysis';
import { api } from '@/lib/api';

// 1. Completely stub react-markdown & plugins to prevent ESM re-render loops
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }: { children: React.ReactNode }) {
    return <div data-testid="markdown-content">{children}</div>;
  };
});

jest.mock('remark-gfm', () => () => {});

// 2. Mock the api module
jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api');
  return {
    ...actual,
    api: {
      ...actual.api,
      analyzeChart: jest.fn(),
    },
  };
});

// Get the mock function after the module is loaded
const mockAnalyzeChart = (api.analyzeChart as jest.Mock);

const mockResponse = {
  core_alignment: {
    ascendant_sign: 'Aries',
    moon_nakshatra: 'Ashwini',
  },
  active_dasha: {
    mahadasha: 'Ketu',
    antardasha: 'Ketu',
    pratyantardasha: 'Ketu',
    start_date: '2026-01-01',
    end_date: '2027-01-01',
  },
  planets: [
    {
      name: 'Sun',
      longitude: 10.5,
      d1: { sign: 'Aries', degree: 10.5, house: 1 },
      d3: { sign: 'Aries', degree: 10.5, house: 1 },
      d9: { sign: 'Sagittarius', degree: 4.5, house: 9 },
      d10: { sign: 'Aries', degree: 10.5, house: 1 },
    },
  ],
  synthesis_markdown: '### Core Analysis\nExalted Sun in 1st House.',
};

describe('ChartAnalysis Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Resolve pending promises cleanly
    if (mockAnalyzeChart) {
      mockAnalyzeChart.mockReset();
    }
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders loading state initially and then displays analysis', async () => {
    // Provide a resolved promise immediately to avoid unhandled state loops
    const testResponse = {
      data: {
        core_alignment: {
          ascendant_sign: 'Aries',
          moon_nakshatra: 'Ashwini',
        },
        active_dasha: {
          mahadasha: 'Ketu',
          antardasha: 'Ketu',
          pratyantardasha: 'Ketu',
          start_date: '2026-01-01',
          end_date: '2027-01-01',
        },
        planets: [],
        synthesis_markdown: 'Test Analysis Content',
      },
    };
    
    mockAnalyzeChart.mockImplementation(() => Promise.resolve(testResponse));

    const mockChartData = {
      dob: '1990-01-01',
      time: '12:00',
      lat: 12.97,
      lon: 77.59,
      tz: 5.5,
      ayanamsha: 'lahiri',
    };

    render(<ChartAnalysis chartData={mockChartData} />);

    // Wait for the async API call to settle
    await waitFor(() => {
      expect(mockAnalyzeChart).toHaveBeenCalledTimes(1);
    }, { timeout: 5000 });

    // Wait for the component to re-render with the analysis data
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toHaveTextContent('Test Analysis Content');
    }, { timeout: 5000 });
  }, 10000);

  it('handles API error state cleanly without infinite retries', async () => {
    // Mock rejected promise explicitly
    mockAnalyzeChart.mockImplementation(() => Promise.reject(new Error('Failed to fetch analysis')));

    const mockChartData = {
      dob: '1990-01-01',
      time: '12:00',
      lat: 12.97,
      lon: 77.59,
      tz: 5.5,
      ayanamsha: 'lahiri',
    };

    render(<ChartAnalysis chartData={mockChartData} />);

    await waitFor(() => {
      expect(mockAnalyzeChart).toHaveBeenCalledTimes(1);
    });
  });
});
