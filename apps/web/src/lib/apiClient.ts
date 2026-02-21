import { ApiError } from "./apiTypes";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "";

function getAccessToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    return localStorage.getItem("access_token") || undefined;
  } catch {
    return undefined;
  }
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

  const finalToken = token ?? getAccessToken();
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
        (data as any)?.message ||
        (data as any)?.detail ||
        "Request failed",
      code: (data as any)?.code,
      request_id: (data as any)?.request_id,
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

  const finalToken = token ?? getAccessToken();
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
          (data as any)?.message ||
          (data as any)?.detail ||
          "Request failed",
        code: (data as any)?.code,
        request_id: (data as any)?.request_id,
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

  const finalToken = token ?? getAccessToken();
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