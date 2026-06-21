"use client";

import React from "react";
import type { MCQQuestionDTO } from "../api/dtos";
import { mcqApi } from "../api/client";
import EmptyState from "@/shared/ui/EmptyState";
import Skeleton from "@/shared/ui/Skeleton";
import MCQCard from "../components/MCQCard";
import MCQScoreSummary from "../components/MCQScoreSummary";

type Difficulty = "" | "easy" | "medium" | "hard";

export default function TopicMCQScreen({
  topicId,
  onXpEarned, // gamification hook (optional)
}: {
  topicId: number;
  onXpEarned?: (xp: number) => void;
}) {
  const [data, setData] = React.useState<MCQQuestionDTO[]>([]);
  const [loading, setLoading] = React.useState(true);

  // ✅ best correctness per question (keeps best score)
  const [bestMap, setBestMap] = React.useState<Record<number, boolean>>({});

  // ✅ difficulty filter
  const [difficulty, setDifficulty] = React.useState<Difficulty>("");

  React.useEffect(() => {
    let mounted = true;
    setLoading(true);

    mcqApi
      .questions({ topic: topicId, difficulty: difficulty || undefined })
      .then((res) => mounted && setData(res))
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [topicId, difficulty]);

  const total = data.length;
  const attemptedUnique = Object.keys(bestMap).length;
  const correct = Object.values(bestMap).filter(Boolean).length;

  // ✅ topic completion status
  const status =
    attemptedUnique === 0
      ? "Not started"
      : attemptedUnique < total
      ? "In progress"
      : "Completed";

  if (loading) {
    return (
      <div className="mt-6 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-4">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-4 w-3/4 mt-3" />
            <Skeleton className="h-10 w-full mt-5" />
          </div>
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return <EmptyState title="No MCQs available" description="Teacher will add questions soon." />;
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm">
          <span className="rounded-full border px-3 py-1">
            Status: <b>{status}</b>
          </span>
          <span className="ml-2 rounded-full border px-3 py-1 opacity-80">
            Attempted: {attemptedUnique}/{total}
          </span>
        </div>

        <select
          className="border rounded-md px-3 py-2 text-sm"
          value={difficulty}
          onChange={(e) => {
            setBestMap({}); // reset bestMap when filter changes (optional)
            setDifficulty(e.target.value as Difficulty);
          }}
        >
          <option value="">All difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      <MCQScoreSummary total={total} correct={correct} />

      {data.map((q, idx) => (
        <MCQCard
          key={q.id}
          q={q}
          index={idx}
          onResult={({ questionId, isCorrect }) => {
            setBestMap((prev) => {
              const prevBest = prev[questionId];
              // keep BEST: if already true, stay true
              const nextBest = Boolean(prevBest) || Boolean(isCorrect);
              return { ...prev, [questionId]: nextBest };
            });

            // ✅ Gamification hook (later you can connect to backend XP)
            // Example: +10 XP for first-time correct (frontend-only for now)
            if (isCorrect) onXpEarned?.(10);
          }}
        />
      ))}
    </div>
  );
}
