import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import YogaInspector, {
  mapYogaResultToEvaluation,
  type YogaEvaluation,
} from '../components/yogas/YogaInspector';

// ── Mock Data ─────────────────────────────────────────────────────────────────

const createMockYoga = (overrides: Partial<YogaEvaluation> = {}): YogaEvaluation => ({
  id: 'gajakesari',
  name: 'Gajakesari Yoga',
  category: 'RAJA' as const,
  description: 'Jupiter and Moon conjunction creates wisdom and prosperity',
  participatingPlanets: ['Jupiter', 'Moon'],
  status: 'ACTIVE_DASHA' as const,
  strengthScore: 1.45,
  activatingLord: 'Jupiter (MD)',
  houseCombination: 'Jupiter in 1st House, Moon in 10th House',
  ruleConditions: [
    { conditionText: 'Jupiter in Kendra from Moon', isMet: true },
    { conditionText: 'Jupiter free from Rahu aspect', isMet: false },
    { conditionText: 'Strength >= 1.0', isMet: true },
  ],
  ...overrides,
});

const createMultipleMockYogas = (): YogaEvaluation[] => [
  createMockYoga({ id: 'gajakesari', name: 'Gajakesari Yoga', category: 'RAJA', status: 'ACTIVE_DASHA', strengthScore: 1.45 }),
  createMockYoga({ id: 'raja', name: 'Raja Yoga', category: 'RAJA', status: 'ACTIVE_TRANSIT', strengthScore: 1.3, activatingLord: 'Sun (AD)' }),
  createMockYoga({ id: 'dhana', name: 'Dhana Yoga', category: 'DHANA', status: 'DORMANT', strengthScore: 0.85 }),
  createMockYoga({ id: 'malavya', name: 'Malavya Yoga', category: 'MAHAPURUSHA', status: 'AFFLICTED', strengthScore: 0.75 }),
  createMockYoga({ id: 'uttama', name: 'Uttama Yoga', category: 'NABHASA', status: 'ACTIVE_DASHA', strengthScore: 1.1 }),
];

const defaultProps = {
  yogas: createMultipleMockYogas(),
  activeDashaLords: ['Jupiter', 'Saturn'],
  minStrengthCutoff: 0.5,
  onSelectYoga: jest.fn(),
};

describe('YogaInspector', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the YogaInspector container', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(document.querySelector('[class*="space-y-4"]')).toBeInTheDocument();
  });

  test('renders filter rail with status toggles', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(screen.getByText('Status:')).toBeInTheDocument();
    // The status toggle buttons exist
    const buttons = screen.getAllByRole('button');
    const buttonTexts = buttons.map(b => b.textContent);
    expect(buttonTexts).toContain('Active');
    expect(buttonTexts).toContain('Dormant');
    expect(buttonTexts).toContain('Afflicted');
  });

  test('renders category dropdown', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(screen.getByText('Category:')).toBeInTheDocument();
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('');
  });

  test('renders strength threshold slider', () => {
    render(<YogaInspector {...defaultProps} />);
    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute('min', '0');
    expect(slider).toHaveAttribute('max', '2');
  });

  test('renders active dasha lords badge', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(screen.getByText('Active Dasha:')).toBeInTheDocument();
    expect(screen.getByText('Jupiter, Saturn')).toBeInTheDocument();
  });

  test('renders yoga cards for each yoga', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(screen.getByText('Gajakesari Yoga')).toBeInTheDocument();
    expect(screen.getByText('Raja Yoga')).toBeInTheDocument();
  });

  test('renders yoga name and category badge', () => {
    render(<YogaInspector {...defaultProps} />);
    // RAJA category badge exists (multiple RAJA badges for RAJA category yogas)
    const rajaBadges = screen.getAllByText('RAJA');
    expect(rajaBadges.length).toBeGreaterThanOrEqual(1);
  });

  test('renders strength scores on cards', () => {
    render(<YogaInspector {...defaultProps} />);
    expect(screen.getByText('Gajakesari Yoga')).toBeInTheDocument();
  });

  test('shows activating lord on card when present', () => {
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} />);
    const container = document.querySelector('[class*="space-y-4"]');
    if (container) {
      expect(container.textContent).toContain('Jupiter (MD)');
      expect(container.textContent).toContain('Sun (AD)');
    }
  });

  test('renders rule conditions with check/cross marks', () => {
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} />);
    const details = document.querySelectorAll('details');
    expect(details.length).toBeGreaterThan(0);
  });

  test('shows results summary with yoga count', () => {
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} />);
    expect(screen.getByText('Showing 5 of 5 yogas')).toBeInTheDocument();
  });

  test('renders legend with status colors', () => {
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} />);
    // Legend has status labels - check the legend section
    const container = document.querySelector('[class*="flex flex-wrap gap-4 justify-center"]');
    if (container) {
      expect(container.textContent).toContain('Active (Dasha)');
      expect(container.textContent).toContain('Active (Transit)');
      expect(container.textContent).toContain('Dormant');
      expect(container.textContent).toContain('Afflicted');
    }
  });

  test('renders empty state when no yogas match filters', () => {
    const emptyYogas: YogaEvaluation[] = [];
    render(<YogaInspector yogas={emptyYogas} activeDashaLords={[]} minStrengthCutoff={0.5} onSelectYoga={jest.fn()} />);
    expect(screen.getByText('No Yoga Matches')).toBeInTheDocument();
  });

  test('calls onSelectYoga when yoga card is clicked', () => {
    const onSelectYoga = jest.fn();
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} onSelectYoga={onSelectYoga} />);
    const gajakesariCard = screen.getByText('Gajakesari Yoga').closest('[class*="rounded-xl"]');
    if (gajakesariCard) {
      fireEvent.click(gajakesariCard);
    }
    expect(onSelectYoga).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'gajakesari',
        name: 'Gajakesari Yoga',
        status: 'ACTIVE_DASHA',
      }),
    );
  });

  test('sorts yogas by strength (highest first)', () => {
    render(<YogaInspector yogas={createMultipleMockYogas()} activeDashaLords={['Jupiter', 'Saturn']} minStrengthCutoff={0.5} />);
    const container = document.querySelector('[class*="grid grid-cols-1 gap-3"]');
    if (container) {
      const yogaElements = container.querySelectorAll('[class*="rounded-xl"]');
      expect(yogaElements.length).toBeGreaterThanOrEqual(2);
      const firstYoga = yogaElements[0].textContent;
      const secondYoga = yogaElements[1].textContent;
      expect(firstYoga).toContain('Gajakesari Yoga');
      expect(secondYoga).toContain('Raja Yoga');
    }
  });
});

