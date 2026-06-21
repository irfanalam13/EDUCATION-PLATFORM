export type NoteVisibility = "public" | "unlisted" | "private";
export type ResourceType = "note" | "video" | "link" | "attachment";
export type AttachmentType = "pdf" | "image" | "audio" | "video" | "other";
export type PackStatus = "pending" | "ready" | "failed";

export type Note = {
  id: number;
  topic: number;
  title: string;
  content_richtext: string;
  visibility: NoteVisibility;
  tags: string[];
  created_at: string;
};

export type Attachment = {
  id: number;
  file_url: string;
  type: AttachmentType;
  size: number;
  mime_type: string;
  pages: number;
  duration_sec: number;
  created_at: string;
};

export type TopicResource = {
  id: number;
  topic: number;
  resource_type: ResourceType;
  note: number | null;
  attachment: number | null;
  url: string;
  created_at: string;
};

export type Tag = { id: number; name: string };

export type Progress = {
  id: number;
  topic: number;
  last_note: number | null;
  last_resource: number | null;
  percent: string;
};

export type DownloadablePack = {
  id: number;
  topic: number | null;
  chapter: number | null;
  version: string;
  size: number;
  checksum: string;
  status: PackStatus;
  file_url: string;
  created_at: string;
};

export type Comment = {
  id: number;
  topic: number;
  note: number | null;
  resource: number | null;
  parent: number | null;
  content: string;
  created_at: string;
};

export type QAQuestion = {
  id: number;
  topic: number;
  title: string;
  body: string;
  is_resolved: boolean;
  created_at: string;
};

export type QAAnswer = {
  id: number;
  question: number;
  body: string;
  is_accepted: boolean;
  created_at: string;
};

export type Deck = { id: number; topic: number; title: string };
export type Card = { id: number; deck: number; front: string; back: string };

export type Review = {
  id: number;
  card: number;
  ease: string;
  interval_days: number;
  due_at: string;
};

export type Collection = {
  id: number;
  topic: number;
  title: string;
  description: string;
  is_published: boolean;
};

export type CollectionItem = {
  id: number;
  collection: number;
  order: number;
  note: number | null;
  resource: number | null;
  attachment: number | null;
  url: string;
};


export type ContentTopicMini = {
  id: number;
  name: string;
};

export type ContentType = "note" | "video" | "link" | "attachment" | "collection";

export type ContentItem = {
  id: number;
  title: string;
  description?: string | null;
  content_type: ContentType;
  topic?: ContentTopicMini | null;
};




// =====================================================
// ADDITIONS (do not remove anything above)
// These make your types match contentClient imports 100%
// =====================================================

// --------------------
// Bookmarks
// --------------------
export type Bookmark = {
  id: number;
  entity_app_label: string;
  entity_model: string;
  entity_id: number;
  created_at: string;
};

// --------------------
// Reports
// --------------------
export type Report = {
  id: number;
  note: number | null;
  resource: number | null;
  reason: string;
  detail?: string | null;
  created_at: string;
};

// --------------------
// Aliases to match client naming
// --------------------
export type TopicProgress = Progress;

export type FlashcardDeck = Deck;
export type Flashcard = Card;

export type QuestionThread = QAQuestion;
export type Answer = QAAnswer;

export type TeacherCollection = Collection;

// --------------------
// Review Queue item (SRS due items)
// --------------------
export type ReviewSessionItem = {
  id: number; // queue row id (or review id)
  card_id: number;
  deck_id: number;
  topic?: number | null;
  front: string;
  back?: string | null; // optional if backend hides answer
  due_at: string;
};

// --------------------
// Optional payload helper (client sends body, your Comment uses content)
// This does NOT modify Comment; just adds a compatible write payload type.
// --------------------
export type CommentCreatePayload = {
  note?: number | null;
  resource?: number | null;
  body: string;
  parent?: number | null;
};

// --------------------
// Optional helper for progress upsert (client sends percent?: number)
// Your Progress.percent is string — keep it, this is just a write payload type.
// --------------------
export type TopicProgressUpsertPayload = {
  topic: number;
  last_note?: number | null;
  last_resource?: number | null;
  percent?: number;
};