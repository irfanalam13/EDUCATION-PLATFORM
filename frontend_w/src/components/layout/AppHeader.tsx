"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { ThemeToggle } from "./ThemeToggle";
import { Button } from "../ui/Button";
import { apiClient } from "@/lib/api";
import type { SessionUser } from "@/lib/types";
import { cn } from "@/lib/utils";


const navItems = [
  { href: "/", label: "Home" },
  { href: "/academics", label: "Learn" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/content/notes", label: "Notes" },
  { href: "/quiz", label: "Quiz" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/badges", label: "Achievements" },
  { href: "/ai", label: "AI Coach" },
  { href: "/assistant", label: "AI Chat" },
];

type SessionResponse = { authenticated: boolean; me?: SessionUser };

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const session = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const response = await fetch("/api/auth/session", { cache: "no-store" });
      return (await response.json()) as SessionResponse;
    },
  });

  const user = session.data?.me;

  const unread = useQuery({
    queryKey: ["notifications-unread"],
    enabled: Boolean(user),
    refetchInterval: 60_000,
    queryFn: async () =>
      (await apiClient.get<{ unread: number }>("/api/notifications/notifications/unread-count/")).data,
  });
  const unreadCount = unread.data?.unread ?? 0;

  return (
    <header className="border-b border-app bg-app/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            EduPlatform
          </Link>

          <nav className="hidden items-center gap-5 md:flex">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-sm transition hover:text-cyan-700",
                  pathname === item.href ? "font-semibold text-cyan-700" : "text-muted",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          {user ? (
            <>
              <Link
                href="/notifications"
                aria-label={`Notifications${unreadCount ? ` (${unreadCount} unread)` : ""}`}
                className="relative inline-flex h-10 w-10 items-center justify-center rounded-md border border-app bg-card hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <span aria-hidden className="text-base">🔔</span>
                {unreadCount > 0 && (
                  <span className="absolute -right-1 -top-1 inline-flex min-w-[18px] items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-semibold text-white">
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </span>
                )}
              </Link>
              <div className="hidden text-right sm:block">
                <div className="text-sm font-medium">{user.first_name || user.username}</div>
                <div className="text-xs uppercase tracking-wide text-muted">{user.role}</div>
              </div>
              <Button
                variant="secondary"
                onClick={async () => {
                  await fetch("/api/auth/logout", { method: "POST" });
                  router.push("/login");
                  router.refresh();
                }}
              >
                Sign out
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="secondary">Sign in</Button>
              </Link>
              <Link href="/signup" className="hidden sm:block">
                <Button>Create account</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