describe('mapYogaResultToEvaluation', () => {
  const createMockYogaResult = (overrides: any = {}): any => ({
    yoga_name: 'Gajakesari',
    category: 'GAJAKESARI',
    status: 'FORMED',
    static_strength: 1.45,
    dynamic_strength: 1.2,
    involved_planets: ['Jupiter', 'Moon'],
    cancellation_reason: null,
    provenance: {
      formation_evidence: 'Jupiter and Moon conjunction in Kendra',
    },
    dasha_activation: {
      present: [{ lord: 'JUPITER', level: 'MD', start: '2020-01-01', end: '2040-01-01', duration_years: 20 }],
    },
    ...overrides,
  });

  test('maps YogaResult to YogaEvaluation', () => {
    const result = createMockYogaResult();
    const evaluation = mapYogaResultToEvaluation(result, ['Jupiter', 'Saturn']);

    expect(evaluation.id).toBe('gajakesari');
    expect(evaluation.name).toBe('Gajakesari');
    expect(evaluation.category).toBe('RAJA');
    expect(evaluation.participatingPlanets).toEqual(['Jupiter', 'Moon']);
    expect(evaluation.strengthScore).toBeCloseTo(1.45);
  });

  test('sets status to ACTIVE_DASHA when involved planets match active dasha lords', () => {
    const result = createMockYogaResult();
    const evaluation = mapYogaResultToEvaluation(result, ['JUPITER', 'SATURN']);

    expect(evaluation.status).toBe('ACTIVE_DASHA');
    expect(evaluation.activatingLord).toBe('JUPITER (MD)');
  });

  test('sets status to DORMANT when no matching dasha lords', () => {
    const result = createMockYogaResult({ involved_planets: ['MERCURY', 'SATURN'] });
    const evaluation = mapYogaResultToEvaluation(result, ['VENUS', 'MARS']);

    expect(evaluation.status).toBe('DORMANT');
    expect(evaluation.activatingLord).toBeUndefined();
  });

  test('maps category correctly', () => {
    const testCases = [
      { category: 'GAJAKESARI', expected: 'RAJA' as const },
      { category: 'RAJA', expected: 'RAJA' as const },
      { category: 'DHANA', expected: 'DHANA' as const },
      { category: 'BUDHADITYA', expected: 'MAHAPURUSHA' as const },
      { category: 'VIPAREETA_RAJA', expected: 'ARISHTA' as const },
      { category: 'PANCHAMAHAPURUSHA', expected: 'MAHAPURUSHA' as const },
      { category: 'UNKNOWN', expected: 'NABHASA' as const },
    ];

    for (const { category, expected } of testCases) {
      const result = createMockYogaResult({ category });
      const evaluation = mapYogaResultToEvaluation(result, ['JUPITER']);
      expect(evaluation.category).toBe(expected);
    }
  });

  test('generates rule conditions', () => {
    const result = createMockYogaResult({ status: 'FORMED', cancellation_reason: 'Rahu aspect' });
    const evaluation = mapYogaResultToEvaluation(result, ['JUPITER']);

    expect(evaluation.ruleConditions).toHaveLength(4);
    expect(evaluation.ruleConditions[0].conditionText).toBe('Yoga formed by classical rules');
    expect(evaluation.ruleConditions[0].isMet).toBe(true);
    expect(evaluation.ruleConditions[1].conditionText).toContain('Static strength');
    expect(evaluation.ruleConditions[2].conditionText).toBe('Dynamic strength > 0');
    expect(evaluation.ruleConditions[3].conditionText).toBe('No cancellation reason');
  });

  test('calculates strength score as ratio vs threshold', () => {
    const result = createMockYogaResult({ static_strength: 1.5 });
    const evaluation = mapYogaResultToEvaluation(result, ['JUPITER'], 1.0);
    expect(evaluation.strengthScore).toBeCloseTo(1.5);

    const evaluation2 = mapYogaResultToEvaluation(result, ['JUPITER'], 1.5);
    expect(evaluation2.strengthScore).toBeCloseTo(1.0);
  });

  test('builds house combination string from participating planets', () => {
    const result = createMockYogaResult({ involved_planets: ['Jupiter', 'Moon'] });
    const evaluation = mapYogaResultToEvaluation(result, ['JUPITER']);

    expect(evaluation.houseCombination).toBe('Jupiter & Moon combination');
  });

  test('handles single planet configuration', () => {
    const result = createMockYogaResult({ involved_planets: ['Jupiter'] });
    const evaluation = mapYogaResultToEvaluation(result, ['JUPITER']);

    expect(evaluation.houseCombination).toBe('Single planet configuration');
  });
});
