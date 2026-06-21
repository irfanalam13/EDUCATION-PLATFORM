"use client";

import { useState } from "react";
import { contentClient } from "../api/content.client";

export default function AttachmentUpload({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState<"pdf" | "image" | "audio" | "video" | "other">("pdf");
  const [loading, setLoading] = useState(false);

  async function upload() {
    if (!file) return;
    setLoading(true);
    try {
      await contentClient.uploadAttachment(file, type);
      setFile(null);
      onUploaded();
      alert("Uploaded!");
    } catch (e: any) {
      alert(e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <div className="font-semibold">Upload Attachment</div>

      <div className="flex gap-2 flex-wrap items-center">
        <select
          className="rounded-lg border p-2 text-sm"
          value={type}
          onChange={(e) => setType(e.target.value as any)}
        >
          <option value="pdf">PDF</option>
          <option value="image">Image</option>
          <option value="audio">Audio</option>
          <option value="video">Video</option>
          <option value="other">Other</option>
        </select>

        <input
          type="file"
          className="text-sm"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <button
          onClick={upload}
          disabled={!file || loading}
          className="rounded-lg bg-black text-white px-4 py-2 text-sm disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>
    </div>
  );
}
