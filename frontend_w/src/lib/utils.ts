export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function formatPercent(value: number | null | undefined) {
  const safe = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${Math.round(safe)}%`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "Not yet";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
