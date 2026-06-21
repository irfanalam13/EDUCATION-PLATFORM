"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useStudyPlan, useGeneratePlan } from "../api";

const ACTIVITY_ICON: Record<string, string> = {
  revision: "📖",
  quiz: "📝",
  practice: "✍️",
  notes: "🗒️",
};

export function StudyPlanView() {
  const plan = useStudyPlan();
  const generate = useGeneratePlan();

  if (plan.isLoading) return <div className="text-sm text-muted">Loading your plan…</div>;

  if (!plan.data) {
    return (
      <Card className="p-10 text-center">
        <p className="text-sm text-muted">No study plan yet. Generate a personalized daily schedule.</p>
        <div className="mt-4">
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? "Building…" : "Generate study plan"}
          </Button>
        </div>
      </Card>
    );
  }

  const p = plan.data;
  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <div className="text-sm text-muted">{p.date}</div>
          <div className="text-lg font-semibold">{p.total_minutes} min planned · {p.sessions.length} blocks</div>
        </div>
        <Button variant="secondary" onClick={() => generate.mutate()} disabled={generate.isPending}>
          {generate.isPending ? "Rebuilding…" : "Rebuild"}
        </Button>
      </Card>

      <ol className="space-y-2">
        {p.sessions.map((s) => (
          <li key={s.id}>
            <Card className="flex items-center gap-4 p-4">
              <div className="w-16 shrink-0 text-sm font-semibold tabular-nums">{s.start_time.slice(0, 5)}</div>
              <div className="text-lg" aria-hidden>{ACTIVITY_ICON[s.activity_type] ?? "•"}</div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{s.title}</div>
                <div className="text-xs text-muted capitalize">{s.activity_type} · {s.duration_min} min</div>
              </div>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}
