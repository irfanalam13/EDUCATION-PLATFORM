import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import { ACCESS_COOKIE, AUTH_COOKIE_OPTIONS, backendBaseUrl, REFRESH_COOKIE } from "@/lib/auth";


export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch(`${backendBaseUrl()}/api/accounts/auth/google/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status });
  }

  const cookieStore = await cookies();
  cookieStore.set(ACCESS_COOKIE, payload.access, AUTH_COOKIE_OPTIONS);
  cookieStore.set(REFRESH_COOKIE, payload.refresh, AUTH_COOKIE_OPTIONS);

  return NextResponse.json({ ok: true, user: payload.user });
}
