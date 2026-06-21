import type { QueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  getMe,
  login as loginRequest,
  loginWithGoogleIdToken,
  logout as logoutRequest,
  resendVerification,
  signup as signupRequest,
  verifyEmail,
  type SignupResponse
} from "@/services/auth";
import { getAccessToken } from "@/services/tokenStore";
import { registerForPushNotifications } from "@/services/push";
import type { Role, User } from "@/types/api";

type SignupPayload = {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password2: string;
  account_type: "STUDENT" | "TEACHER";
  teacher_message?: string;
};

type AuthContextValue = {
  user: User | null;
  bootstrapping: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signInWithGoogleToken: (idToken: string) => Promise<void>;
  signUp: (payload: SignupPayload) => Promise<SignupResponse>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  resendEmailVerification: (email: string) => Promise<{ detail: string; dev_otp?: string }>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
  role: Role | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  queryClient
}: {
  children: React.ReactNode;
  queryClient: QueryClient;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);

  async function refreshUser() {
    const me = await getMe();
    setUser(me);
    // Register this device for push (best-effort; never blocks auth).
    registerForPushNotifications().catch(() => {});
  }

  useEffect(() => {
    let mounted = true;
    async function bootstrap() {
      try {
        const access = await getAccessToken();
        if (access) {
          const me = await getMe();
          if (mounted) setUser(me);
        }
      } catch {
        if (mounted) setUser(null);
      } finally {
        if (mounted) setBootstrapping(false);
      }
    }
    bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      bootstrapping,
      role: user?.role ?? null,
      refreshUser,
      signIn: async (username, password) => {
        await loginRequest(username, password);
        await refreshUser();
      },
      signInWithGoogleToken: async (idToken) => {
        const me = await loginWithGoogleIdToken(idToken);
        setUser(me);
      },
      signUp: async (payload) => {
        return signupRequest(payload);
      },
      verifyEmail: async (email, code) => {
        await verifyEmail(email, code);
      },
      resendEmailVerification: async (email) => {
        return resendVerification(email);
      },
      signOut: async () => {
        await logoutRequest();
        queryClient.clear();
        setUser(null);
      }
    }),
    [bootstrapping, queryClient, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
