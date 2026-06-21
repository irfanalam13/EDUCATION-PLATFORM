"use client";

import { useEffect, useMemo, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Note, Tag } from "../../types/content.types";
import NoteEditor from "../NoteEditor";
import NoteCard from "../NoteCard";

export default function NotesPanel({ topicId }: { topicId: number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTag, setSelectedTag] = useState<string>("");

  async function load() {
    const [n, t] = await Promise.all([
      contentClient.listNotes({ topic: topicId }),
      contentClient.listTags(),
    ]);
    setNotes(n);
    setTags(t);
  }

  const filtered = useMemo(() => {
    if (!selectedTag) return notes;
    // If backend supports tag param on listNotes, you can replace this with server filter.
    // For now, client-side tag filtering requires note to include tag info (optional).
    return notes;
  }, [notes, selectedTag]);

  useEffect(() => {
    load();
  }, [topicId]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 flex gap-3 items-center flex-wrap">
        <div className="font-semibold">Notes</div>
        <div className="ml-auto flex gap-2 items-center">
          <span className="text-sm text-gray-600">Tag</span>
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="rounded-lg border p-2 text-sm"
          >
            <option value="">All</option>
            {tags.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <NoteEditor topicId={topicId} onCreated={load} />

      <div className="grid gap-3">
        {filtered.map((note) => (
          <NoteCard key={note.id} note={note} onChanged={load} />
        ))}
      </div>
    </div>
  );
}
