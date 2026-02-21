import { ApiError } from "./apiTypes";
import { readAuthToken } from "./auth";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "";

export const API_URL = BASE_URL || "http://localhost:8000";
export async function apiFetchOptional<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
) {
  return apiFetchWithMeta<T>(path, opts);
}

export async function apiHealth() {
  return apiFetch<{ status: string }>('/health');
}

export async function apiAuthProbe(token?: string) {
  return apiFetch<unknown>("/api/proposals/generate", {
    method: "POST",
    body: JSON.stringify({ raw_text: "test", session_id: "probe" }),
    token,
  });
}


// Helper to safely read a string field from an unknown JSON object
function readStringField(obj: unknown, key: string): string | undefined {
  if (typeof obj === 'object' && obj !== null && Object.prototype.hasOwnProperty.call(obj, key)) {
    const val = (obj as { [k: string]: unknown })[key];
    return typeof val === 'string' ? val : undefined;
  }
  return undefined;
}

export async function apiFetch<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...init } = opts;
  const url = new URL(path.replace(/^\/+/, ""), BASE_URL).toString();
  const headers = new Headers(init.headers || {});

  headers.set("Accept", "application/json");

  if (init.body && typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

    const finalToken = token ?? readAuthToken();
  if (finalToken) {
    headers.set("Authorization", `Bearer ${finalToken}`);
  }

  let res: Response;

  try {
    res = await fetch(url, { ...init, headers });
  } catch {
    throw new ApiError({ status: 0, message: "Network error" });
  }

  let data: unknown = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }


  if (!res.ok) {
    throw new ApiError({
      status: res.status,
      message:
        readStringField(data, 'message') ||
        readStringField(data, 'detail') ||
        "Request failed",
      // code property removed to satisfy ESLint/type error
      requestId: readStringField(data, 'request_id'),
    });
  }

  return data as T;
}

export async function apiFetchWithMeta<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<{
  ok: boolean;
  status: number;
  data?: T;
  error?: unknown;
  requestId?: string;
}> {
  const { token, ...init } = opts;
  const url = new URL(path.replace(/^\/+/, ""), BASE_URL).toString();
  const headers = new Headers(init.headers || {});

  headers.set("Accept", "application/json");

  if (init.body && typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const finalToken = token ?? readAuthToken();
  if (finalToken) {
    headers.set("Authorization", `Bearer ${finalToken}`);
  }

  let res: Response;
  let requestId: string | undefined = undefined;

  // Detailed auth debug log
  console.log("AUTH DEBUG", {
    url,
    tokenParam: token ? token.slice(0, 12) + "..." : null,
    accessFromGetter: readAuthToken()?.slice(0, 12) + "..." ?? null,
    finalToken: finalToken ? finalToken.slice(0, 12) + "..." : null,
    authHeaderBeforeFetch: headers.get("Authorization"),
    hasAuthHeader: headers.has("Authorization"),
    headerKeys: Array.from(headers.keys()),
  });

  try {
    res = await fetch(url, { ...init, headers });
    requestId = res.headers.get("x-request-id") || undefined;
  } catch {
    return {
      ok: false,
      status: 0,
      error: new ApiError({ status: 0, message: "Network error" }),
      requestId,
    };
  }

  let data: unknown = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      error: new ApiError({
        status: res.status,
        message:
          readStringField(data, 'message') ||
          readStringField(data, 'detail') ||
          "Request failed",
        // code property removed to satisfy ESLint/type error
        requestId: readStringField(data, 'request_id'),
      }),
      requestId,
    };
  }

  return {
    ok: true,
    status: res.status,
    data: data as T,
    requestId,
  };
}

export async function apiFetchBlobWithMeta(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<{
  ok: boolean;
  status: number;
  data?: Blob;
  error?: unknown;
  requestId?: string;
}> {
  const { token, ...init } = opts;
  const url = new URL(path.replace(/^\/+/, ""), BASE_URL).toString();
  const headers = new Headers(init.headers || {});

  headers.set("Accept", "application/pdf");

    const finalToken = token ?? readAuthToken();
  if (finalToken) {
    headers.set("Authorization", `Bearer ${finalToken}`);
  }

  let res: Response;
  let requestId: string | undefined = undefined;

  try {
    res = await fetch(url, { ...init, headers });
    requestId = res.headers.get("x-request-id") || undefined;
  } catch {
    return {
      ok: false,
      status: 0,
      error: new ApiError({ status: 0, message: "Network error" }),
      requestId,
    };
  }

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      error: new ApiError({
        status: res.status,
        message: "Failed to download file",
      }),
      requestId,
    };
  }

  const blob = await res.blob();

  return {
    ok: true,
    status: res.status,
    data: blob,
    requestId,
  };
}