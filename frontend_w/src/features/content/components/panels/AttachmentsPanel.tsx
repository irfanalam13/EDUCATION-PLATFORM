"use client";

import { useEffect, useMemo, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Attachment } from "../../types/content.types";
import AttachmentUpload from "../AttachmentUpload";
import BookmarkButton from "../BookmarkButton";

export default function AttachmentsPanel({ topicId }: { topicId: number }) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(true);

  const pdfs = useMemo(() => attachments.filter((a) => a.type === "pdf"), [attachments]);

  async function load() {
    setLoading(true);
    // Attachments aren't topic-linked by default; you can link via TopicResource(attachment)
    // Here we show all attachments; if you want topic-only, link attachments into TopicResource and filter resources.
    const list = await contentClient.listAttachments({ ordering: "-created_at" } as any);
    setAttachments(list);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, [topicId]);

  return (
    <div className="space-y-4">
      <AttachmentUpload onUploaded={load} />

      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">PDF Preview</div>

        {loading ? (
          <div className="text-sm text-gray-500">Loading...</div>
        ) : pdfs.length === 0 ? (
          <div className="text-sm text-gray-500">No PDFs uploaded yet.</div>
        ) : (
          <div className="grid gap-3">
            {pdfs.map((a) => (
              <div key={a.id} className="rounded-lg border p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="font-semibold truncate">PDF #{a.id}</div>
                  <div className="ml-auto flex gap-2">
                    <a
                      className="rounded-lg border px-3 py-1 text-sm hover:bg-gray-50"
                      href={a.file_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open
                    </a>
                    <BookmarkButton model="attachment" entityId={a.id} />
                  </div>
                </div>

                {/* Simple preview */}
                <div className="rounded-lg overflow-hidden border">
                  <iframe
                    title={`pdf-${a.id}`}
                    src={a.file_url}
                    className="w-full h-[420px]"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">All Files</div>
        <div className="grid gap-2">
          {attachments.map((a) => (
            <div key={a.id} className="rounded-lg border p-3 flex items-center gap-2">
              <div className="text-xs text-gray-500">{a.type}</div>
              <a className="underline break-all text-sm" href={a.file_url} target="_blank" rel="noreferrer">
                {a.file_url}
              </a>
              <div className="ml-auto">
                <BookmarkButton model="attachment" entityId={a.id} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
