import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import EvaluatePage from '@/app/evaluate/page';

// Mock the heavy report component; assert which props the page passes through.
jest.mock('@/components/EvaluationReportTabs', () => {
  return function MockEvaluationReportTabs(props: any) {
    return (
      <div data-testid="report-tabs">
        <div data-testid="prop-evaluation-id">{props.evaluationData?.evaluation_id}</div>
        <div data-testid="prop-lagna">{props.evaluationData?.lagna}</div>
        <div data-testid="prop-synthesis-markdown">{props.synthesisMarkdown}</div>
        <div data-testid="prop-synthesis-error">{props.synthesisError}</div>
        <div data-testid="prop-is-synthesizing">{String(props.isSynthesizing)}</div>
        <div data-testid="prop-birth-time">{props.birthDisplay?.time}</div>
        <button data-testid="mock-generate" onClick={() => props.onGenerateReport?.()}>
          mock generate
        </button>
      </div>
    );
  };
});

// jsdom has no fetch; jest.setup.ts installs a jest.fn() we control per test.
const fetchMock = globalThis.fetch as jest.Mock;

const okJson = (body: any) => ({ ok: true, status: 200, json: async () => body });

const EVALUATION_RESPONSE = {
  evaluation_id: 'eval-1',
  lagna: 'MAKARA',
  moon_nakshatra: 'VISHAKHA',
  yogas: [
    {
      yoga_name: 'Gajakesari',
      status: 'FORMED',
      involved_planets: ['JUPITER', 'MOON'],
      static_strength: 0.8,
      domains: ['CAREER_PROMINENCE'],
    },
  ],
  elemental_balance: { fire: 2, earth: 1, air: 3, water: 2 },
  dignity_map: { SUN: 'Exalted' },
  planet_details: { SUN: { sign: 'KANYA', degree_in_sign: 12.5, house: 9 } },
  birth_data_display: { date: '1995-09-28', time: '14:30:00', timezone: 'Asia/Kolkata' },
  deep_dasha: { md: { lord: 'MARS' } },
  parivartana_yogas: [],
  parivartana_synthesis: {},
  unknown_tob: false,
  skipped_yogas: [],
  disclaimer: 'For entertainment purposes only.',
};

const getDateInput = () => document.querySelector('input[type="date"]') as HTMLInputElement;

const callsToUrl = (fragment: string) =>
  fetchMock.mock.calls.filter(([url]) => String(url).includes(fragment));

const lastBodyFor = (fragment: string) => {
  const calls = callsToUrl(fragment);
  expect(calls.length).toBeGreaterThan(0);
  return JSON.parse(calls[calls.length - 1][1].body);
};

