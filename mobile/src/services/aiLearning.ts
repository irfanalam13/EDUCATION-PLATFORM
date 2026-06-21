import { apiRequest } from "./api";
import type {
  AiMastery, AiWeakTopic, AiRecommendation, AiStudyPlan,
} from "@/types/api";

export const getMastery = () => apiRequest<AiMastery>("/api/ai/mastery/");
export const getWeakTopics = () => apiRequest<AiWeakTopic[]>("/api/ai/weak-topics/");
export const getRecommendations = () => apiRequest<AiRecommendation[]>("/api/ai/recommendations/");

export async function getStudyPlan(): Promise<AiStudyPlan | null> {
  const data = await apiRequest<AiStudyPlan | { plan: null }>("/api/ai/study-plan/");
  return "sessions" in data ? (data as AiStudyPlan) : null;
}

export const generatePlan = () =>
  apiRequest<{ ok: boolean; weak_topics: number; recommendations: number }>(
    "/api/ai/generate-plan/",
    { method: "POST" },
  );
