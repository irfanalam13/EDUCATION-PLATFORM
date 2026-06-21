"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { TopicProgress } from "../../types/content.types";

export default function ProgressPanel({ topicId }: { topicId: number }) {
  const [progress, setProgress] = useState<TopicProgress | null>(null);
  const [percent, setPercent] = useState<number>(0);
  const [saving, setSaving] = useState(false);

  async function load() {
    const p = await contentClient.getProgress({ topic: topicId });
    setProgress(p);
    setPercent(Number(p?.percent ?? 0));
  }

  async function save() {
    setSaving(true);
    try {
      const updated = await contentClient.upsertProgress({
        topic: topicId,
        percent,
        last_note: progress?.last_note ?? null,
        last_resource: progress?.last_resource ?? null,
      });
      setProgress(updated);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    load();
  }, [topicId]);

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Progress</h3>
        <button
          onClick={save}
          disabled={saving}
          className="rounded-lg bg-black text-white px-3 py-1 text-sm disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div className="bg-green-500 h-3" style={{ width: `${percent}%` }} />
      </div>

      <div className="flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={100}
          value={percent}
          onChange={(e) => setPercent(Number(e.target.value))}
          className="w-full"
        />
        <div className="text-sm text-gray-600 w-14 text-right">{percent}%</div>
      </div>

      <div className="text-xs text-gray-500">
        Continue reading is saved using <code>last_note</code>/<code>last_resource</code> when you open items in Study Mode.
      </div>
    </div>
  );
}
