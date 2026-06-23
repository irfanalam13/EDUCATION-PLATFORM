import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

import { ACCESS_COOKIE, AUTH_COOKIE_OPTIONS, backendBaseUrl, REFRESH_COOKIE } from "@/lib/auth";


async function refreshAccessToken() {
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
  return (await response.json()) as { access: string; refresh?: string };
}


async function proxy(request: NextRequest, path: string[]) {
  const cookieStore = await cookies();
  const access = cookieStore.get(ACCESS_COOKIE)?.value;
  const target = `${backendBaseUrl()}/${path.join("/")}${request.nextUrl.search}`;
  const requestBody =
    request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();

  const doFetch = async (token?: string) => {
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("cookie");
    headers.delete("content-length");
    if (token) {
      headers.set("authorization", `Bearer ${token}`);
    } else {
      headers.delete("authorization");
    }

    return fetch(target, {
      method: request.method,
      headers,
      body: requestBody,
      cache: "no-store",
    });
  };

  let response = await doFetch(access);
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed?.access) {
      cookieStore.set(ACCESS_COOKIE, refreshed.access, AUTH_COOKIE_OPTIONS);
      if (refreshed.refresh) {
        cookieStore.set(REFRESH_COOKIE, refreshed.refresh, AUTH_COOKIE_OPTIONS);
      }
      response = await doFetch(refreshed.access);
    }
  }

  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}


export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}
