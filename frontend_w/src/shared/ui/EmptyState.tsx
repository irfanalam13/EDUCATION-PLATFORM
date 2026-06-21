import React from "react";

export default function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-xl border p-6 text-center">
      <div className="text-lg font-medium">{title}</div>
      {description ? <p className="mt-1 text-sm opacity-70">{description}</p> : null}
    </div>
  );
}
