"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient, unwrapList } from "@/lib/api";
import type { McqQuestion } from "@/lib/types";


export function QuizPlayer({ topicId }: { topicId: number }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState<Record<number, boolean>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  const questions = useQuery({
    queryKey: ["mcq-questions", topicId],
    queryFn: async () =>
      unwrapList(
        (await apiClient.get<McqQuestion[] | { results: McqQuestion[] }>("/api/assessment/mcq/questions/", { params: { topic: topicId } })).data,
      ),
  });

  const answer = useMutation({
    mutationFn: async ({ questionId, choiceId }: { questionId: number; choiceId: number }) =>
      (await apiClient.post<{ is_correct: boolean }>(`/api/assessment/mcq/questions/${questionId}/answer/`, { choice_id: choiceId })).data,
    onSuccess: (data, variables) => {
      setAnswered((prev) => ({ ...prev, [variables.questionId]: true }));
      if (data.is_correct) {
        setScore((value) => value + 1);
      }
      setFeedback(data.is_correct ? "Correct answer." : "Not quite. Review the concept and try the next one.");
    },
  });

  const currentQuestion = useMemo(() => questions.data?.[currentIndex], [questions.data, currentIndex]);

  if (questions.isLoading) {
    return <div className="text-sm text-muted">Loading quiz...</div>;
  }

  if (!questions.data?.length) {
    return <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">No MCQs are available for this topic yet.</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm text-muted">Topic #{topicId}</div>
            <h1 className="mt-1 text-2xl font-semibold">Practice quiz</h1>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted">Score</div>
            <div className="text-2xl font-semibold">
              {score}/{questions.data.length}
            </div>
          </div>
        </div>
      </Card>

      {currentQuestion ? (
        <Card className="p-6">
          <div className="text-sm text-muted">
            Question {currentIndex + 1} of {questions.data.length} • {currentQuestion.difficulty}
          </div>
          <h2 className="mt-3 text-xl font-semibold">{currentQuestion.question_text}</h2>

          <div className="mt-6 space-y-3">
            {currentQuestion.choices.map((choice) => (
              <button
                key={choice.id}
                className={`w-full rounded-md border p-4 text-left text-sm transition ${
                  selectedChoiceId === choice.id ? "border-cyan-700 bg-cyan-50 dark:bg-cyan-950/40" : "border-app hover:border-cyan-700"
                }`}
                onClick={() => setSelectedChoiceId(choice.id)}
                type="button"
              >
                {choice.choice_text}
              </button>
            ))}
          </div>

          {feedback ? <div className="mt-4 rounded-md border border-app bg-slate-50 p-3 text-sm text-muted dark:bg-slate-900">{feedback}</div> : null}

          <div className="mt-6 flex items-center justify-between gap-3">
            <Button
              variant="secondary"
              disabled={currentIndex === 0}
              onClick={() => {
                setCurrentIndex((value) => Math.max(0, value - 1));
                setSelectedChoiceId(null);
                setFeedback(null);
              }}
            >
              Previous
            </Button>

            {!answered[currentQuestion.id] ? (
              <Button
                disabled={!selectedChoiceId || answer.isPending}
                onClick={() =>
                  selectedChoiceId && answer.mutate({ questionId: currentQuestion.id, choiceId: selectedChoiceId })
                }
              >
                {answer.isPending ? "Checking..." : "Submit answer"}
              </Button>
            ) : (
              <Button
                onClick={() => {
                  setCurrentIndex((value) => Math.min(questions.data.length - 1, value + 1));
                  setSelectedChoiceId(null);
                  setFeedback(null);
                }}
              >
                {currentIndex === questions.data.length - 1 ? "Review quiz" : "Next question"}
              </Button>
            )}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
