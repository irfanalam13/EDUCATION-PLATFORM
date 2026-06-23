import { NextResponse } from "next/server";

import { backendFetch, refreshAccessIfNeeded } from "@/lib/server-api";
import { ACCESS_COOKIE, AUTH_COOKIE_OPTIONS, REFRESH_COOKIE } from "@/lib/auth";
import { cookies } from "next/headers";


type BackendInit = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: string;
  headers?: Record<string, string>;
};

async function fetchWithRefresh(path: string, init?: BackendInit) {
  const cookieStore = await cookies();
  let response = await backendFetch(path, init);

  if (response.status === 401) {
    const refreshed = await refreshAccessIfNeeded();
    if (refreshed?.access) {
      cookieStore.set(ACCESS_COOKIE, refreshed.access, AUTH_COOKIE_OPTIONS);
      if (refreshed.refresh) {
        cookieStore.set(REFRESH_COOKIE, refreshed.refresh, AUTH_COOKIE_OPTIONS);
      }
      response = await backendFetch(path, init);
    }
  }

  return response;
}

export async function GET() {
  const response = await fetchWithRefresh("/api/accounts/me/");
  const payload = await response.json().catch(() => ({}));
  return NextResponse.json(payload, { status: response.status });
}

export async function PATCH(request: Request) {
  const payload = await request.text();
  const response = await fetchWithRefresh("/api/accounts/me/", {
    method: "PATCH",
    body: payload,
  });
  const data = await response.json().catch(() => ({}));
  return NextResponse.json(data, { status: response.status });
}
