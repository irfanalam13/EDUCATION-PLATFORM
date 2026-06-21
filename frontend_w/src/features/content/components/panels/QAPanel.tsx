"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Answer, QuestionThread } from "../../types/content.types";

export default function QAPanel({ topicId }: { topicId: number }) {
  const [questions, setQuestions] = useState<QuestionThread[]>([]);
  const [selected, setSelected] = useState<QuestionThread | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);

  const [qTitle, setQTitle] = useState("");
  const [qBody, setQBody] = useState("");
  const [aBody, setABody] = useState("");

  async function loadQuestions() {
    const q = await contentClient.listQuestions({ topic: topicId });
    setQuestions(q);
    if (!selected && q.length) setSelected(q[0]);
  }

  async function loadAnswers(questionId: number) {
    const a = await contentClient.listAnswers({ question: questionId });
    setAnswers(a);
  }

  useEffect(() => {
    loadQuestions();
  }, [topicId]);

  useEffect(() => {
    if (selected?.id) loadAnswers(selected.id);
  }, [selected?.id]);

  async function ask() {
    if (!qTitle.trim() || !qBody.trim()) return;
    const created = await contentClient.createQuestion({ topic: topicId, title: qTitle, body: qBody });
    setQTitle("");
    setQBody("");
    await loadQuestions();
    setSelected(created);
  }

  async function answer() {
    if (!selected?.id || !aBody.trim()) return;
    await contentClient.createAnswer({ question: selected.id, body: aBody });
    setABody("");
    await loadAnswers(selected.id);
  }

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Questions</div>
        <div className="grid gap-2">
          {questions.map((q) => (
            <button
              key={q.id}
              onClick={() => setSelected(q)}
              className={`text-left rounded-lg border p-3 hover:bg-gray-50 ${
                selected?.id === q.id ? "bg-gray-50" : ""
              }`}
            >
              <div className="font-medium text-sm">{q.title}</div>
              <div className="text-xs text-gray-500 line-clamp-2">{q.body}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="md:col-span-2 space-y-4">
        <div className="rounded-xl border p-4 space-y-2">
          <div className="font-semibold">Ask a question</div>
          <input
            className="w-full rounded-lg border p-2 text-sm"
            placeholder="Title"
            value={qTitle}
            onChange={(e) => setQTitle(e.target.value)}
          />
          <textarea
            className="w-full rounded-lg border p-2 text-sm"
            placeholder="Details"
            value={qBody}
            onChange={(e) => setQBody(e.target.value)}
          />
          <button onClick={ask} className="rounded-lg bg-black text-white px-4 py-2 text-sm">
            Post
          </button>
        </div>

        <div className="rounded-xl border p-4 space-y-3">
          {!selected ? (
            <div className="text-sm text-gray-600">Select a question to view answers.</div>
          ) : (
            <>
              <div>
                <div className="font-semibold">{selected.title}</div>
                <div className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{selected.body}</div>
              </div>

              <div className="space-y-2">
                <div className="font-semibold">Answers</div>
                {answers.map((a) => (
                  <div key={a.id} className="rounded-lg border p-3 text-sm whitespace-pre-wrap">
                    {a.body}
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <textarea
                  className="w-full rounded-lg border p-2 text-sm"
                  placeholder="Write an answer..."
                  value={aBody}
                  onChange={(e) => setABody(e.target.value)}
                />
                <button onClick={answer} className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50">
                  Submit Answer
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
