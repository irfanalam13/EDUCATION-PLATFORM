import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth";

// Next.js 16 renamed the edge "middleware" entrypoint to "proxy" (same API,
// the exported function is now `proxy`). This file is the single source of
// route protection — do NOT reintroduce a middleware.ts alongside it, or the
// build fails with "Both middleware file and proxy file are detected".

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
  "/billing",
  "/pricing",
];

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const needsAuth = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
  if (!needsAuth) return NextResponse.next();

  // A refresh token (or still-valid access token) means there is a session;
  // the BFF proxy refreshes the short-lived access token on demand. Checking
  // only the access cookie would wrongly bounce users whose 15-min access
  // token has expired but who still hold a valid refresh token.
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
    "/billing/:path*",
    "/pricing/:path*",
  ],
};
