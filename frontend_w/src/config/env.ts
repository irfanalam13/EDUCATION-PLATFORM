// src/config/env.ts
export const env = {
  API_BASE_URL:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",

  AUTH_DISABLED:
    process.env.NEXT_PUBLIC_AUTH_DISABLED === "true",
} as const;