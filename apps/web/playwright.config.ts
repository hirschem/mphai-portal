import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  retries: 0,
  timeout: 60000,
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
  },
  webServer: {
    command: 'npm run dev -- -p 3000',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: {
      NODE_ENV: "test",
      TZ: "UTC",
      DEMO_PASSWORD: process.env.DEMO_PASSWORD ?? "",
      NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "",
      // Add other keys as needed, always default to ""
    },
  },
});
