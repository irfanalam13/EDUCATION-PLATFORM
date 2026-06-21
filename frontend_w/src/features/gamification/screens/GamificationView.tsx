"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient } from "@/lib/api";
import type { GamificationProfile, QuestProgress } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function GamificationView() {
  const qc = useQueryClient();

  const profile = useQuery({
    queryKey: ["gami-profile"],
    queryFn: async () =>
      (await apiClient.get<GamificationProfile>("/api/gamification/gamification/profile/")).data,
  });

  const quests = useQuery({
    queryKey: ["quests"],
    queryFn: async () =>
      (await apiClient.get<QuestProgress[]>("/api/gamification/quests/")).data,
  });

  const claim = useMutation({
    mutationFn: async (code: string) =>
      (await apiClient.post(`/api/gamification/quests/claim/${code}/`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quests"] });
      qc.invalidateQueries({ queryKey: ["gami-profile"] });
    },
  });

  if (profile.isLoading) {
    return <div className="text-sm text-muted">Loading your achievements…</div>;
  }
  if (profile.isError || !profile.data) {
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        Unable to load gamification data right now.
      </div>
    );
  }

  const p = profile.data;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-5">
          <div className="text-sm text-muted">Level</div>
          <div className="mt-2 text-3xl font-semibold">{p.level}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Total XP</div>
          <div className="mt-2 text-3xl font-semibold">{p.total_xp.toLocaleString()}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Current streak</div>
          <div className="mt-2 text-3xl font-semibold">{p.streak_days} 🔥</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Longest streak</div>
          <div className="mt-2 text-3xl font-semibold">{p.longest_streak} days</div>
        </Card>
      </section>

      <Card className="p-6">
        <h2 className="text-lg font-semibold">Badges</h2>
        {p.badges.length === 0 ? (
          <div className="mt-4 rounded-md border border-dashed border-app p-6 text-center text-sm text-muted">
            No badges yet. Earn XP, keep a streak, and they&apos;ll start unlocking.
          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {p.badges.map((ub) => (
              <div key={ub.id} className="flex items-center gap-3 rounded-md border border-app p-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-100 text-xl dark:bg-amber-950/40">
                  🏅
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{ub.badge.name}</div>
                  <div className="text-xs text-muted">Earned {formatDate(ub.awarded_at)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-semibold">Quests</h2>
        {quests.isLoading ? (
          <div className="mt-4 text-sm text-muted">Loading quests…</div>
        ) : !quests.data || quests.data.length === 0 ? (
          <div className="mt-4 rounded-md border border-dashed border-app p-6 text-center text-sm text-muted">
            No active quests right now. Check back soon.
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {quests.data.map((q) => {
              const target = Number((q.quest.rules as { target?: number })?.target ?? 0);
              const pct = target > 0 ? Math.min(100, Math.round((q.progress / target) * 100)) : q.is_completed ? 100 : 0;
              return (
                <div key={q.id} className="rounded-md border border-app p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{q.quest.name}</div>
                      <div className="truncate text-xs text-muted">{q.quest.description}</div>
                    </div>
                    {q.is_completed && !q.is_claimed ? (
                      <Button
                        onClick={() => claim.mutate(q.quest.code)}
                        disabled={claim.isPending}
                      >
                        {claim.isPending ? "Claiming…" : "Claim"}
                      </Button>
                    ) : q.is_claimed ? (
                      <span className="text-xs font-medium text-emerald-600">Claimed ✓</span>
                    ) : null}
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className="h-full rounded-full bg-cyan-700" style={{ width: `${pct}%` }} />
                  </div>
                  {target > 0 && (
                    <div className="mt-1 text-right text-xs text-muted">
                      {q.progress}/{target}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
