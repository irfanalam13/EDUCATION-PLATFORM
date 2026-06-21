export const ACCESS_COOKIE = "access_token";
export const REFRESH_COOKIE = "refresh_token";

export function backendBaseUrl() {
  return (
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}
