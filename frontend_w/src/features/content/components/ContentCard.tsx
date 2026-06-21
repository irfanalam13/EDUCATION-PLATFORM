import Link from "next/link";
import type { ContentItem } from "@/features/content/types/content.types";
import  Card  from "@/shared/ui/Card";

export function ContentCard({ item }: { item: ContentItem }) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold">
            <Link href={`/content/${item.id}`} className="hover:underline">
              {item.title}
            </Link>
          </h3>
          {item.description ? <p className="mt-1 text-sm text-gray-600">{item.description}</p> : null}
          <div className="mt-2 text-xs text-gray-500">
            <span className="rounded-lg border px-2 py-1">{item.content_type}</span>
            {item.topic?.name ? <span className="ml-2">{item.topic.name}</span> : null}
          </div>
        </div>
      </div>
    </Card>
  );
}
