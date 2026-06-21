import { NextResponse } from "next/server";

import { backendFetch, refreshAccessIfNeeded } from "@/lib/server-api";
import { cookies } from "next/headers";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth";


export async function GET() {
  const cookieStore = await cookies();

  let response = await backendFetch("/api/accounts/me/");
  if (response.status === 401) {
    const refreshed = await refreshAccessIfNeeded();
    if (refreshed?.access) {
      cookieStore.set(ACCESS_COOKIE, refreshed.access, { httpOnly: true, sameSite: "lax", path: "/" });
      if (refreshed.refresh) {
        cookieStore.set(REFRESH_COOKIE, refreshed.refresh, { httpOnly: true, sameSite: "lax", path: "/" });
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
