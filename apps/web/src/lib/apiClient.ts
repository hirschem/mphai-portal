import { ApiError } from "./apiTypes";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function isJsonContentType(headers: Headers): boolean {
  const ct = headers.get("content-type");
  return !!ct && ct.toLowerCase().includes("application/json");
}

function isRecord(v: unknown): v is Record<string, any> {
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

  let data: any = undefined;
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
    message = data.message || data.error_message || message;
    errorCode = data.error_code || data.code;
    detail = data.detail;
  } else {
    message = await res.text().catch(() => message);
  }

  // 429: contract check detail.error === "Too many requests"
  if (res.status === 429 && isRecord(detail) && detail.error !== "Too many requests") {
    console.error("RATE_LIMIT_DETAIL_MISMATCH", { got: detail.error, requestId, path });
  }

  console.error("API_ERROR", { status: res.status, requestId, path, message, errorCode });
  throw new ApiError({ status: res.status, requestId, message, errorCode, detail });
}

// --- Minimal smoke helpers ---
export async function apiHealth() {
  return apiFetch<{ status: string }>("/health");
}

export async function apiAuthProbe(token?: string) {
  return apiFetch<any>("/api/proposals/generate", {
    method: "POST",
    body: JSON.stringify({ raw_text: "test", session_id: "probe" }),
    token,
  });
}
