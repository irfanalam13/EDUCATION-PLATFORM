// export async function fetchJSON(
//   url: string,
//   options: RequestInit = {}
// ) {
//   const res = await fetch(url, {
//     ...options,
//     headers: {
//       "Content-Type": "application/json",
//       ...(options.headers || {}),
//     },
//     cache: "no-store",
//   });

//   const data = await res.json().catch(() => ({}));
//   if (!res.ok) throw data;
//   return data;
// }

















// src/shared/lib/fetcher.ts
type FetchJSONOptions = RequestInit & { body?: any };

const API_ORIGIN =
  process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://127.0.0.1:8000";

// ✅ always keep /api in your paths; pass urls like "/api/accounts/..."
export async function fetchJSON<T = any>(path: string, options: FetchJSONOptions = {}) {
  const url = path.startsWith("http")
    ? path
    : `${API_ORIGIN}${path.startsWith("/") ? "" : "/"}${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  const text = await res.text();
  let data: any = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const message =
      (data && (data.detail || data.message)) || `Request failed: ${res.status}`;
    throw new Error(message);
  }

  return data as T;
}
