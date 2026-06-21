"use client";

import { useEffect, useMemo, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Note, TopicResource } from "../../types/content.types";

type StudyItem =
  | { kind: "note"; note: Note }
  | { kind: "resource"; resource: TopicResource };

export default function StudyModePanel({ topicId }: { topicId: number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [resources, setResources] = useState<TopicResource[]>([]);
  const [selected, setSelected] = useState<StudyItem | null>(null);
  const [fontSize, setFontSize] = useState(16);

  async function load() {
    const [n, r] = await Promise.all([
      contentClient.listNotes({ topic: topicId, ordering: "-created_at" }),
      contentClient.listResources({ topic: topicId, ordering: "-created_at" }),
    ]);
    setNotes(n);
    setResources(r);
  }

  // Save continue-reading (last_note / last_resource) when selection changes
  useEffect(() => {
    if (!selected) return;
    if (selected.kind === "note") {
      contentClient.upsertProgress({ topic: topicId, last_note: selected.note.id });
    } else {
      contentClient.upsertProgress({ topic: topicId, last_resource: selected.resource.id });
    }
  }, [selected, topicId]);

  useEffect(() => {
    load();
  }, [topicId]);

  const resourceWithUrl = useMemo(() => {
    if (!selected || selected.kind !== "resource") return null;
    const r = selected.resource;
    // For link/video/attachment, backend should return url or you can open attachment separately
    return r.url || "";
  }, [selected]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="font-semibold">Study Mode</div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Font</span>
            <input
              type="range"
              min={14}
              max={24}
              value={fontSize}
              onChange={(e) => setFontSize(Number(e.target.value))}
            />
            <span className="text-sm text-gray-600 w-8 text-right">{fontSize}</span>
          </div>
        </div>

        <div className="mt-3 grid md:grid-cols-3 gap-3">
          <div className="md:col-span-1 space-y-3">
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold mb-2">Notes</div>
              <div className="grid gap-2">
                {notes.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => setSelected({ kind: "note", note: n })}
                    className="text-left rounded-lg border px-3 py-2 hover:bg-gray-50"
                  >
                    <div className="text-sm font-medium">{n.title}</div>
                    <div className="text-xs text-gray-500">{n.visibility}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold mb-2">Resources</div>
              <div className="grid gap-2">
                {resources.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setSelected({ kind: "resource", resource: r })}
                    className="text-left rounded-lg border px-3 py-2 hover:bg-gray-50"
                  >
                    <div className="text-sm font-medium">{r.resource_type}</div>
                    <div className="text-xs text-gray-500 truncate">{r.url || `ref: ${r.note || r.attachment || "-"}`}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            {!selected ? (
              <div className="rounded-xl border p-6 text-sm text-gray-600">
                Select a note or resource to start studying.
              </div>
            ) : selected.kind === "note" ? (
              <div className="rounded-xl border p-6 bg-[#faf7f2]">
                <div className="font-semibold mb-3">{selected.note.title}</div>
                <div
                  style={{ fontSize }}
                  className="leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: selected.note.content_richtext }}
                />
              </div>
            ) : (
              <div className="rounded-xl border p-4">
                <div className="font-semibold mb-2">Resource Preview</div>

                {/* If resource URL is a PDF, preview in iframe/object */}
                {resourceWithUrl ? (
                  <div className="space-y-2">
                    <a className="underline text-sm" href={resourceWithUrl} target="_blank" rel="noreferrer">
                      Open in new tab
                    </a>

                    {/* Simple PDF preview */}
                    <div className="w-full h-[70vh] rounded-lg overflow-hidden border">
                      <iframe
                        src={resourceWithUrl}
                        className="w-full h-full"
                        title="Resource Preview"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-600">
                    This resource has no direct URL. If it’s an attachment ref, open it from Resources/Attachments.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
