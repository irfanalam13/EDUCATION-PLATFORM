"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Comment, Note } from "../../types/content.types";

export default function CommentsPanel({ topicId }: { topicId: number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [noteId, setNoteId] = useState<number | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [body, setBody] = useState("");
  const [reason, setReason] = useState("spam");
  const [reportDetail, setReportDetail] = useState("");

  async function loadNotes() {
    const n = await contentClient.listNotes({ topic: topicId, ordering: "-created_at" });
    setNotes(n);
    if (!noteId && n.length) setNoteId(n[0].id);
  }

  async function loadComments(selectedNoteId: number) {
    const c = await contentClient.listComments({ note: selectedNoteId, ordering: "created_at" });
    setComments(c);
  }

  useEffect(() => {
    loadNotes();
  }, [topicId]);

  useEffect(() => {
    if (noteId) loadComments(noteId);
  }, [noteId]);

  async function postComment() {
    if (!noteId || !body.trim()) return;
    await contentClient.createComment({ note: noteId, body });
    setBody("");
    await loadComments(noteId);
  }

  async function reportNote() {
    if (!noteId) return;
    await contentClient.createReport({ note: noteId, reason, detail: reportDetail });
    setReportDetail("");
    alert("Reported. Admin will review.");
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Comments</div>

        <select
          className="w-full rounded-lg border p-2 text-sm"
          value={noteId ?? ""}
          onChange={(e) => setNoteId(Number(e.target.value))}
        >
          {notes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.title}
            </option>
          ))}
        </select>

        <div className="grid gap-2">
          {comments.map((c) => (
            <div key={c.id} className="rounded-lg border p-3 text-sm">
              {c.body}
            </div>
          ))}
        </div>

        <textarea
          className="w-full rounded-lg border p-2"
          placeholder="Write a comment..."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />

        <button onClick={postComment} className="rounded-lg bg-black text-white px-4 py-2 text-sm">
          Post Comment
        </button>
      </div>

      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Report Content</div>
        <div className="flex gap-2">
          <select className="rounded-lg border p-2 text-sm" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="spam">Spam</option>
            <option value="abuse">Abuse</option>
            <option value="fake">Fake info</option>
            <option value="copyright">Copyright</option>
            <option value="other">Other</option>
          </select>
          <button onClick={reportNote} className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50">
            Report Selected Note
          </button>
        </div>

        <textarea
          className="w-full rounded-lg border p-2"
          placeholder="Extra details (optional)"
          value={reportDetail}
          onChange={(e) => setReportDetail(e.target.value)}
        />
      </div>
    </div>
  );
}
