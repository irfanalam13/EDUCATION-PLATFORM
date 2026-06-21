"use client";

import { useState } from "react";
import type { Note } from "../types/content.types";
import { contentClient } from "../api/content.client";
import BookmarkButton from "./BookmarkButton";

export default function NoteCard({ note, onChanged }: { note: Note; onChanged?: () => void }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(note.title);
  const [content, setContent] = useState(note.content_richtext);
  const [visibility, setVisibility] = useState(note.visibility);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await contentClient.updateNote(note.id, {
        title,
        content_richtext: content,
        visibility,
      });
      setEditing(false);
      onChanged?.();
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!confirm("Delete this note?")) return;
    await contentClient.deleteNote(note.id);
    onChanged?.();
  }

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="flex items-start gap-2">
        <div className="flex-1">
          {!editing ? (
            <>
              <div className="font-semibold">{note.title}</div>
              <div className="text-xs text-gray-500">{note.visibility}</div>
            </>
          ) : (
            <div className="space-y-2">
              <input
                className="w-full rounded-lg border p-2 text-sm"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <select
                className="rounded-lg border p-2 text-sm"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as any)}
              >
                <option value="private">Private</option>
                <option value="unlisted">Unlisted</option>
                <option value="public">Public</option>
              </select>
            </div>
          )}
        </div>

        <BookmarkButton entityModel="note" entityId={note.id} />
      </div>

      {!editing ? (
        <div className="text-sm whitespace-pre-wrap">{note.content_richtext}</div>
      ) : (
        <textarea
          className="w-full rounded-lg border p-2 text-sm min-h-[140px]"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      )}

      <div className="flex gap-2 justify-end">
        {!editing ? (
          <>
            <button
              onClick={() => setEditing(true)}
              className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
            >
              Edit
            </button>
            <button
              onClick={remove}
              className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
            >
              Delete
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setEditing(false)}
              className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={save}
              disabled={saving}
              className="rounded-lg bg-black text-white px-3 py-1 text-sm disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
