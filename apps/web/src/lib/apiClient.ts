import { readAuthToken } from "./auth";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function isBrowser() {
  return typeof window !== "undefined";
}

function getAuthToken(): string | null {
  if (!isBrowser()) return null;
  return readAuthToken();
}

function getPathname(input: string): string {
  try {
    return new URL(input).pathname; // absolute URL
  } catch {
    return input; // relative path like "/api/..."
  }
}

function shouldAttachAuth(input: string): boolean {
  const path = getPathname(input);
  // only endpoint that must NOT include auth
  return path !== "/api/auth/login";
}

function isFormDataBody(body: unknown): body is FormData {
  if (!body) return false;
  if (typeof FormData !== "undefined" && body instanceof FormData) return true;
  return Object.prototype.toString.call(body) === "[object FormData]";
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<{ resp: Response; text: string; data: T; requestId: string | null }> {
  const url = path.startsWith("http") ? path : `${API_URL}${path}`;

  // --- PATCH: Canonical safe header merge and Authorization logic ---
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const headers = new Headers(options.headers ?? undefined);
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body: BodyInit | null | undefined = options.body as any;
  if (!isFormData && options.body != null && typeof options.body === "object" && !(options.body instanceof Blob) && !(options.body instanceof ArrayBuffer)) {
    body = JSON.stringify(options.body);
  }

  // --- END PATCH ---


  // --- PATCH: Temporary debug log for outgoing headers ---
  console.log("OUTGOING HEADERS", Object.fromEntries(headers.entries()));
  // --- END PATCH ---
  const { headers: _ignored, mode: _modeIgnored, credentials: _credIgnored, ...rest } = options;
  // --- PATCH: AUTH DEBUG instrumentation ---
  console.log("AUTH DEBUG", {
    url,
    token,
    shouldAttachAuth: shouldAttachAuth(url),
    headers: Object.fromEntries(headers.entries()),
  });
  // --- END PATCH ---
  const resp = await fetch(url, {
    ...rest,
    mode: "cors",
    credentials: "omit",
    headers,
    body,
  });
  const requestId = resp.headers.get("x-request-id") ?? null;

  const text = await resp.text();
  let data = undefined as unknown as T;
  try {
    data = text ? (JSON.parse(text) as T) : (undefined as unknown as T);
  } catch {
    data = undefined as unknown as T;
  }

  return { resp, text, data, requestId };
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T; error: unknown; requestId: string | null }> {
  try {
    const { resp, text, data, requestId } = await request<T>(path, options);

    if (resp.ok) return { ok: true, status: resp.status, data, error: null, requestId };

    console.error("[API ERROR]", { method: options.method || "GET", url: path, status: resp.status, body: text });
    return { ok: false, status: resp.status, data, error: data, requestId };
  } catch (error: unknown) {
    return { ok: false, status: 0, data: undefined as unknown as T, error, requestId: null };
  }
}

export async function apiFetchOptional<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T | null; error: unknown; requestId: string | null }> {
  const r = await apiFetch<T>(path, options);
  if (r.status === 404) return { ok: false, status: 404, data: null, error: null, requestId: r.requestId };
  return { ok: r.ok, status: r.status, data: r.ok ? r.data : (r.data ?? null), error: r.error, requestId: r.requestId };
}

export async function apiFetchWithMeta<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: T; error: unknown; requestId: string | null }> {
  // Alias for apiFetch, kept for compatibility
  return apiFetch<T>(path, options);
}