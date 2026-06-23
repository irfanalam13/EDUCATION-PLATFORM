import { NextResponse } from "next/server";

import { backendFetch, refreshAccessIfNeeded } from "@/lib/server-api";
import { cookies } from "next/headers";
import { ACCESS_COOKIE, AUTH_COOKIE_OPTIONS, REFRESH_COOKIE } from "@/lib/auth";


export async function GET() {
  const cookieStore = await cookies();

  let response = await backendFetch("/api/accounts/me/");
  if (response.status === 401) {
    const refreshed = await refreshAccessIfNeeded();
    if (refreshed?.access) {
      cookieStore.set(ACCESS_COOKIE, refreshed.access, AUTH_COOKIE_OPTIONS);
      if (refreshed.refresh) {
        cookieStore.set(REFRESH_COOKIE, refreshed.refresh, AUTH_COOKIE_OPTIONS);
      }
      response = await backendFetch("/api/accounts/me/");
    }
  }

  if (!response.ok) {
    return NextResponse.json({ authenticated: false }, { status: 200 });
  }

  const me = await response.json();
  return NextResponse.json({ authenticated: true, me }, { status: 200 });
}
