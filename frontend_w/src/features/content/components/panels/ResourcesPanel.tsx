"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { TopicResource } from "../../types/content.types";
import ResourceList from "../ResourceList";

export default function ResourcesPanel({ topicId }: { topicId: number }) {
  const [resources, setResources] = useState<TopicResource[]>([]);
  const [loading, setLoading] = useState(true);

  // quick add link/video
  const [kind, setKind] = useState<"link" | "video">("link");
  const [url, setUrl] = useState("");

  async function load() {
    setLoading(true);
    const list = await contentClient.listResources({ topic: topicId, ordering: "-created_at" } as any);
    setResources(list);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, [topicId]);

  async function add() {
    if (!url.trim()) return;
    await contentClient.createResource({
      topic: topicId,
      resource_type: kind,
      url: url.trim(),
      note: null,
      attachment: null,
    } as any);
    setUrl("");
    load();
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Add Resource</div>
        <div className="flex gap-2 flex-wrap">
          <select className="rounded-lg border p-2" value={kind} onChange={(e) => setKind(e.target.value as any)}>
            <option value="link">Link</option>
            <option value="video">Video</option>
          </select>
          <input
            className="flex-1 rounded-lg border p-2 min-w-[220px]"
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button onClick={add} className="rounded-lg bg-black text-white px-4 py-2">
            Add
          </button>
        </div>
      </div>

      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Resources</div>
        {loading ? (
          <div className="text-sm text-gray-500">Loading...</div>
        ) : (
          <ResourceList resources={resources} />
        )}
      </div>
    </div>
  );
}
