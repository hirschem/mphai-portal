import { test, expect } from '@playwright/test';

const DEMO_PASSWORD = process.env.DEMO_PASSWORD || 'demo2026';
const AUTH_TOKEN_KEY = 'auth_token'; // from apps/web/src/lib/auth.ts

function normalizeBase(base: string): string {
  return base.replace(/\/+$/, '');
}

test('login → generate → download PDF endpoint 200', async ({ page, request }) => {
  // Keep UI navigation deterministic (but do not rely on browser CORS/network constraints).
  await page.goto('/login');

  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.E2E_API_BASE_URL ||
    'https://mphai-portal-production.up.railway.app';
  const base = normalizeBase(apiBase);

  // Perform login via APIRequestContext (bypasses browser CORS/network constraints).
  const loginResp = await request.post(`${base}/api/auth/login`, {
    headers: { 'content-type': 'application/json' },
    data: { password: DEMO_PASSWORD },
  });

  expect(loginResp.status()).toBe(200);

  const loginJson = await loginResp.json();
  const token: string | undefined = loginJson?.access_token;
  expect(token).toBeTruthy();

  // Store token in localStorage with the correct key.
  await page.evaluate(
    ({ k, t }) => {
      window.localStorage.setItem(k, t);
    },
    { k: AUTH_TOKEN_KEY, t: token as string }
  );

  // Read back deterministically using the correct key.
  const storedToken = await page.evaluate((k) => window.localStorage.getItem(k), AUTH_TOKEN_KEY);
  expect(storedToken).toBe(token);

  // Deterministic generate via APIRequestContext.
  const sessionId = `e2e-${Date.now()}`;

  const genResp = await request.post(`${base}/api/proposals/generate`, {
    headers: {
      'content-type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    data: {
      session_id: sessionId,
      raw_text: 'Playwright smoke test: generate proposal + download PDF.',
    },
  });

  expect(genResp.status()).toBe(200);

  const genJson = await genResp.json();
  const returnedSessionId: string | undefined = genJson?.session_id;
  expect(returnedSessionId).toBeTruthy();

  const downloadUrl = `${base}/api/proposals/download/${returnedSessionId}`;
  const downloadResp = await request.get(downloadUrl, {
    headers: { Authorization: `Bearer ${token}` },
  });

  expect(downloadResp.status()).toBe(200);
  expect(downloadResp.headers()['content-type'] || '').toContain('pdf');

  const pdfBytes = await downloadResp.body();
  expect(pdfBytes.length).toBeGreaterThan(500);
});