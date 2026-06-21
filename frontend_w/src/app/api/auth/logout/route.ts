import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import { ACCESS_COOKIE, backendBaseUrl, REFRESH_COOKIE } from "@/lib/auth";


export async function POST() {
  const cookieStore = await cookies();
  const refresh = cookieStore.get(REFRESH_COOKIE)?.value;

  if (refresh) {
    await fetch(`${backendBaseUrl()}/api/accounts/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
  }

  cookieStore.delete(ACCESS_COOKIE);
  cookieStore.delete(REFRESH_COOKIE);

  return NextResponse.json({ ok: true });
}
