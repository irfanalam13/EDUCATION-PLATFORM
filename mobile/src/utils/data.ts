import type { Paginated } from "@/types/api";

export function unwrapList<T>(payload: T[] | Paginated<T> | { results?: T[] }): T[] {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

export function formatPercent(value: number | null | undefined) {
  const safe = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${Math.round(safe)}%`;
}

export function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
