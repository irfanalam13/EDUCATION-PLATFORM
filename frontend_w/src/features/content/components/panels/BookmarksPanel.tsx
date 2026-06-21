"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Bookmark } from "../../types/content.types";

export default function BookmarksPanel() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const b = await contentClient.myBookmarks();
      setBookmarks(b);
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    await contentClient.deleteBookmark(id);
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="font-semibold">My Bookmarks</div>
        <button onClick={load} className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50">
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600">Loading...</div>
      ) : (
        <div className="grid gap-2">
          {bookmarks.map((b) => (
            <div key={b.id} className="rounded-lg border p-3 flex items-center justify-between">
              <div className="text-sm">
                <div className="font-medium">Entity #{b.entity_id}</div>
                <div className="text-xs text-gray-500">{b.created_at}</div>
              </div>
              <button
                onClick={() => remove(b.id)}
                className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
              >
                Remove
              </button>
            </div>
          ))}
          {!bookmarks.length && <div className="text-sm text-gray-500">No bookmarks yet.</div>}
        </div>
      )}
    </div>
  );
}
