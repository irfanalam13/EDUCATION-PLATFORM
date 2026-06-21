"use client";

import React from "react";
import { useRouter } from "next/navigation";

export default function BackButton({ fallbackHref }: { fallbackHref: string }) {
  const router = useRouter();
  return (
    <button
      className="rounded-lg border px-3 py-2 text-sm hover:bg-black/5"
      onClick={() => router.back()}
      type="button"
      title="Go back"
    >
      ← Back
    </button>
  );
}
