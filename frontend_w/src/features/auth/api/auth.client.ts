export const authAPI = {
  login: async (payload: { username: string; password: string }) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw await response.json().catch(() => ({ detail: "Login failed" }));
    return response.json();
  },

  register: async (payload: any) => {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw await response.json().catch(() => ({ detail: "Registration failed" }));
    return response.json();
  },

  logout: async () => {
    const response = await fetch("/api/auth/logout", { method: "POST" });
    if (!response.ok) throw await response.json().catch(() => ({ detail: "Logout failed" }));
    return response.json();
  },

  me: async () => {
    const response = await fetch("/api/auth/session", { cache: "no-store" });
    const session = await response.json();
    if (!session.authenticated) throw new Error("Not authenticated");
    return session.me;
  },
};
