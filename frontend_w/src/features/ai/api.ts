"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";
import type {
  AiMastery, AiWeakTopic, AiRecommendation, AiStudyPlan, MasteryBand,
} from "@/lib/types";

export const BAND_LABEL: Record<MasteryBand, string> = {
  mastered: "Mastered",
  proficient: "Proficient",
  developing: "Developing",
  beginner: "Beginner",
};

// Tailwind background classes keyed by band (used by heatmap + chips).
export const BAND_BG: Record<MasteryBand, string> = {
  mastered: "bg-emerald-500",
  proficient: "bg-cyan-600",
  developing: "bg-amber-500",
  beginner: "bg-rose-500",
};

export function masteryColor(mastery: number): string {
  if (mastery >= 80) return "bg-emerald-500";
  if (mastery >= 60) return "bg-cyan-600";
  if (mastery >= 35) return "bg-amber-500";
  if (mastery > 0) return "bg-rose-500";
  return "bg-slate-300 dark:bg-slate-700";
}

export function useMastery() {
  return useQuery({
    queryKey: ["ai-mastery"],
    queryFn: async () => (await apiClient.get<AiMastery>("/api/ai/mastery/")).data,
  });
}

export function useWeakTopics() {
  return useQuery({
    queryKey: ["ai-weak-topics"],
    queryFn: async () => (await apiClient.get<AiWeakTopic[]>("/api/ai/weak-topics/")).data,
  });
}

export function useRecommendations() {
  return useQuery({
    queryKey: ["ai-recommendations"],
    queryFn: async () => (await apiClient.get<AiRecommendation[]>("/api/ai/recommendations/")).data,
  });
}

export function useStudyPlan() {
  return useQuery({
    queryKey: ["ai-study-plan"],
    queryFn: async () => {
      const data = (await apiClient.get<AiStudyPlan | { plan: null }>("/api/ai/study-plan/")).data;
      return "sessions" in data ? (data as AiStudyPlan) : null;
    },
  });
}

export function useGeneratePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await apiClient.post("/api/ai/generate-plan/")).data,
    onSuccess: () => {
      ["ai-mastery", "ai-weak-topics", "ai-recommendations", "ai-study-plan"].forEach((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      );
    },
  });
}
