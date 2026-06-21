import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE } from "@/lib/auth";


const protectedPrefixes = ["/dashboard", "/content/notes", "/quiz", "/assistant"];

function isProtected(pathname: string) {
  return protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
}


export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (!isProtected(pathname)) {
    return NextResponse.next();
  }

  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  if (!access) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  const sessionResponse = await fetch(new URL("/api/auth/session", request.url), {
    headers: { cookie: request.headers.get("cookie") ?? "" },
    cache: "no-store",
  });
  const session = await sessionResponse.json().catch(() => ({ authenticated: false }));

  if (!session?.authenticated) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/login";
    redirectUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}


export const config = {
  matcher: ["/dashboard/:path*", "/content/notes/:path*", "/quiz/:path*", "/assistant/:path*"],
};
