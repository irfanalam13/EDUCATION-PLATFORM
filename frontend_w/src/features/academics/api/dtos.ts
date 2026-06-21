// src/features/academics/api/dtos.ts
export type LevelDTO = {
  id: number;
  name: string;
  order: number;
  is_active: boolean;
};

export type StreamDTO = {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
};

export type SubjectDTO = {
  id: number;
  name: string;
  code: string;
  order: number;
  is_active: boolean;
  level: number;
  stream: number | null;
  // if you included these in serializer:
  level_name?: string;
  stream_name?: string | null;
};

export type ChapterDTO = {
  id: number;
  title: string;
  number: number;
  order: number;
  is_active: boolean;
  subject: number;
  subject_name?: string;
};

export type TopicDTO = {
  id: number;
  title: string;
  order: number;
  is_active: boolean;
  content: string;
  chapter: number;
  chapter_title?: string;
};

export type TagDTO = {
  id: number;
  name: string;
  slug: string;
};
