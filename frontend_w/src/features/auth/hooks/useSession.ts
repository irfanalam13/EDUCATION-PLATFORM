"use client";

import { useEffect, useState } from "react";
import { authAPI } from "../api/auth.client";
import { User } from "../types/auth.types";

export function useSession() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authAPI
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading, authenticated: !!user };
}
