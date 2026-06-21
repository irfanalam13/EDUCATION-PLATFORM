"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { CollectionItem, TeacherCollection } from "../../types/content.types";

export default function CollectionsPanel({ topicId }: { topicId: number }) {
  const [collections, setCollections] = useState<TeacherCollection[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [items, setItems] = useState<CollectionItem[]>([]);

  async function loadCollections() {
    const c = await contentClient.listCollections({ topic: topicId });
    setCollections(c);
    if (!selectedId && c.length) setSelectedId(c[0].id);
  }

  async function loadItems(collectionId: number) {
    const it = await contentClient.listCollectionItems({ collection: collectionId });
    setItems(it);
  }

  useEffect(() => {
    loadCollections();
  }, [topicId]);

  useEffect(() => {
    if (selectedId) loadItems(selectedId);
  }, [selectedId]);

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="rounded-xl border p-4 space-y-2">
        <div className="font-semibold">Teacher Collections</div>
        <div className="grid gap-2">
          {collections.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedId(c.id)}
              className={`text-left rounded-lg border p-3 hover:bg-gray-50 ${
                selectedId === c.id ? "bg-gray-50" : ""
              }`}
            >
              <div className="font-medium text-sm">{c.title}</div>
              <div className="text-xs text-gray-500 line-clamp-2">{c.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="md:col-span-2 rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Playlist Items</div>

        {!selectedId ? (
          <div className="text-sm text-gray-600">Select a collection.</div>
        ) : (
          <div className="grid gap-2">
            {items.map((i) => (
              <div key={i.id} className="rounded-lg border p-3 text-sm">
                <div className="text-xs text-gray-500">{i.item_type}</div>
                <div className="font-medium">{i.title || i.url || `ref: ${i.note || i.resource || i.attachment || "-"}`}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
