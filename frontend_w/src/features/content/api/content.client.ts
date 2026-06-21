import { http } from "@/shared/lib/http";
import type {
  Note,
  TopicResource,
  Attachment,
  Bookmark,
  DownloadablePack,
  TopicProgress,
  Tag,
  Comment,
  Report,
  FlashcardDeck,
  Flashcard,
  ReviewSessionItem,
  QuestionThread,
  Answer,
  TeacherCollection,
  CollectionItem,
} from "../types/content.types";

/**
 * Notes about API assumptions (match your Django module):
 * Base prefix: /api/content/
 *
 * Existing endpoints you already had:
 * - notes/
 * - attachments/
 * - topic-resources/
 * - bookmarks/
 * - download-packs/
 *
 * New endpoints this client expects you to add in backend (same style DRF ViewSets):
 * - progress/
 * - tags/
 * - comments/
 * - reports/
 * - flashcard-decks/
 * - flashcards/
 * - review-queue/          (SRS due items)
 * - review-grade/          (submit SRS grading)
 * - questions/
 * - answers/
 * - teacher-collections/
 * - collection-items/
 */

const base = "/api/content";

function unwrap<T>(data: any): T {
  return (data?.results ?? data) as T;
}

export const contentClient = {
  // -----------------------------
  // Notes (with filtering + tags)
  // -----------------------------
  async listNotes(params?: {
    topic?: number;
    visibility?: string;
    created_by?: number;
    search?: string;
    ordering?: string;
    tag?: string; // if you support tag filter server-side
  }) {
    const { data } = await http.get(`${base}/notes/`, { params: { ordering: "-created_at", ...params } });
    return unwrap<Note[]>(data);
  },

  async getNote(noteId: number) {
    const { data } = await http.get(`${base}/notes/${noteId}/`);
    return data as Note;
  },

  async createNote(payload: { topic: number; title: string; content_richtext: string; visibility: string }) {
    const { data } = await http.post(`${base}/notes/`, payload);
    return data as Note;
  },

  async updateNote(noteId: number, payload: Partial<{ title: string; content_richtext: string; visibility: string }>) {
    const { data } = await http.patch(`${base}/notes/${noteId}/`, payload);
    return data as Note;
  },

  async deleteNote(noteId: number) {
    await http.delete(`${base}/notes/${noteId}/`);
    return true;
  },

  // -----------------------------
  // Attachments (PDF/Image/Audio/Video)
  // -----------------------------
  async listAttachments(params?: { type?: string; uploaded_by?: number; ordering?: string }) {
    const { data } = await http.get(`${base}/attachments/`, { params: { ordering: "-created_at", ...params } });
    return unwrap<Attachment[]>(data);
  },

  async uploadAttachment(file: File, type: string) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("type", type);

    const { data } = await http.post(`${base}/attachments/`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data as Attachment;
  },

  async deleteAttachment(attachmentId: number) {
    await http.delete(`${base}/attachments/${attachmentId}/`);
    return true;
  },

  // -----------------------------
  // Topic Resources (note/video/link/attachment)
  // -----------------------------
  async listResources(params?: { topic?: number; resource_type?: string; ordering?: string }) {
    const { data } = await http.get(`${base}/topic-resources/`, {
      params: { ordering: "-created_at", ...params },
    });
    return unwrap<TopicResource[]>(data);
  },

  async createResource(payload: {
    topic: number;
    resource_type: "note" | "video" | "link" | "attachment";
    note?: number | null;
    attachment?: number | null;
    url?: string;
  }) {
    const { data } = await http.post(`${base}/topic-resources/`, payload);
    return data as TopicResource;
  },

  async deleteResource(resourceId: number) {
    await http.delete(`${base}/topic-resources/${resourceId}/`);
    return true;
  },

  // -----------------------------
  // Bookmarks (generic)
  // -----------------------------
  async myBookmarks(params?: { ordering?: string }) {
    const { data } = await http.get(`${base}/bookmarks/`, { params: { ordering: "-created_at", ...params } });
    return unwrap<Bookmark[]>(data);
  },

  async addBookmark(payload: { entity_app_label: string; entity_model: string; entity_id: number }) {
    const { data } = await http.post(`${base}/bookmarks/`, payload);
    return data as Bookmark;
  },

  async deleteBookmark(bookmarkId: number) {
    await http.delete(`${base}/bookmarks/${bookmarkId}/`);
    return true;
  },

  // -----------------------------
  // Downloadable Packs (filtered)
  // -----------------------------
  async listPacks(params?: { topic?: number; chapter?: number; version?: string; ordering?: string }) {
    const { data } = await http.get(`${base}/download-packs/`, {
      params: { ordering: "-created_at", ...params },
    });
    return unwrap<DownloadablePack[]>(data);
  },

  async getPack(packId: number) {
    const { data } = await http.get(`${base}/download-packs/${packId}/`);
    return data as DownloadablePack;
  },

  async createPack(payload: { topic?: number | null; chapter?: number | null; version: string }) {
    // backend should set status=pending and size/file later
    const { data } = await http.post(`${base}/download-packs/`, payload);
    return data as DownloadablePack;
  },

  async deletePack(packId: number) {
    await http.delete(`${base}/download-packs/${packId}/`);
    return true;
  },

  // -----------------------------
  // Progress + Continue reading
  // -----------------------------
  async getProgress(params: { topic: number }) {
    const { data } = await http.get(`${base}/progress/`, { params });
    // backend can return single object OR list; we handle both
    const arr = unwrap<TopicProgress[]>(data);
    return Array.isArray(arr) ? arr[0] ?? null : (arr as any);
  },

  async upsertProgress(payload: {
    topic: number;
    last_note?: number | null;
    last_resource?: number | null;
    percent?: number;
  }) {
    const { data } = await http.post(`${base}/progress/`, payload);
    return data as TopicProgress;
  },

  // -----------------------------
  // Tags (global) + tagging notes/resources
  // -----------------------------
  async listTags(params?: { search?: string; ordering?: string }) {
    const { data } = await http.get(`${base}/tags/`, { params: { ordering: "name", ...params } });
    return unwrap<Tag[]>(data);
  },

  async createTag(payload: { name: string }) {
    const { data } = await http.post(`${base}/tags/`, payload);
    return data as Tag;
  },

  // Attach/Detach tags (assumes backend actions exist)
  // Example endpoints:
  // POST /notes/{id}/tags/   { tag_ids: [1,2] }
  // DELETE /notes/{id}/tags/{tagId}/
  async setNoteTags(noteId: number, tagIds: number[]) {
    const { data } = await http.post(`${base}/notes/${noteId}/tags/`, { tag_ids: tagIds });
    return data as { note_id: number; tag_ids: number[] };
  },

  async removeNoteTag(noteId: number, tagId: number) {
    await http.delete(`${base}/notes/${noteId}/tags/${tagId}/`);
    return true;
  },

  // -----------------------------
  // Comments (notes/resources) + Reports
  // -----------------------------
  async listComments(params: { note?: number; resource?: number; ordering?: string }) {
    const { data } = await http.get(`${base}/comments/`, { params: { ordering: "created_at", ...params } });
    return unwrap<Comment[]>(data);
  },

  async createComment(payload: { note?: number | null; resource?: number | null; body: string; parent?: number | null }) {
    const { data } = await http.post(`${base}/comments/`, payload);
    return data as Comment;
  },

  async deleteComment(commentId: number) {
    await http.delete(`${base}/comments/${commentId}/`);
    return true;
  },

  async createReport(payload: {
    note?: number | null;
    resource?: number | null;
    reason: string;
    detail?: string;
  }) {
    const { data } = await http.post(`${base}/reports/`, payload);
    return data as Report;
  },

  // -----------------------------
  // Flashcards + SRS
  // -----------------------------
  async listDecks(params?: { topic?: number; ordering?: string }) {
    const { data } = await http.get(`${base}/flashcard-decks/`, {
      params: { ordering: "-created_at", ...params },
    });
    return unwrap<FlashcardDeck[]>(data);
  },

  async createDeck(payload: { topic: number; title: string; description?: string }) {
    const { data } = await http.post(`${base}/flashcard-decks/`, payload);
    return data as FlashcardDeck;
  },

  async deleteDeck(deckId: number) {
    await http.delete(`${base}/flashcard-decks/${deckId}/`);
    return true;
  },

  async listFlashcards(params?: { deck?: number; topic?: number; ordering?: string }) {
    const { data } = await http.get(`${base}/flashcards/`, { params: { ordering: "-created_at", ...params } });
    return unwrap<Flashcard[]>(data);
  },

  async createFlashcard(payload: { deck: number; front: string; back: string }) {
    const { data } = await http.post(`${base}/flashcards/`, payload);
    return data as Flashcard;
  },

  async updateFlashcard(cardId: number, payload: Partial<{ front: string; back: string }>) {
    const { data } = await http.patch(`${base}/flashcards/${cardId}/`, payload);
    return data as Flashcard;
  },

  async deleteFlashcard(cardId: number) {
    await http.delete(`${base}/flashcards/${cardId}/`);
    return true;
  },

  // Review queue (due cards) + grade
  async getReviewQueue(params?: { topic?: number; deck?: number; limit?: number }) {
    const { data } = await http.get(`${base}/review-queue/`, { params });
    return unwrap<ReviewSessionItem[]>(data);
  },

  async gradeReview(payload: { card_id: number; grade: 0 | 1 | 2 | 3 }) {
    // grade: 0=again, 1=hard, 2=good, 3=easy (example)
    const { data } = await http.post(`${base}/review-grade/`, payload);
    return data as { card_id: number; next_due_at: string };
  },

  // -----------------------------
  // Q&A (Topic questions + answers)
  // -----------------------------
  async listQuestions(params?: { topic?: number; search?: string; ordering?: string }) {
    const { data } = await http.get(`${base}/questions/`, { params: { ordering: "-created_at", ...params } });
    return unwrap<QuestionThread[]>(data);
  },

  async createQuestion(payload: { topic: number; title: string; body: string }) {
    const { data } = await http.post(`${base}/questions/`, payload);
    return data as QuestionThread;
  },

  async getQuestion(questionId: number) {
    const { data } = await http.get(`${base}/questions/${questionId}/`);
    return data as QuestionThread;
  },

  async listAnswers(params: { question: number; ordering?: string }) {
    const { data } = await http.get(`${base}/answers/`, { params: { ordering: "created_at", ...params } });
    return unwrap<Answer[]>(data);
  },

  async createAnswer(payload: { question: number; body: string }) {
    const { data } = await http.post(`${base}/answers/`, payload);
    return data as Answer;
  },

  async acceptAnswer(questionId: number, answerId: number) {
    // assumes backend action: POST /questions/{id}/accept-answer/ { answer_id }
    const { data } = await http.post(`${base}/questions/${questionId}/accept-answer/`, { answer_id: answerId });
    return data as { question_id: number; accepted_answer: number };
  },

  // -----------------------------
  // Teacher Collections / Playlists
  // -----------------------------
  async listCollections(params?: { topic?: number; teacher?: number; ordering?: string }) {
    const { data } = await http.get(`${base}/teacher-collections/`, {
      params: { ordering: "-created_at", ...params },
    });
    return unwrap<TeacherCollection[]>(data);
  },

  async createCollection(payload: { topic: number; title: string; description?: string }) {
    const { data } = await http.post(`${base}/teacher-collections/`, payload);
    return data as TeacherCollection;
  },

  async deleteCollection(collectionId: number) {
    await http.delete(`${base}/teacher-collections/${collectionId}/`);
    return true;
  },

  async listCollectionItems(params: { collection: number; ordering?: string }) {
    const { data } = await http.get(`${base}/collection-items/`, { params: { ordering: "order", ...params } });
    return unwrap<CollectionItem[]>(data);
  },

  async addCollectionItem(payload: {
    collection: number;
    order: number;
    item_type: "note" | "resource" | "attachment" | "link" | "video";
    note?: number | null;
    resource?: number | null;
    attachment?: number | null;
    url?: string;
    title?: string;
  }) {
    const { data } = await http.post(`${base}/collection-items/`, payload);
    return data as CollectionItem;
  },

  async reorderCollectionItems(collectionId: number, orderedItemIds: number[]) {
    // assumes backend action: POST /teacher-collections/{id}/reorder/ { item_ids: [...] }
    const { data } = await http.post(`${base}/teacher-collections/${collectionId}/reorder/`, {
      item_ids: orderedItemIds,
    });
    return data as { collection_id: number; item_ids: number[] };
  },

  async deleteCollectionItem(itemId: number) {
    await http.delete(`${base}/collection-items/${itemId}/`);
    return true;
  },
};
