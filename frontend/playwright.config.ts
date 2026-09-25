import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false, retries: 0,
  timeout: 120000, expect: { timeout: 10000 }, reporter: 'list',
  outputDir: '../artifacts/phase910-tests',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:5173',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    viewport: { width: 1440, height: 1000 }, screenshot: 'only-on-failure',
    // Traces are off: they can contain bearer tokens and passwords.
    trace: 'off',
  },
})
