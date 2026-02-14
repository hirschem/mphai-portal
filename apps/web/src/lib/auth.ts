// For backward compatibility
export const clearAuth = clearAuthToken;
// src/lib/auth.ts
function isBrowser() {
  return typeof window !== 'undefined';
}

export function readAuthToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem('mph_auth');
}

export function writeAuthToken(token: string): void {
  if (!isBrowser()) return;
  localStorage.setItem('mph_auth', token);
}

export function clearAuthToken(): void {
  if (!isBrowser()) return;
  localStorage.removeItem('mph_auth');
  localStorage.removeItem('mph_auth_level');
}

export function readAuthLevel(): 'demo' | 'admin' | null {
  if (!isBrowser()) return null;
  const level = localStorage.getItem('mph_auth_level');
  return level === 'demo' || level === 'admin' ? level : null;
}

export function writeAuthLevel(level: 'demo' | 'admin'): void {
  if (!isBrowser()) return;
  localStorage.setItem('mph_auth_level', level);
}

export function isAuthed(): boolean {
  return !!readAuthToken() && !!readAuthLevel();
}
