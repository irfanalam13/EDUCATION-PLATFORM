"use client";

import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatPercent } from "@/lib/utils";
import type { MasteryBand } from "@/lib/types";
import {
  useMastery, useWeakTopics, useRecommendations, useGeneratePlan, BAND_LABEL, BAND_BG,
} from "../api";

const BANDS: MasteryBand[] = ["mastered", "proficient", "developing", "beginner"];
const KIND_CHIP: Record<string, string> = {
  practice: "bg-cyan-100 text-cyan-800 dark:bg-cyan-950/50 dark:text-cyan-300",
  revise: "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300",
  learn: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300",
  prerequisite: "bg-violet-100 text-violet-800 dark:bg-violet-950/50 dark:text-violet-300",
};

export function AiDashboard() {
  const mastery = useMastery();
  const weak = useWeakTopics();
  const recs = useRecommendations();
  const generate = useGeneratePlan();

  const dist = mastery.data?.band_distribution;
  const totalTopics = mastery.data?.topics.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Your AI study coach analyzes mastery, accuracy, and memory decay to tell you exactly what to study next.
        </p>
        <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
          {generate.isPending ? "Analyzing…" : "Regenerate plan"}
        </Button>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-5">
          <div className="text-sm text-muted">Overall mastery</div>
          <div className="mt-2 text-3xl font-semibold">{formatPercent(mastery.data?.overall_mastery ?? 0)}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Topics tracked</div>
          <div className="mt-2 text-3xl font-semibold">{totalTopics}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Weak topics</div>
          <div className="mt-2 text-3xl font-semibold">{weak.data?.length ?? 0}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Recommendations</div>
          <div className="mt-2 text-3xl font-semibold">{recs.data?.length ?? 0}</div>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Mastery distribution</h2>
            <Link href="/ai/mastery" className="text-sm text-cyan-700 hover:underline">Mastery map →</Link>
          </div>
          <div className="mt-4 space-y-3">
            {BANDS.map((b) => {
              const count = dist?.[b] ?? 0;
              const pct = totalTopics ? Math.round((count / totalTopics) * 100) : 0;
              return (
                <div key={b}>
                  <div className="flex justify-between text-sm">
                    <span>{BAND_LABEL[b]}</span>
                    <span className="text-muted">{count}</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className={`h-full rounded-full ${BAND_BG[b]}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Top recommendations</h2>
            <Link href="/ai/recommendations" className="text-sm text-cyan-700 hover:underline">View all →</Link>
          </div>
          <div className="mt-4 space-y-3">
            {recs.isLoading ? (
              <div className="text-sm text-muted">Loading…</div>
            ) : (recs.data?.length ?? 0) === 0 ? (
              <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">
                No recommendations yet — click <span className="font-medium">Regenerate plan</span>.
              </div>
            ) : (
              recs.data!.slice(0, 4).map((r) => (
                <div key={r.id} className="rounded-md border border-app p-3">
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${KIND_CHIP[r.kind] ?? ""}`}>{r.kind}</span>
                    <span className="text-sm font-medium">{r.title}</span>
                  </div>
                  {r.message ? <p className="mt-1 text-xs text-muted">{r.message}</p> : null}
                </div>
              ))
            )}
          </div>
        </Card>
      </section>

      <section className="flex flex-wrap gap-3">
        <Link href="/ai/study-plan"><Button variant="secondary">Today&apos;s study plan</Button></Link>
        <Link href="/ai/weak-topics"><Button variant="secondary">Weak topics</Button></Link>
      </section>
    </div>
  );
}
