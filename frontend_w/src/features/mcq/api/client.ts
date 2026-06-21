import { api } from "@/shared/lib/http";
import type { MCQQuestionDTO } from "./dtos";

export type AttemptResult = {
  is_correct: boolean;
  explanation: string;
};

export const mcqApi = {
  questions(params: { topic: number; difficulty?: string }) {
    const qs = new URLSearchParams({ topic: String(params.topic) });
    if (params.difficulty) qs.set("difficulty", params.difficulty);
    return api<MCQQuestionDTO[]>(`/api/mcq/questions/?${qs.toString()}`);
  },

  attempt(payload: { question_id: number; choice_id: number }) {
    // Requires JWT auth → set auth:true
    return api<AttemptResult>("/api/mcq/attempt/", {
      method: "POST",
      body: payload,
      auth: true,
    });
  },
};
