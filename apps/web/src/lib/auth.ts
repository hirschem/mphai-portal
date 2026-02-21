const AUTH_LEVEL_KEY = "auth_level";

import type { AuthLevel } from '../contexts/AuthContext';
export function readAuthLevel(): AuthLevel {
  if (typeof window === "undefined") return null;
  const level = window.localStorage.getItem(AUTH_LEVEL_KEY);
  if (level === 'admin' || level === 'demo') return level;
  return null;
}

export function writeAuthLevel(level: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_LEVEL_KEY, level.trim());
}

export function clearAuthLevel(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_LEVEL_KEY);
}
// src/lib/auth.ts
const AUTH_TOKEN_KEY = "auth_token";

// Keep temporary backwards-compat only so old saved values still work.
// Once everything is stable, you can remove the legacy list entirely.
const LEGACY_KEYS = ["access_token", "mphai_admin_password", "token", "admin_password"];

export function readAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const direct = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (direct && direct.trim()) return direct.trim();
  return null;
}

export function writeAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_TOKEN_KEY, token.trim());
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  for (const k of LEGACY_KEYS) window.localStorage.removeItem(k);
}
