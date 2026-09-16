import { defineConfig, devices } from '@playwright/test';

// Frontend dev server port (next dev default 3000; override with PORT).
const PORT = Number(process.env.PORT ?? 3000);
// FastAPI backend the evaluate page calls (the spec reads API_URL from process.env).

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  // Reuse an already-running `next dev` (dev.sh / manual) instead of spawning a second one.
  webServer: process.env.E2E_NO_WEB_SERVER
    ? undefined
    : {
        command: 'npm run dev',
        url: `http://localhost:${PORT}`,
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
