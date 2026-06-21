import { cookies } from "next/headers";

import { ACCESS_COOKIE, backendBaseUrl, REFRESH_COOKIE } from "./auth";


type FetchOptions = Omit<RequestInit, "headers"> & { headers?: Record<string, string> };

export async function backendFetch(path: string, opts: FetchOptions = {}) {
  const cookieStore = await cookies();
  const access = cookieStore.get(ACCESS_COOKIE)?.value;

  const headers: Record<string, string> = {
    ...(opts.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(opts.headers ?? {}),
  };

  if (access) {
    headers.Authorization = `Bearer ${access}`;
  }

  return fetch(`${backendBaseUrl()}${path}`, {
    ...opts,
    headers,
    cache: "no-store",
  });
}


export async function refreshAccessIfNeeded() {
  const cookieStore = await cookies();
  const refresh = cookieStore.get(REFRESH_COOKIE)?.value;
  if (!refresh) return null;

  const response = await fetch(`${backendBaseUrl()}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });

  if (!response.ok) return null;
  return response.json() as Promise<{ access: string; refresh?: string }>;
}
