import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SAVViewer, {
  savBand,
  bavCellColor,
  type AshtakavargaReport,
} from '../components/ashtakavarga/SAVViewer';

// Deterministic report fixture (shape of ashtakavarga_to_dict()).
// SAV row sums to the classical invariant 337.
const SAV: number[] = [22, 27, 30, 22, 34, 19, 27, 35, 29, 42, 22, 28];

const createReport = (overrides: Partial<AshtakavargaReport> = {}): AshtakavargaReport => ({
  ...({} as AshtakavargaReport),
  version: '1.0.0',
  anchor_signs: {
    SUN: 'MEENA',
    MOON: 'VRISHCHIKA',
    MARS: 'MAKARA',
    MERCURY: 'MEENA',
    JUPITER: 'KUMBHA',
    VENUS: 'MEENA',
    SATURN: 'MEENA',
    LAGNA: 'MITHUNA',
  },
  fact_ids: [
    'FACT-ASHTA-BAV-SUN',
    'FACT-ASHTA-BAV-MOON',
    'FACT-ASHTA-BAV-MARS',
    'FACT-ASHTA-BAV-MERCURY',
    'FACT-ASHTA-BAV-JUPITER',
    'FACT-ASHTA-BAV-VENUS',
    'FACT-ASHTA-BAV-SATURN',
    'FACT-ASHTA-BAV-LAGNA',
    'FACT-ASHTA-SAV',
    'FACT-ASHTA-PINDA-SUN',
    'FACT-ASHTA-PINDA-MOON',
    'FACT-ASHTA-PINDA-MARS',
    'FACT-ASHTA-PINDA-MERCURY',
    'FACT-ASHTA-PINDA-JUPITER',
    'FACT-ASHTA-PINDA-VENUS',
    'FACT-ASHTA-PINDA-SATURN',
    'FACT-ASHTA-PINDA-LAGNA',
  ],
  bav: {
    SUN: [3, 3, 4, 2, 5, 4, 3, 5, 6, 7, 3, 3],
    MOON: [5, 5, 3, 2, 7, 8, 0, 3, 2, 7, 3, 4],
    MARS: [2, 2, 6, 2, 3, 1, 5, 8, 2, 3, 1, 4],
    MERCURY: [5, 2, 5, 3, 5, 2, 6, 5, 5, 8, 3, 5],
    JUPITER: [3, 5, 5, 4, 5, 3, 5, 6, 7, 1, 5, 7],
    VENUS: [3, 6, 5, 6, 2, 0, 6, 7, 3, 8, 3, 3],
    SATURN: [1, 4, 2, 3, 7, 1, 2, 1, 4, 8, 4, 2],
    LAGNA: [8, 2, 5, 3, 6, 5, 2, 7, 1, 2, 2, 7],
  },
  sav: SAV,
  shodhita_sav: [18, 13, 17, 17, 18, 13, 17, 17, 18, 4, 4, 17],
  pinda: {
    SUN: { rashi_pinda: 147, graha_pinda: 40, shodhya_pinda: 187 },
    MOON: { rashi_pinda: 118, graha_pinda: 40, shodhya_pinda: 158 },
    MARS: { rashi_pinda: 96, graha_pinda: 40, shodhya_pinda: 136 },
    MERCURY: { rashi_pinda: 235, graha_pinda: 76, shodhya_pinda: 311 },
    JUPITER: { rashi_pinda: 220, graha_pinda: 88, shodhya_pinda: 308 },
    VENUS: { rashi_pinda: 132, graha_pinda: 60, shodhya_pinda: 192 },
    SATURN: { rashi_pinda: 88, graha_pinda: 28, shodhya_pinda: 116 },
    LAGNA: { rashi_pinda: 123, graha_pinda: 60, shodhya_pinda: 183 },
  },
  ...overrides,
});

describe('savBand', () => {
  test('classical banding thresholds', () => {
    expect(savBand(30).label).toBe('Strong');
    expect(savBand(28).label).toBe('Good');
    expect(savBand(25).label).toBe('Average');
    expect(savBand(24).label).toBe('Weak');
  });
});

describe('bavCellColor', () => {
  test('0 bindus is neutral/muted', () => {
    expect(bavCellColor(0).bg).toBe('transparent');
  });

  test('high bindus tint benefic', () => {
    expect(bavCellColor(8).color).toContain('benefic-green');
  });
});

describe('SAVViewer', () => {
  const baseProps = { report: createReport(), subject: 'Albert Einstein' };

  test('renders the matrix with all 12 signs and 8 anchors', () => {
    render(<SAVViewer {...baseProps} />);
    expect(screen.getByTestId('sav-viewer')).toBeInTheDocument();
    SIGN_ORDER_COUNT_CHECK: {
      // 12 sign rows in tbody (plus the TOTAL row).
      expect(screen.getAllByTestId(/^bav-SUN-/)).toHaveLength(12);
    }
    expect(screen.getByTestId('sav-MESHA')).toHaveTextContent('22');
    expect(screen.getByTestId('sav-MAKARA')).toHaveTextContent('42');
  });

  test('renders the SAV=337 total row', () => {
    render(<SAVViewer {...baseProps} />);
    expect(screen.getByTestId('sav-total-row')).toHaveTextContent('337');
  });

  test('shows subject and version', () => {
    render(<SAVViewer {...baseProps} />);
    expect(screen.getByText(/Albert Einstein/)).toBeInTheDocument();
    expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
  });

  test('toggles raw vs shodhita SAV', () => {
    render(<SAVViewer {...baseProps} />);
    const toggle = screen.getByTestId('sav-toggle-shodhita');
    expect(screen.getByTestId('sav-MAKARA')).toHaveTextContent('42');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('sav-MAKARA')).toHaveTextContent('4');
    expect(screen.getByTestId('sav-total-row')).toHaveTextContent('173');
  });

  test('renders the pinda grid by default', () => {
    render(<SAVViewer {...baseProps} />);
    expect(screen.getByTestId('sav-pinda')).toBeInTheDocument();
    expect(screen.getByText('187')).toBeInTheDocument();
  });

  test('hides pinda when hidePinda is set', () => {
    render(<SAVViewer {...baseProps} hidePinda />);
    expect(screen.queryByTestId('sav-pinda')).not.toBeInTheDocument();
  });

  test('initial shodhita view via prop', () => {
    render(<SAVViewer {...baseProps} showShodhita />);
    expect(screen.getByTestId('sav-MESHA')).toHaveTextContent('18');
  });

  test('empty state when report is null', () => {
    render(<SAVViewer report={null} />);
    expect(screen.getByTestId('sav-viewer-empty')).toBeInTheDocument();
  });

  test('SAV fixture row sums to the classical invariant 337', () => {
    const report = createReport();
    expect(report.sav.reduce((a, b) => a + b, 0)).toBe(337);
  });
});
