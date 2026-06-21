"use client";

import { useMemo, useState } from "react";
import ProgressPanel from "./panels/ProgressPanel";
import NotesPanel from "./panels/NotesPanel";
import ResourcesPanel from "./panels/ResourcesPanel";
import StudyModePanel from "./panels/StudyModePanel";
import AttachmentsPanel from "./panels/AttachmentsPanel";
import BookmarksPanel from "./panels/BookmarksPanel";
import PacksPanel from "./panels/PacksPanel";
import CommentsPanel from "./panels/CommentsPanel";
import FlashcardsPanel from "./panels/FlashcardsPanel";
import QAPanel from "./panels/QAPanel";
import CollectionsPanel from "./panels/CollectionsPanel";

type TabKey =
  | "progress"
  | "notes"
  | "resources"
  | "study"
  | "attachments"
  | "bookmarks"
  | "packs"
  | "comments"
  | "flashcards"
  | "qa"
  | "collections";

export default function TopicLearningTabs({ topicId }: { topicId: number }) {
  const tabs = useMemo(
    () =>
      [
        { key: "progress", label: "Progress" },
        { key: "notes", label: "Notes" },
        { key: "resources", label: "Resources" },
        { key: "study", label: "Study Mode" },
        { key: "attachments", label: "Attachments" },
        { key: "bookmarks", label: "Bookmarks" },
        { key: "packs", label: "Offline Packs" },
        { key: "comments", label: "Comments" },
        { key: "flashcards", label: "Flashcards" },
        { key: "qa", label: "Q&A" },
        { key: "collections", label: "Collections" },
      ] as { key: TabKey; label: string }[],
    []
  );

  const [active, setActive] = useState<TabKey>("progress");

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActive(t.key)}
            className={`rounded-lg border px-3 py-1 text-sm ${
              active === t.key ? "bg-black text-white" : "hover:bg-gray-50"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {active === "progress" && <ProgressPanel topicId={topicId} />}
      {active === "notes" && <NotesPanel topicId={topicId} />}
      {active === "resources" && <ResourcesPanel topicId={topicId} />}
      {active === "study" && <StudyModePanel topicId={topicId} />}
      {active === "attachments" && <AttachmentsPanel topicId={topicId} />}
      {active === "bookmarks" && <BookmarksPanel />}
      {active === "packs" && <PacksPanel topicId={topicId} />}
      {active === "comments" && <CommentsPanel topicId={topicId} />}
      {active === "flashcards" && <FlashcardsPanel topicId={topicId} />}
      {active === "qa" && <QAPanel topicId={topicId} />}
      {active === "collections" && <CollectionsPanel topicId={topicId} />}
    </div>
  );
}
