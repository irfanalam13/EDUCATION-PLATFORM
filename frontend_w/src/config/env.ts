// src/config/env.ts
//
// Browser-side API base used by the feature clients in shared/lib/http.ts.
// Configured via env (NEXT_PUBLIC_API_BASE_URL) — see frontend_w/.env.local.
// Recommended value is the same-origin proxy "/api/backend" (no CORS, works the
// same locally and in production).
export const env = {
  API_BASE_URL:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend",

  AUTH_DISABLED:
    process.env.NEXT_PUBLIC_AUTH_DISABLED === "true",
} as const;
