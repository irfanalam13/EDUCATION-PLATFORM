"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { formatPercent } from "@/lib/utils";
import { useWeakTopics, useGeneratePlan, BAND_LABEL, BAND_BG } from "../api";

export function WeakTopicsList() {
  const weak = useWeakTopics();
  const generate = useGeneratePlan();

  if (weak.isLoading) return <div className="text-sm text-muted">Analyzing weak topics…</div>;
  if (weak.isError) return <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">Unable to load weak topics.</div>;

  if (!weak.data?.length) {
    return (
      <Card className="p-10 text-center">
        <p className="text-sm text-muted">No weak topics detected — great work, or generate an analysis.</p>
        <div className="mt-4">
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? "Analyzing…" : "Run analysis"}
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {weak.data.map((w) => (
        <Card key={w.topic} className="p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">{w.topic_title}</span>
                <span className={`rounded px-2 py-0.5 text-[11px] font-medium text-white ${BAND_BG[w.band]}`}>
                  {BAND_LABEL[w.band]}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted">{w.reason}</p>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-lg font-semibold text-rose-600">{Math.round(w.weak_score)}</div>
              <div className="text-[11px] text-muted">weakness</div>
            </div>
          </div>
          <div className="mt-3 flex gap-4 text-xs text-muted">
            <span>Mastery {formatPercent(w.mastery)}</span>
            <span>Accuracy {formatPercent(w.accuracy * 100)}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}
