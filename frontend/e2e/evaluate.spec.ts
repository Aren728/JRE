import { test, expect } from '@playwright/test';

// Live backend contract: the evaluate page POSTs to {API_URL}/api/v1/evaluate/custom
// (X-API-Key) and the report flow POSTs to {API_URL}/api/v1/analyze.
const API_URL = process.env.API_URL ?? 'http://localhost:8000';

test.describe('Evaluate page end-to-end', () => {
  test('evaluates birth data and renders the full report tabs', async ({ page }) => {
    await page.goto('/evaluate');
    await expect(page.getByRole('heading', { name: 'Chart Evaluation Input' })).toBeVisible();

    // Fill the known-good chart (form defaults are New Delhi / IST; set date + time explicitly).
    // NOTE: the location autocomplete hits the external Nominatim API, so we intentionally
    // keep the prefilled location rather than typing into it.
    await page.locator('input[type="date"]').fill('1995-09-28');
    await page.locator('input[placeholder="02:30"]').fill('02:30');
    const ampm = page.getByRole('combobox').first();
    await expect(ampm).toHaveValue('PM');

    await page.getByRole('button', { name: 'Run Evaluation' }).click();

    // Backend computes the full chart; tabs render once EvaluationResponse arrives.
    await expect(
      page.getByRole('heading', { name: 'Dynamic Astro-Karmic Blueprint' })
    ).toBeVisible({ timeout: 90_000 });
    await expect(page.getByText(/Yogas Detected/)).toBeVisible();

    // Tab navigation renders real, server-derived content.
    // (Blueprint tab shows "Core Natal Charts"; the Charts tab shows "Divisional Charts".)
    await page.getByRole('button', { name: /Charts/ }).click();
    await expect(page.getByRole('heading', { name: 'Divisional Charts' })).toBeVisible();

    // Report generation: Overview tab -> /api/v1/analyze -> markdown synthesis renders.
    await page.getByRole('button', { name: /Overview/ }).click();
    await page.getByRole('button', { name: 'Generate Full Report' }).click();
    // The Overview tab renders the synthesis markdown under "Chart Synthesis Report";
    // the Blueprint tab carries the "Cosmic Synthesis Blueprint" heading instead.
    await expect(
      page.getByRole('heading', { name: /Part 1: Your Psychological/ })
    ).toBeVisible({ timeout: 120_000 });

    // Response contract sanity: chart data came from the evaluate endpoint.
    await expect(page.getByText(/Lagna:/)).toBeVisible();
  });

  test('evaluate/custom endpoint contract matches what the page binds to', async ({ request }) => {
    // Guard the API contract independently of the UI: every top-level key
    // EvaluationReportTabs reads must be present in the response.
    const res = await request.post(`${API_URL}/api/v1/evaluate/custom`, {
      headers: { 'X-API-Key': 'jre-beta-key-alpha' },
      data: {
        date: '1995-09-28',
        time: '14:30:00',
        latitude: 28.6139,
        longitude: 77.209,
        timezone: 'Asia/Kolkata',
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const key of [
      'planet_details',
      'evaluation_id',
      'yogas',
      'deep_dasha',
      'birth_data_display',
      'dignity_map',
      'elemental_balance',
      'parivartana_yogas',
      'parivartana_synthesis',
      'lagna',
      'moon_nakshatra',
    ]) {
      expect(body, `missing key: ${key}`).toHaveProperty(key);
    }
  });
});
