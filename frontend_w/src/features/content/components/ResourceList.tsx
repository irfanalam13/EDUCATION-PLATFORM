"use client";

import { useState } from "react";
import type { TopicResource } from "../types/content.types";
import { contentClient } from "../api/content.client";

export default function ResourceList({
  topicId,
  resources,
  onChanged,
}: {
  topicId: number;
  resources: TopicResource[];
  onChanged?: () => void;
}) {
  const [type, setType] = useState<"link" | "video">("link");
  const [url, setUrl] = useState("");
  const [saving, setSaving] = useState(false);

  async function add() {
    if (!url.trim()) return;
    setSaving(true);
    try {
      await contentClient.createResource({
        topic: topicId,
        resource_type: type,
        url,
        note: null,
        attachment: null,
      });
      setUrl("");
      onChanged?.();
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this resource?")) return;
    await contentClient.deleteResource(id);
    onChanged?.();
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 flex gap-2 flex-wrap items-center">
        <select
          className="rounded-lg border p-2 text-sm"
          value={type}
          onChange={(e) => setType(e.target.value as any)}
        >
          <option value="link">Link</option>
          <option value="video">Video</option>
        </select>

        <input
          className="flex-1 rounded-lg border p-2 text-sm"
          placeholder="https://..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <button
          onClick={add}
          disabled={saving}
          className="rounded-lg bg-black text-white px-4 py-2 text-sm disabled:opacity-50"
        >
          {saving ? "Adding..." : "Add"}
        </button>
      </div>

      <div className="grid gap-2">
        {resources.map((r) => (
          <div key={r.id} className="rounded-xl border p-4 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-xs text-gray-500 uppercase">{r.resource_type}</div>

              {r.url ? (
                <a className="underline text-sm break-all" href={r.url} target="_blank" rel="noreferrer">
                  {r.url}
                </a>
              ) : (
                <div className="text-sm text-gray-700">
                  ref: {r.note ? `note:${r.note}` : r.attachment ? `attachment:${r.attachment}` : "-"}
                </div>
              )}
            </div>

            <button
              onClick={() => remove(r.id)}
              className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
