"use client";

import { useMemo } from "react";

import { Card } from "@/components/ui/Card";
import { formatPercent } from "@/lib/utils";
import type { AiMasteryTopic, MasteryBand } from "@/lib/types";
import { useMastery, masteryColor, BAND_LABEL, BAND_BG } from "../api";

const BANDS: MasteryBand[] = ["mastered", "proficient", "developing", "beginner"];

export function MasteryMap() {
  const mastery = useMastery();

  const bySubject = useMemo(() => {
    const groups: Record<string, AiMasteryTopic[]> = {};
    (mastery.data?.topics ?? []).forEach((t) => {
      const key = t.subject || "Other";
      (groups[key] ||= []).push(t);
    });
    return groups;
  }, [mastery.data]);

  if (mastery.isLoading) return <div className="text-sm text-muted">Building your mastery map…</div>;
  if (mastery.isError || !mastery.data) return <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">Unable to load mastery.</div>;

  const topics = mastery.data.topics;
  if (!topics.length) {
    return <Card className="p-10 text-center text-sm text-muted">No topic mastery yet — take a few quizzes to populate your map.</Card>;
  }

  const dist = mastery.data.band_distribution;

  return (
    <div className="space-y-6">
      {/* Legend + band distribution */}
      <Card className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Overall mastery {formatPercent(mastery.data.overall_mastery)}</h2>
          <div className="flex flex-wrap gap-3 text-xs">
            {BANDS.map((b) => (
              <span key={b} className="inline-flex items-center gap-1.5">
                <span className={`inline-block h-3 w-3 rounded ${BAND_BG[b]}`} />
                {BAND_LABEL[b]} ({dist?.[b] ?? 0})
              </span>
            ))}
          </div>
        </div>
      </Card>

      {/* Per-subject average (radar substitute: horizontal bars) */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold">Subject strength</h2>
        <div className="mt-4 space-y-3">
          {Object.entries(bySubject).map(([subject, ts]) => {
            const avg = ts.reduce((a, t) => a + t.mastery, 0) / ts.length;
            return (
              <div key={subject}>
                <div className="flex justify-between text-sm">
                  <span>{subject}</span>
                  <span className="text-muted">{formatPercent(avg)}</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div className={`h-full rounded-full ${masteryColor(avg)}`} style={{ width: `${Math.round(avg)}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Heatmap: one cell per topic, colored by mastery, grouped by subject */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold">Topic heatmap</h2>
        <div className="mt-4 space-y-5">
          {Object.entries(bySubject).map(([subject, ts]) => (
            <div key={subject}>
              <div className="mb-2 text-sm font-medium text-muted">{subject}</div>
              <div className="flex flex-wrap gap-1.5">
                {ts.map((t) => (
                  <div
                    key={t.topic_id}
                    title={`${t.topic_title} — ${formatPercent(t.mastery)} (${BAND_LABEL[t.band]})`}
                    className={`h-9 w-9 rounded ${masteryColor(t.mastery)}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
