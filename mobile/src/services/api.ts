import { getAccessToken, getRefreshToken, setTokens, updateAccessToken } from "./tokenStore";

const configuredBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, "");

type ApiOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  auth?: boolean;
  retry?: boolean;
};

type UploadFile = {
  uri: string;
  name: string;
  mimeType?: string | null;
  type?: string | null;
};

// Single in-flight refresh: if several requests 401 at once (dashboard, learn,
// notes all firing on launch), they share ONE refresh call. Without this, the
// extra refreshes fail against rotating refresh tokens and log the user out.
let refreshPromise: Promise<string | null> | null = null;

function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const refresh = await getRefreshToken();
      if (!refresh) return null;

      const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh })
      });

      if (!response.ok) return null;

      const payload = (await response.json()) as { access: string; refresh?: string };
      if (payload.refresh) {
        await setTokens({ access: payload.access, refresh: payload.refresh });
      } else {
        await updateAccessToken(payload.access);
      }
      return payload.access;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function parseResponsePayload(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text().catch(() => null);
}

function getErrorMessage(payload: unknown, status: number) {
  if (payload && typeof payload === "object") {
    if ("detail" in payload) return String((payload as { detail: unknown }).detail);
    if ("file" in payload) return String((payload as { file: unknown }).file);
    if ("non_field_errors" in payload) return String((payload as { non_field_errors: unknown }).non_field_errors);
  }
  return `Request failed with status ${status}`;
}

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };

  if (options.auth !== false) {
    const access = await getAccessToken();
    if (access) headers.Authorization = `Bearer ${access}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  if (response.status === 401 && options.retry !== false && options.auth !== false) {
    const access = await refreshAccessToken();
    if (access) return apiRequest<T>(path, { ...options, retry: false });
  }

  const payload = await parseResponsePayload(response);

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, response.status));
  }

  return payload as T;
}

export async function apiUploadFile<T>(
  path: string,
  file: UploadFile,
  fields: Record<string, string> = {},
  options: { auth?: boolean; retry?: boolean } = {}
): Promise<T> {
  const formData = new FormData();
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value));
  formData.append("file", {
    uri: file.uri,
    name: file.name,
    type: file.mimeType || file.type || "application/pdf"
  } as unknown as Blob);

  const headers: Record<string, string> = {};
  if (options.auth !== false) {
    const access = await getAccessToken();
    if (access) headers.Authorization = `Bearer ${access}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData
  });

  if (response.status === 401 && options.retry !== false && options.auth !== false) {
    const access = await refreshAccessToken();
    if (access) return apiUploadFile<T>(path, file, fields, { ...options, retry: false });
  }

  const payload = await parseResponsePayload(response);
  if (!response.ok) {
    throw new Error(getErrorMessage(payload, response.status));
  }

  return payload as T;
}
