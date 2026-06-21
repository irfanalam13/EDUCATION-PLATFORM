import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth";

// Routes that require an authenticated session. The public catalogue
// (/, /academics, /content/[id], /login, /signup) is intentionally open.
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/leaderboard",
  "/badges",
  "/notifications",
  "/content/notes",
  "/quiz",
  "/assistant",
  "/ai",
  "/profile",
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const needsAuth = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
  if (!needsAuth) return NextResponse.next();

  // A refresh token (or still-valid access token) means there is a session;
  // the BFF proxy refreshes the access token on demand.
  const hasSession =
    req.cookies.has(ACCESS_COOKIE) || req.cookies.has(REFRESH_COOKIE);
  if (hasSession) return NextResponse.next();

  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.searchParams.set("next", pathname);
  return NextResponse.redirect(url);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/leaderboard/:path*",
    "/badges/:path*",
    "/notifications/:path*",
    "/content/notes/:path*",
    "/quiz/:path*",
    "/assistant/:path*",
    "/ai/:path*",
    "/profile/:path*",
  ],
};
