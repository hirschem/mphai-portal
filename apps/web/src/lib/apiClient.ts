import { ApiError } from "./apiTypes";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const BASE_URL = API_URL;

function isJsonContentType(headers: Headers): boolean {
  const ct = headers.get("content-type");
  return !!ct && ct.toLowerCase().includes("application/json");
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

export async function apiFetch<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...init } = opts; // do not pass token to fetch()

  const url = new URL(path.replace(/^\/+/, ""), BASE_URL).toString();
  const headers = new Headers(init.headers || {});
  headers.set("Accept", "application/json");

  // Only set JSON content-type if caller is sending a string body and didn't set it.
  if (init.body && typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(url, { ...init, headers });
  } catch {
    console.error("API_ERROR", { status: 0, path, message: "Network error" });
    throw new ApiError({ status: 0, message: "Network error" });
  }

  const requestId = res.headers.get("x-request-id") || undefined;
  if (!requestId) {
    console.error("MISSING_X_REQUEST_ID", { path, status: res.status });
  }

  let data: unknown = undefined;
  let isJson = isJsonContentType(res.headers);

  if (isJson) {
    try {
      data = await res.json();
    } catch {
      data = undefined;
      isJson = false;
    }
  }

  if (res.ok) {
    return data as T;
  }

  // --- Error normalization ---
  let message = "API request failed";
  let errorCode: string | undefined = undefined;
  let detail: unknown = undefined;

  if (isJson && isRecord(data)) {
    const obj = data as Record<string, unknown>;
    const msg = obj["message"];
    const altMsg = obj["error_message"];
    const ec = obj["error_code"];
    const altEc = obj["code"];

    message = (typeof msg === "string" ? msg : undefined)
      ?? (typeof altMsg === "string" ? altMsg : undefined)
      ?? message;

    errorCode =
      (typeof ec === "string" ? ec : undefined) ??
      (typeof altEc === "string" ? altEc : undefined);

    detail = obj["detail"];
  } else {
    message = await res.text().catch(() => message);
  }

  // 429: contract check detail.error === "Too many requests"
  if (res.status === 429 && isRecord(detail)) {
    const errVal = (detail as Record<string, unknown>)["error"];
    if (errVal !== "Too many requests") {
      console.error("RATE_LIMIT_DETAIL_MISMATCH", { got: errVal, requestId, path });
    }
  }

  console.error("API_ERROR", { status: res.status, requestId, path, message, errorCode });
  throw new ApiError({ status: res.status, requestId, message, errorCode, detail });
}
export async function apiFetchWithMeta<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<{ ok: boolean; status: number; data?: T; error?: unknown; requestId?: string }> {
  return apiFetchOptional<T>(path, opts);
}

export async function apiFetchOptional<T = unknown>(
  path: string,
  opts: RequestInit & { token?: string } = {}
): Promise<{ ok: boolean; status: number; data?: T; error?: unknown; requestId?: string }> {
  try {
    const data = await apiFetch<T>(path, opts);
    return { ok: true, status: 200, data };
  } catch (err: unknown) {
    const e = err as { status?: unknown; requestId?: unknown };
    return {
      ok: false,
      status: typeof e?.status === "number" ? e.status : 0,
      requestId: typeof e?.requestId === "string" ? e.requestId : undefined,
      error: err,
    };
  }
}

// --- Minimal smoke helpers ---
export async function apiHealth() {
  return apiFetch<{ status: string }>("/health");
}

export async function apiAuthProbe(token?: string) {
  return apiFetch<unknown>("/api/proposals/generate", {
    method: "POST",
    body: JSON.stringify({ raw_text: "test", session_id: "probe" }),
    token,
  });
}
