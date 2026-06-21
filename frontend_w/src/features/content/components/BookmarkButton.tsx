"use client";

import { useState } from "react";
import { contentClient } from "../api/content.client";

export default function BookmarkButton({
  entityAppLabel = "content",
  entityModel,
  entityId,
}: {
  entityAppLabel?: string;
  entityModel: string; // "note" | "topic" | "attachment" etc
  entityId: number;
}) {
  const [loading, setLoading] = useState(false);

  async function add() {
    setLoading(true);
    try {
      await contentClient.addBookmark({
        entity_app_label: entityAppLabel,
        entity_model: entityModel,
        entity_id: entityId,
      });
      alert("Bookmarked!");
    } catch (e: any) {
      alert(e?.message || "Failed to bookmark");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={add}
      disabled={loading}
      className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50"
      title="Bookmark"
    >
      {loading ? "..." : "Bookmark"}
    </button>
  );
}
