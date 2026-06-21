"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { createContent } from "../api/content.api";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";

export function UploadContentForm() {
  const [title, setTitle] = React.useState("");
  const [contentType, setContentType] = React.useState("pdf");
  const [videoUrl, setVideoUrl] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [description, setDescription] = React.useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      fd.append("title", title);
      fd.append("content_type", contentType);
      if (description) fd.append("description", description);
      if (videoUrl) fd.append("video_url", videoUrl);
      if (file) fd.append("file", file);
      return createContent(fd);
    },
  });

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <label className="text-sm">Title</label>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>

      <div className="space-y-1">
        <label className="text-sm">Description</label>
        <Input value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div className="space-y-1">
        <label className="text-sm">Content type</label>
        <select
          className="w-full rounded-xl border px-3 py-2"
          value={contentType}
          onChange={(e) => setContentType(e.target.value)}
        >
          <option value="pdf">PDF</option>
          <option value="video">Video</option>
          <option value="note">Note</option>
          <option value="file">File</option>
          <option value="link">Link</option>
        </select>
      </div>

      {contentType === "video" ? (
        <div className="space-y-1">
          <label className="text-sm">YouTube / Video URL</label>
          <Input value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)} placeholder="https://..." />
        </div>
      ) : null}

      {contentType === "pdf" || contentType === "file" ? (
        <div className="space-y-1">
          <label className="text-sm">File</label>
          <input
            type="file"
            className="w-full"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
      ) : null}

      <div className="flex gap-2">
        <Button disabled={mutation.isPending} onClick={() => mutation.mutate()}>
          {mutation.isPending ? "Uploading..." : "Upload"}
        </Button>
      </div>

      {mutation.isError ? <p className="text-sm text-red-600">Upload failed.</p> : null}
      {mutation.isSuccess ? <p className="text-sm text-green-700">Uploaded!</p> : null}
    </div>
  );
}
