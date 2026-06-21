import { api } from "@/shared/lib/http";
import type { LevelDTO, StreamDTO, SubjectDTO, ChapterDTO, TopicDTO, TagDTO } from "./dtos";

export const academicsApi = {
  // ✅ array
  levels() {
    return api<LevelDTO[]>("/api/academics/levels/");
  },
  levelDetail(id: number) {
    return api<LevelDTO>(`/api/academics/levels/${id}/`);
  },

  // ✅ array
  streams() {
    return api<StreamDTO[]>("/api/academics/streams/");
  },

  // ✅ array
  subjects(params?: { level?: number; stream?: number; search?: string }) {
    const qs = new URLSearchParams();
    if (params?.level) qs.set("level", String(params.level));
    if (params?.stream) qs.set("stream", String(params.stream));
    if (params?.search) qs.set("search", params.search);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return api<SubjectDTO[]>(`/api/academics/subjects/${suffix}`);
  },
  subjectDetail(id: number) {
    return api<SubjectDTO>(`/api/academics/subjects/${id}/`);
  },

  // ✅ robust list -> always array
  chapters(params: { subject: number; search?: string }) {
    const qs = new URLSearchParams();
    qs.set("subject", String(params.subject));
    if (params.search) qs.set("search", params.search);

    return api<any>(`/api/academics/chapters/?${qs.toString()}`).then((r) =>
      Array.isArray(r) ? r : r?.results ?? []
    ) as Promise<ChapterDTO[]>;
  },

  // ✅ ADD THIS BACK (detail endpoint)
  chapterDetail(id: number) {
    return api<ChapterDTO>(`/api/academics/chapters/${id}/`);
  },

  // ✅ list -> array (your backend returns [ ... ])
  topics(params: { chapter: number; search?: string }) {
    const qs = new URLSearchParams();
    qs.set("chapter", String(params.chapter));
    if (params.search) qs.set("search", params.search);

    return api<TopicDTO[]>(`/api/academics/topics/?${qs.toString()}`);
  },

  // ✅ ADD THIS BACK (detail endpoint)
  topicDetail(id: number) {
    return api<TopicDTO>(`/api/academics/topics/${id}/`);
  },

  // ✅ array
  tags() {
    return api<TagDTO[]>("/api/academics/tags/");
  },
};
