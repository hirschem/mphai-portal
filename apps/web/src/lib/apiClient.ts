function isFormDataBody(body: unknown): body is FormData {
  if (!body) return false;
  if (typeof FormData !== "undefined" && body instanceof FormData) return true;
  // Fallback for edge cases / different realms
  return Object.prototype.toString.call(body) === "[object FormData]";
}

function stripContentType(headers: Record<string, string>): Record<string, string> {
  for (const k of Object.keys(headers)) {
    if (k.toLowerCase() === "content-type") delete headers[k];
  }
  return headers;
}

function hasContentType(headers: Record<string, string>): boolean {
  return Object.keys(headers).some((k) => k.toLowerCase() === "content-type");
}
// Like apiFetch, but treats 404 as ok (data: null, ok: false, status: 404)
export async function apiFetchOptional<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T | null; error: unknown; requestId: string | null }> {
  const url = path.startsWith('http') ? path : `${API_URL}${path}`;
  const isFormData = isFormDataBody(options.body);
  const headers = buildHeaders(url, (options.headers as Record<string, string>) || {});
  if (isFormData) {
    stripContentType(headers);
  } else if (options.body != null && !hasContentType(headers)) {
    headers["Content-Type"] = "application/json";
  }
  const fetchBody = isFormData
    ? (options.body as FormData)
    : options.body != null
    ? JSON.stringify(options.body)
    : undefined;
  let resp: Response;
  let requestId: string | null = null;
  let text = '';
  let data: T = undefined as unknown as T;
  try {
    resp = await fetch(url, { ...options, headers, body: fetchBody });
    requestId = resp.headers.get('x-request-id') ?? null;
    text = await resp.text();
    try { data = text ? (JSON.parse(text) as T) : undefined as unknown as T; } catch { data = undefined as unknown as T; }
    if (resp.ok) {
      return { ok: true, status: resp.status, data, error: null, requestId };
    } else if (resp.status === 404) {
      // Treat 404 as valid empty state
      return { ok: false, status: 404, data: null, error: null, requestId };
    } else {
      // Minimal error logging for failed API requests
      console.error('[API ERROR]', {
        method: options.method || 'GET',
        url,
        status: resp.status,
        body: text
      });
      return { ok: false, status: resp.status, data, error: data, requestId };
    }
  } catch (error: unknown) {
    return { ok: false, status: 0, data: null, error, requestId };
  }
}
// src/lib/apiClient.ts
import { readAuthToken } from './auth';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function isBrowser() {
  return typeof window !== 'undefined';
}

function getAuthToken(): string | null {
  if (!isBrowser()) return null;
  return readAuthToken();
}

function shouldAttachAuth(url: string): boolean {
  if (url.startsWith('/')) return true;
  try {
    const api = new URL(API_URL);
    const req = new URL(url, API_URL);
    return req.origin === api.origin;
  } catch {
    return false;
  }
}

function buildHeaders(url: string, extra: Record<string, string> = {}): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...extra,
  };
  if (token && shouldAttachAuth(url)) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}


export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T; error: unknown; requestId: string | null }> {
  const url = path.startsWith('http') ? path : `${API_URL}${path}`;
  const isFormData = isFormDataBody(options.body);
  const headers = buildHeaders(url, (options.headers as Record<string, string>) || {});
  if (isFormData) {
    stripContentType(headers);
  } else if (options.body != null && !hasContentType(headers)) {
    headers["Content-Type"] = "application/json";
  }
  const fetchBody = isFormData
    ? (options.body as FormData)
    : options.body != null
    ? JSON.stringify(options.body)
    : undefined;
  let resp: Response;
  let requestId: string | null = null;
  let text = '';
  let data: T = undefined as unknown as T;
  try {
    resp = await fetch(url, { ...options, headers, body: fetchBody });
    requestId = resp.headers.get('x-request-id') ?? null;
    text = await resp.text();
    try { data = text ? (JSON.parse(text) as T) : undefined as unknown as T; } catch { data = undefined as unknown as T; }
    if (resp.ok) {
      return { ok: true, status: resp.status, data, error: null, requestId };
    } else {
      // Minimal error logging for failed API requests
      console.error('[API ERROR]', {
        method: options.method || 'GET',
        url,
        status: resp.status,
        body: text
      });
      return { ok: false, status: resp.status, data, error: data, requestId };
    }
  } catch (error: unknown) {
    return { ok: false, status: 0, data: undefined as unknown as T, error, requestId };
  }
}

export async function apiFetchWithMeta<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T; error: unknown; requestId: string | null }> {
  // Alias for apiFetch, kept for compatibility
  return apiFetch<T>(path, options);
}