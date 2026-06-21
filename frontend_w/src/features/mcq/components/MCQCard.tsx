"use client";

import React from "react";
import Card from "@/shared/ui/Card";
import type { MCQQuestionDTO } from "../api/dtos";
import { mcqApi } from "../api/client";

export default function MCQCard({
  q,
  index,
  onResult,
  maxRetries = 3,
}: {
  q: MCQQuestionDTO;
  index: number;
  onResult: (payload: { questionId: number; isCorrect: boolean }) => void;
  maxRetries?: number;
}) {
  const [selected, setSelected] = React.useState<number | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [result, setResult] = React.useState<null | { is_correct: boolean; explanation: string }>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [tries, setTries] = React.useState(0);

  const canRetry = tries < maxRetries && result?.is_correct === false;

  const submit = async () => {
    if (selected == null) return;
    setSubmitting(true);
    setError(null);

    try {
      const res = await mcqApi.attempt({ question_id: q.id, choice_id: selected });
      setResult(res);
      setTries((v) => v + 1);
      onResult({ questionId: q.id, isCorrect: res.is_correct });
    } catch (e: any) {
      setError(e?.message ?? "Submit failed. Are you logged in?");
    } finally {
      setSubmitting(false);
    }
  };

  const retry = () => {
    setSelected(null);
    setResult(null);
    setError(null);
  };

  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <div className="font-medium">Q{index + 1}</div>
        <div className="flex items-center gap-2">
          <span className="text-xs rounded-full border px-2 py-1 opacity-70">{q.difficulty}</span>
          <span className="text-xs rounded-full border px-2 py-1 opacity-70">
            Try {tries}/{maxRetries}
          </span>
        </div>
      </div>

      <p className="mt-3 whitespace-pre-wrap">{q.question_text}</p>

      <div className="mt-4 space-y-2">
        {q.choices.map((c) => {
          const active = selected === c.id;
          const disabled = submitting || !!result;
          return (
            <button
              key={c.id}
              type="button"
              disabled={disabled}
              onClick={() => setSelected(c.id)}
              className={`w-full text-left rounded-lg border px-3 py-2 text-sm transition disabled:opacity-60 ${
                active ? "bg-black text-white" : "hover:bg-black/5"
              }`}
            >
              {c.choice_text}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 items-center">
        <button
          className="rounded-lg bg-black text-white px-4 py-2 text-sm "
          disabled={selected === null || submitting || !!result}
          onClick={submit}
        >
          {submitting ? "Submitting..." : "Submit"}
        </button>

        <button
          className="rounded-lg border px-4 py-2 text-sm hover:bg-black/5"
          onClick={() => {
            setSelected(null);
            setResult(null);
            setError(null);
            setTries(0);
          }}
          type="button"
        >
          Reset
        </button>

        {result && canRetry ? (
          <button className="rounded-lg border px-4 py-2 text-sm hover:bg-black/5" onClick={retry} type="button">
            Try again
          </button>
        ) : null}

        {error ? <span className="text-sm text-red-600">{error}</span> : null}
      </div>

      {result ? (
        <div className="mt-4 rounded-xl border p-4">
          <div className={`font-medium ${result.is_correct ? "text-green-700" : "text-red-700"}`}>
            {result.is_correct ? "✅ Correct" : "❌ Wrong"}
          </div>
          {result.explanation ? (
            <p className="mt-2 text-sm opacity-80 whitespace-pre-wrap">{result.explanation}</p>
          ) : (
            <p className="mt-2 text-sm opacity-60">No explanation provided.</p>
          )}

          {!result.is_correct && tries >= maxRetries ? (
            <p className="mt-3 text-sm text-red-700">
              Retry limit reached for this question.
            </p>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}
