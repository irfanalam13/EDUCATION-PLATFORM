"use client";

import type { DownloadablePack } from "../types/content.types";

export default function PackCard({ pack }: { pack: DownloadablePack }) {
  return (
    <div className="rounded-xl border p-4 flex items-center justify-between">
      <div>
        <div className="font-semibold">Pack v{pack.version}</div>
        <div className="text-xs text-gray-500">
          Size: {Math.round((pack.size || 0) / 1024)} KB
        </div>
        <div className="text-xs text-gray-500">Created: {pack.created_at}</div>
        {"status" in pack && (
          <div className="text-xs text-gray-500">
            Status: {(pack as any).status}
          </div>
        )}
      </div>

      {"file_url" in pack && (pack as any).file_url ? (
        <a
          href={(pack as any).file_url}
          target="_blank"
          rel="noreferrer"
          className="rounded-lg bg-black text-white px-4 py-2 text-sm"
        >
          Download
        </a>
      ) : (
        <span className="text-sm text-gray-500">Pending / No file</span>
      )}
    </div>
  );
}
