import { NextResponse } from "next/server";

import { backendBaseUrl } from "@/lib/auth";


export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch(`${backendBaseUrl()}/api/accounts/auth/resend-verification/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  return NextResponse.json(payload, { status: response.status });
}
