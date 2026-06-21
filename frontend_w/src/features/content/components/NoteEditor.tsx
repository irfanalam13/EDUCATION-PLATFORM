"use client";

import { useState } from "react";
import { contentClient } from "../api/content.client";

export default function NoteEditor({ topicId, onCreated }: { topicId: number; onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<"private" | "unlisted" | "public">("private");
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!title.trim()) return;
    setLoading(true);
    try {
      await contentClient.createNote({
        topic: topicId,
        title,
        content_richtext: content,
        visibility,
      });
      setTitle("");
      setContent("");
      onCreated();
    } catch (e: any) {
      alert(e?.message || "Failed to create note");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="font-semibold">Create Note</div>

      <input
        className="w-full rounded-lg border p-2"
        placeholder="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <textarea
        className="w-full rounded-lg border p-2 min-h-[120px]"
        placeholder="Write note..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />

      <div className="flex items-center gap-2">
        <select
          className="rounded-lg border p-2 text-sm"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as any)}
        >
          <option value="private">Private</option>
          <option value="unlisted">Unlisted</option>
          <option value="public">Public</option>
        </select>

        <button
          onClick={submit}
          disabled={loading}
          className="ml-auto rounded-lg bg-black text-white px-4 py-2 text-sm disabled:opacity-50"
        >
          {loading ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );
}
