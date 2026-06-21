"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useRecommendations, useGeneratePlan } from "../api";

const KIND_CHIP: Record<string, string> = {
  practice: "bg-cyan-100 text-cyan-800 dark:bg-cyan-950/50 dark:text-cyan-300",
  revise: "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300",
  learn: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300",
  prerequisite: "bg-violet-100 text-violet-800 dark:bg-violet-950/50 dark:text-violet-300",
};

export function RecommendationsList() {
  const recs = useRecommendations();
  const generate = useGeneratePlan();

  if (recs.isLoading) return <div className="text-sm text-muted">Loading recommendations…</div>;
  if (recs.isError) return <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">Unable to load recommendations.</div>;

  if (!recs.data?.length) {
    return (
      <Card className="p-10 text-center">
        <p className="text-sm text-muted">No recommendations yet.</p>
        <div className="mt-4">
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? "Analyzing…" : "Generate recommendations"}
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <ul className="space-y-3">
      {recs.data.map((r) => (
        <li key={r.id}>
          <Card className="flex items-start justify-between gap-4 p-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-xs font-medium ${KIND_CHIP[r.kind] ?? ""}`}>{r.kind}</span>
                <span className="text-sm font-medium">{r.title}</span>
              </div>
              {r.message ? <p className="mt-1 text-sm text-muted">{r.message}</p> : null}
            </div>
            <span className="shrink-0 text-xs text-muted">priority {r.priority}</span>
          </Card>
        </li>
      ))}
    </ul>
  );
}
