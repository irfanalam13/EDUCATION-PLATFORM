"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { DownloadablePack } from "../../types/content.types";
import PackCard from "../PackCard";

export default function PacksPanel({ topicId }: { topicId: number }) {
  const [packs, setPacks] = useState<DownloadablePack[]>([]);
  const [version, setVersion] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    const p = await contentClient.listPacks({ topic: topicId, ordering: "-created_at" });
    setPacks(p);
  }

  async function createPack() {
    if (!version.trim()) return;
    setCreating(true);
    try {
      await contentClient.createPack({ topic: topicId, version });
      setVersion("");
      await load();
      alert("Pack created (pending). Generator can fill file/size later.");
    } finally {
      setCreating(false);
    }
  }

  useEffect(() => {
    load();
  }, [topicId]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 flex gap-2 items-center">
        <input
          className="flex-1 rounded-lg border p-2"
          placeholder="Pack version (ex: 2026-01-25)"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
        />
        <button
          onClick={createPack}
          disabled={creating}
          className="rounded-lg bg-black text-white px-4 py-2 text-sm disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create Pack"}
        </button>
      </div>

      <div className="grid gap-3">
        {packs.map((p) => (
          <PackCard key={p.id} pack={p} />
        ))}
      </div>
    </div>
  );
}
