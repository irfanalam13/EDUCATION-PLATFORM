export const ACCESS_COOKIE = "access_token";
export const REFRESH_COOKIE = "refresh_token";

// Options for the httpOnly JWT cookies set by the auth/proxy routes. `secure`
// is on in production (Vercel serves over HTTPS) so the browser never sends the
// tokens over plaintext; it stays off in local dev (http://localhost) so login
// works without TLS. SameSite=Lax is safe here because the browser only ever
// talks to same-origin Next.js routes (the BFF proxy), never Django directly.
export const AUTH_COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax",
  secure: process.env.NODE_ENV === "production",
  path: "/",
} as const;

// Backend base URL — where the Next.js server-side proxy (/api/backend, /api/auth)
// forwards requests to Django. The value comes entirely from the environment:
//   • local dev  → frontend_w/.env.local  (BACKEND_URL)
//   • production → Vercel dashboard env    (BACKEND_URL)
// The localhost fallback only applies if no env var is set at all.
export function backendBaseUrl() {
  return (
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}
