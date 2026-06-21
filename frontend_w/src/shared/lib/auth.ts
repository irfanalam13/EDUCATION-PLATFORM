// src/shared/lib/auth.ts
const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export const tokenStore = {
  getAccess(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_KEY);
  },
  setAccess(token: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_KEY, token);
  },
  getRefresh(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(REFRESH_KEY);
  },
  setRefresh(token: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(REFRESH_KEY, token);
  },
  clear() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
