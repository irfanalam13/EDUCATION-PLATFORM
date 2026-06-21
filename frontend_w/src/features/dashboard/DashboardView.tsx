"use client";

import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { apiClient } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";
import { formatDate, formatPercent } from "@/lib/utils";


export function DashboardView() {
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await apiClient.get<DashboardPayload>("/api/progress/dashboard/")).data,
  });

  if (dashboard.isLoading) {
    return <div className="text-sm text-muted">Loading your dashboard...</div>;
  }

  if (dashboard.isError || !dashboard.data) {
    return <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">Unable to load dashboard data right now.</div>;
  }

  const data = dashboard.data;
  const accuracy = data.totals.total_answered
    ? (data.totals.correct / data.totals.total_answered) * 100
    : 0;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-5">
          <div className="text-sm text-muted">Topics tracked</div>
          <div className="mt-2 text-3xl font-semibold">{data.totals.topics}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Average mastery</div>
          <div className="mt-2 text-3xl font-semibold">{formatPercent(data.totals.avg_mastery)}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Accuracy</div>
          <div className="mt-2 text-3xl font-semibold">{formatPercent(accuracy)}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Current streak</div>
          <div className="mt-2 text-3xl font-semibold">{data.streak.current_streak} days</div>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="p-6">
          <h2 className="text-lg font-semibold">Study momentum</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-app p-4">
              <div className="text-xs uppercase tracking-wide text-muted">Today</div>
              <div className="mt-2 text-2xl font-semibold">{data.today.minutes} min</div>
              <div className="text-sm text-muted">{data.today.attempted} attempts logged</div>
            </div>
            <div className="rounded-md border border-app p-4">
              <div className="text-xs uppercase tracking-wide text-muted">Goal</div>
              <div className="mt-2 text-2xl font-semibold">{data.goals.daily_minutes_goal} min</div>
              <div className="text-sm text-muted">{data.goals.daily_attempt_goal} practice target</div>
            </div>
            <div className="rounded-md border border-app p-4">
              <div className="text-xs uppercase tracking-wide text-muted">Best streak</div>
              <div className="mt-2 text-2xl font-semibold">{data.streak.best_streak} days</div>
              <div className="text-sm text-muted">Last active {formatDate(data.streak.last_active_date)}</div>
            </div>
          </div>

          <div className="mt-6">
            <div className="text-sm font-medium">Last 7 days</div>
            <div className="mt-4 grid grid-cols-7 gap-2">
              {data.activity_7d.map((item) => {
                const height = Math.max(18, Math.min(100, item.minutes * 2));
                return (
                  <div key={item.date} className="space-y-2 text-center">
                    <div className="flex h-28 items-end justify-center rounded-md bg-slate-100 px-2 dark:bg-slate-900">
                      <div className="w-full rounded-sm bg-cyan-700" style={{ height: `${height}%` }} />
                    </div>
                    <div className="text-xs text-muted">{new Date(item.date).toLocaleDateString(undefined, { weekday: "short" })}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold">Review queue</h2>
          <div className="mt-4 space-y-3">
            {data.due_topics.length ? (
              data.due_topics.map((topic) => (
                <div key={topic.topic} className="rounded-md border border-app p-4">
                  <div className="text-sm font-medium">Topic #{topic.topic}</div>
                  <div className="mt-1 text-sm text-muted">Mastery {formatPercent(topic.mastery)} • Accuracy {formatPercent(topic.accuracy * 100)}</div>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">No due reviews yet. Keep practicing and the queue will fill in naturally.</div>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