describe('EvaluatePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetchMock.mockImplementation(async () => okJson(EVALUATION_RESPONSE));
  });

  test('renders the evaluation form with all required fields', () => {
    render(<EvaluatePage />);

    expect(screen.getByRole('heading', { name: 'Chart Evaluation Input' })).toBeInTheDocument();
    expect(getDateInput()).toHaveValue('1995-09-28');
    expect(screen.getByPlaceholderText('02:30')).toHaveValue('02:30');
    expect(screen.getByRole('button', { name: 'Run Evaluation' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('28.6139')).toBeInTheDocument();
    expect(screen.getByDisplayValue('77.209')).toBeInTheDocument();

    // No geocode request should fire on mount (query equals the resolved location).
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test('Run Evaluation posts the documented payload and renders the report tabs', async () => {
    render(<EvaluatePage />);

    fireEvent.submit(document.querySelector('form') as HTMLFormElement);

    await waitFor(() => {
      expect(screen.getByTestId('report-tabs')).toBeInTheDocument();
    });

    const evaluateCalls = callsToUrl('/api/v1/evaluate/custom');
    expect(evaluateCalls).toHaveLength(1);
    const [url, init] = evaluateCalls[0];
    expect(String(url)).toContain('/api/v1/evaluate/custom');
    expect(init.method).toBe('POST');
    expect(init.headers['X-API-Key']).toBe('jre-beta-key-alpha');

    const body = JSON.parse(init.body);
    // 12-hour "02:30 PM" -> 24-hour "14:30:00"; ISO date passthrough.
    expect(body).toMatchObject({
      date: '1995-09-28',
      time: '14:30:00',
      latitude: 28.6139,
      longitude: 77.209,
      timezone: 'Asia/Kolkata',
    });

    expect(screen.getByTestId('prop-evaluation-id')).toHaveTextContent('eval-1');
    expect(screen.getByTestId('prop-lagna')).toHaveTextContent('MAKARA');
    // The page passes a 12-hour display time through birthDisplay.
    expect(screen.getByTestId('prop-birth-time')).toHaveTextContent('02:30 PM');
  });

  test('AM selection converts midnight hours correctly', async () => {
    render(<EvaluatePage />);

    const ampmSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(ampmSelect, { target: { value: 'AM' } });

    fireEvent.submit(document.querySelector('form') as HTMLFormElement);

    await waitFor(() => {
      expect(screen.getByTestId('report-tabs')).toBeInTheDocument();
    });

    expect(lastBodyFor('/api/v1/evaluate/custom').time).toBe('02:30:00');
  });

  test('endpoint string detail is surfaced as the error message and tabs stay hidden', async () => {
    fetchMock.mockImplementation(
      async () => ({
        ok: false,
        status: 422,
        json: async () => ({ detail: 'Chart computation failed: boom' }),
      })
    );

    render(<EvaluatePage />);
    fireEvent.submit(document.querySelector('form') as HTMLFormElement);

    await waitFor(() => {
      expect(screen.getByText('Chart computation failed: boom')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('report-tabs')).not.toBeInTheDocument();
  });

  test('pydantic array details are formatted with the failing field', async () => {
    fetchMock.mockImplementation(
      async () => ({
        ok: false,
        status: 422,
        json: async () => ({
          detail: [{ loc: ['body', 'date'], msg: 'invalid date format' }],
        }),
      })
    );

    render(<EvaluatePage />);
    fireEvent.submit(document.querySelector('form') as HTMLFormElement);

    await waitFor(() => {
      expect(screen.getByText(/body\.date - invalid date format/)).toBeInTheDocument();
    });
  });

  test('dates before the Gregorian cutoff are rejected without an API call', async () => {
    render(<EvaluatePage />);

    fireEvent.change(getDateInput(), { target: { value: '0979-09-28' } });
    fireEvent.submit(document.querySelector('form') as HTMLFormElement);

    await waitFor(() => {
      expect(
        screen.getByText(/Date must be on or after October 15, 1582/)
      ).toBeInTheDocument();
    });
    expect(callsToUrl('/api/v1/evaluate/custom')).toHaveLength(0);
  });

  test('Generate Full Report posts to /api/v1/analyze and wires synthesis props', async () => {
    render(<EvaluatePage />);

    fireEvent.submit(document.querySelector('form') as HTMLFormElement);
    await waitFor(() => {
      expect(screen.getByTestId('report-tabs')).toBeInTheDocument();
    });

    // While synthesis runs, the page reports its loading state to the tabs.
    let resolveSynthesis: (value: any) => void = () => {};
    fetchMock.mockImplementationOnce(
      () => new Promise((resolve) => (resolveSynthesis = resolve))
    );

    fireEvent.click(screen.getByTestId('mock-generate'));
    await waitFor(() => {
      expect(screen.getByTestId('prop-is-synthesizing')).toHaveTextContent('true');
    });

    resolveSynthesis(
      okJson({ synthesis_markdown: '# Synthesis Report\n\nAll good.' })
    );
    await waitFor(() => {
      expect(screen.getByTestId('prop-is-synthesizing')).toHaveTextContent('false');
    });
    expect(screen.getByTestId('prop-synthesis-markdown')).toHaveTextContent('Synthesis Report');

    const analyzeCalls = callsToUrl('/api/v1/analyze');
    expect(analyzeCalls).toHaveLength(1);
    expect(lastBodyFor('/api/v1/analyze')).toMatchObject({
      date: '1995-09-28',
      time: '14:30:00',
      latitude: 28.6139,
      longitude: 77.209,
      timezone: 'Asia/Kolkata',
    });
  });

  test('selecting a geocoded result updates coordinates and location', async () => {
    render(<EvaluatePage />);

    fetchMock.mockResolvedValueOnce(
      okJson([{ display_name: 'London, UK', lat: '51.5074', lon: '-0.1278' }])
    );

    fireEvent.change(screen.getByPlaceholderText(/Search city/), {
      target: { value: 'Lond' },
    });

    // Debounced (400ms) Nominatim lookup resolves and opens the dropdown.
    await waitFor(
      () => {
        expect(screen.getAllByRole('listitem').length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );

    fireEvent.click(screen.getAllByRole('listitem')[0]);

    await waitFor(() => {
      expect(screen.getByDisplayValue('51.5074')).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue('-0.1278')).toBeInTheDocument();
    expect(screen.getByDisplayValue('London, UK')).toBeInTheDocument();
  });
});
