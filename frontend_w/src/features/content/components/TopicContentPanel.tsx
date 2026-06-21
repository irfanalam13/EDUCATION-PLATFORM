"use client";

import NotesPanel from "./panels/NotesPanel";
import ResourcesPanel from "./panels/ResourcesPanel";
import AttachmentsPanel from "./panels/AttachmentsPanel";
import BookmarksPanel from "./panels/BookmarksPanel";
import PacksPanel from "./panels/PacksPanel";

type Tab = "notes" | "resources" | "attachments" | "bookmarks" | "packs";

export default function TopicContentPanel({ topicId, tab }: { topicId: number; tab: Tab }) {
  if (tab === "notes") return <NotesPanel topicId={topicId} />;
  if (tab === "resources") return <ResourcesPanel topicId={topicId} />;
  if (tab === "attachments") return <AttachmentsPanel topicId={topicId} />;
  if (tab === "bookmarks") return <BookmarksPanel />;
  if (tab === "packs") return <PacksPanel topicId={topicId} />;
  return null;
}
