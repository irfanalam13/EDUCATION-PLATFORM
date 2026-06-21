import type { ContentItem } from "../types/content.types";
import { Card } from "@/shared/ui/Card";

function toYouTubeEmbed(url: string) {
  // supports normal youtube urls; adjust if you store embed directly
  const match = url.match(/v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
  const id = match?.[1];
  return id ? `https://www.youtube.com/embed/${id}` : url;
}

export function ContentViewer({ item }: { item: ContentItem }) {
  if (item.content_type === "video" && item.video_url) {
    return (
      <Card>
        <div className="aspect-video w-full overflow-hidden rounded-xl">
          <iframe
            className="h-full w-full"
            src={toYouTubeEmbed(item.video_url)}
            title={item.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          />
        </div>
      </Card>
    );
  }

  if (item.content_type === "pdf" && item.file_url) {
    return (
      <Card>
        <div className="h-[75vh] w-full overflow-hidden rounded-xl border">
          <iframe className="h-full w-full" src={item.file_url} title={item.title} />
        </div>
        <div className="mt-3">
          <a className="text-sm underline" href={item.file_url} target="_blank" rel="noreferrer">
            Open / Download PDF
          </a>
        </div>
      </Card>
    );
  }

  if (item.content_type === "note") {
    return (
      <Card>
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap">{item.body || "No content."}</pre>
        </div>
      </Card>
    );
  }

  if (item.file_url) {
    return (
      <Card>
        <a className="text-sm underline" href={item.file_url} target="_blank" rel="noreferrer">
          Download file
        </a>
      </Card>
    );
  }

  return (
    <Card>
      <p className="text-sm text-gray-600">No viewer available for this content.</p>
    </Card>
  );
}
