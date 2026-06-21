"use client";

import React from "react";

export default function Pagination({
  page,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
}: {
  page: number;
  hasPrev: boolean;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="mt-6 flex items-center justify-between gap-3">
      <button
        className="border rounded-md px-4 py-2"
        disabled={!hasPrev}
        onClick={onPrev}
      >
        ← Previous
      </button>

      <div className="text-sm opacity-70">Page {page}</div>

      <button
        className="border rounded-md px-4 py-2 "
        disabled={!hasNext}
        onClick={onNext}
      >
        Next →
      </button>
    </div>
  );
}
