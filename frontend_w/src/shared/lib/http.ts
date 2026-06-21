import { env } from "@/config/env";
import { tokenStore } from "./auth";

export type ApiError = {
  status: number;
  message: string;
  details?: unknown;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  headers?: Record<string, string>;
  cache?: RequestCache;
};

// ✅ Django backend URL builder
function buildBackendUrl(path: string) {
  const base = env.API_BASE_URL.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

// ✅ Next (same-origin) URL builder
function buildLocalUrl(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

// ✅ BACKEND API (Django)
export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const url = buildBackendUrl(path);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers ?? {}),
  };

  if (opts.auth) {
    const token = tokenStore.getAccess();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    cache: opts.cache ?? "no-store",
  });

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json().catch(() => null) : await res.text().catch(() => null);

  if (!res.ok) {
    throw {
      status: res.status,
      message:
        (data && typeof data === "object" && "detail" in data && String((data as any).detail)) ||
        res.statusText ||
        "Request failed",
      details: data,
    } satisfies ApiError;
  }

  return data as T;
}

// ✅ LOCAL API (Next routes, used for cookie login/session)
export async function apiLocal<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const url = buildLocalUrl(path);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers ?? {}),
  };

  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    cache: opts.cache ?? "no-store",
  });

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json().catch(() => null) : await res.text().catch(() => null);

  if (!res.ok) {
    throw {
      status: res.status,
      message:
        (data && typeof data === "object" && "detail" in data && String((data as any).detail)) ||
        res.statusText ||
        "Request failed",
      details: data,
    } satisfies ApiError;
  }

  return data as T;
}
