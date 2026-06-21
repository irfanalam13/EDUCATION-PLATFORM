"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { apiClient } from "@/lib/api";
import type { LeaderboardEntry, LeaderboardMe, SessionUser } from "@/lib/types";
import { cn } from "@/lib/utils";

const PERIODS = [
  { key: "weekly", label: "This week" },
  { key: "monthly", label: "This month" },
  { key: "all_time", label: "All time" },
] as const;

type Period = (typeof PERIODS)[number]["key"];

export function LeaderboardView() {
  const [period, setPeriod] = useState<Period>("weekly");

  const session = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const res = await fetch("/api/auth/session", { cache: "no-store" });
      return (await res.json()) as { authenticated: boolean; me?: SessionUser };
    },
  });

  const board = useQuery({
    queryKey: ["leaderboard", period],
    queryFn: async () =>
      (
        await apiClient.get<LeaderboardEntry[]>("/api/gamification/leaderboards/", {
          params: { scope: "global", period, limit: 50 },
        })
      ).data,
  });

  const me = useQuery({
    queryKey: ["leaderboard-me", period],
    queryFn: async () =>
      (
        await apiClient.get<LeaderboardMe>("/api/gamification/leaderboards/me/", {
          params: { scope: "global", period },
        })
      ).data,
  });

  const myId = session.data?.me?.id;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-md border border-app bg-card p-1" role="tablist" aria-label="Leaderboard period">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              role="tab"
              aria-selected={period === p.key}
              onClick={() => setPeriod(p.key)}
              className={cn(
                "rounded px-3 py-1.5 text-sm transition",
                period === p.key ? "bg-cyan-700 text-white" : "text-muted hover:text-inherit",
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
        {me.data?.rank_in_top200 ? (
          <div className="text-sm text-muted">
            Your rank: <span className="font-semibold text-inherit">#{me.data.rank_in_top200}</span>
          </div>
        ) : (
          <div className="text-sm text-muted">You&apos;re not ranked yet — earn XP to join.</div>
        )}
      </div>

      <Card className="p-2 sm:p-4">
        {board.isLoading ? (
          <div className="p-6 text-sm text-muted">Loading leaderboard…</div>
        ) : board.isError ? (
          <div className="m-2 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40">
            Unable to load the leaderboard right now.
          </div>
        ) : !board.data || board.data.length === 0 ? (
          <div className="m-2 rounded-md border border-dashed border-app p-6 text-center text-sm text-muted">
            No rankings for this period yet. Finish a quiz to earn XP and appear here.
          </div>
        ) : (
          <ol className="divide-y divide-app">
            {board.data.map((entry, idx) => {
              const isMe = entry.user_id === myId;
              const rank = idx + 1;
              return (
                <li
                  key={entry.user_id}
                  className={cn(
                    "flex items-center gap-4 px-3 py-3",
                    isMe && "rounded-md bg-cyan-50 dark:bg-cyan-950/30",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                      rank === 1 && "bg-amber-400 text-amber-950",
                      rank === 2 && "bg-slate-300 text-slate-800",
                      rank === 3 && "bg-orange-300 text-orange-950",
                      rank > 3 && "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
                    )}
                  >
                    {rank}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {entry.display_name || entry.username}
                      {isMe && <span className="ml-2 text-xs text-cyan-700">You</span>}
                    </div>
                  </div>
                  <div className="text-sm font-semibold tabular-nums">{entry.xp_total.toLocaleString()} XP</div>
                </li>
              );
            })}
          </ol>
        )}
      </Card>
    </div>
  );
}
