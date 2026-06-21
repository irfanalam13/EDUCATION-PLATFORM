import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import { ACCESS_COOKIE, backendBaseUrl, REFRESH_COOKIE } from "@/lib/auth";


export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch(`${backendBaseUrl()}/api/auth/token/`, {
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
  cookieStore.set(ACCESS_COOKIE, payload.access, { httpOnly: true, sameSite: "lax", path: "/" });
  cookieStore.set(REFRESH_COOKIE, payload.refresh, { httpOnly: true, sameSite: "lax", path: "/" });

  return NextResponse.json({ ok: true });
}
