import { apiRequest } from "./api";
import { clearTokens, getRefreshToken, setTokens } from "./tokenStore";
import type { User } from "@/types/api";

export type SignupResponse = {
  id: number;
  username: string;
  email: string;
  role: User["role"];
  email_verified: boolean;
  requires_verification: boolean;
  dev_otp?: string;
};

export async function login(username: string, password: string) {
  const tokens = await apiRequest<{ access: string; refresh: string }>("/api/auth/token/", {
    method: "POST",
    auth: false,
    body: { username, password }
  });
  await setTokens(tokens);
  return tokens;
}

export async function signup(payload: {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password2: string;
  account_type: "STUDENT" | "TEACHER";
  teacher_message?: string;
}) {
  return apiRequest<SignupResponse>("/api/accounts/auth/register/", {
    method: "POST",
    auth: false,
    body: payload
  });
}

export async function verifyEmail(email: string, code: string) {
  return apiRequest<{ detail: string; user: User }>("/api/accounts/auth/verify-email/", {
    method: "POST",
    auth: false,
    body: { email, code }
  });
}

export async function resendVerification(email: string) {
  return apiRequest<{ detail: string; dev_otp?: string }>("/api/accounts/auth/resend-verification/", {
    method: "POST",
    auth: false,
    body: { email }
  });
}

export async function loginWithGoogleIdToken(idToken: string) {
  const payload = await apiRequest<{ access: string; refresh: string; user: User }>("/api/accounts/auth/google/", {
    method: "POST",
    auth: false,
    body: { id_token: idToken }
  });
  await setTokens({ access: payload.access, refresh: payload.refresh });
  return payload.user;
}

export async function getMe() {
  return apiRequest<User>("/api/accounts/me/");
}

export async function logout() {
  const refresh = await getRefreshToken();
  if (refresh) {
    await apiRequest("/api/accounts/auth/logout/", {
      method: "POST",
      body: { refresh }
    }).catch(() => undefined);
  }
  await clearTokens();
}
