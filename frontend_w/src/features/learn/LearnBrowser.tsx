"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { apiClient, unwrapList } from "@/lib/api";
import type { AcademicTopic, Chapter, Level, Subject } from "@/lib/types";

type ContentTopic = { id: number; chapter: number; title: string };

export function LearnBrowser() {
  const [selectedLevel, setSelectedLevel] = useState<number | "">("");
  const [selectedSubject, setSelectedSubject] = useState<number | "">("");
  const [selectedChapter, setSelectedChapter] = useState<number | "">("");

  const levels = useQuery({
    queryKey: ["levels"],
    queryFn: async () => unwrapList((await apiClient.get<Level[] | { results: Level[] }>("/api/academics/levels/")).data),
  });
  const subjects = useQuery({
    queryKey: ["subjects", selectedLevel],
    queryFn: async () =>
      unwrapList(
        (
          await apiClient.get<Subject[] | { results: Subject[] }>("/api/academics/subjects/", {
            params: selectedLevel ? { level: selectedLevel } : {},
          })
        ).data,
      ),
  });
  const chapters = useQuery({
    queryKey: ["chapters", selectedSubject],
    queryFn: async () =>
      unwrapList(
        (
          await apiClient.get<Chapter[] | { results: Chapter[] }>("/api/academics/chapters/", {
            params: selectedSubject ? { subject: selectedSubject } : {},
          })
        ).data,
      ),
  });
  const topics = useQuery({
    queryKey: ["academic-topics", selectedChapter],
    queryFn: async () =>
      unwrapList(
        (
          await apiClient.get<AcademicTopic[] | { results: AcademicTopic[] }>("/api/academics/topics/", {
            params: selectedChapter ? { chapter: selectedChapter } : {},
          })
        ).data,
      ),
  });
  const contentTopics = useQuery({
    queryKey: ["content-topics"],
    queryFn: async () =>
      unwrapList((await apiClient.get<ContentTopic[] | { results: ContentTopic[] }>("/api/academics/topics/")).data).slice(0, 8),
  });

  const summary = useMemo(
    () => ({
      levels: levels.data?.length || 0,
      subjects: subjects.data?.length || 0,
      topics: topics.data?.length || 0,
    }),
    [levels.data, subjects.data, topics.data],
  );

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <Card className="p-5">
          <div className="text-sm text-muted">Levels available</div>
          <div className="mt-2 text-3xl font-semibold">{summary.levels}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Subjects in view</div>
          <div className="mt-2 text-3xl font-semibold">{summary.subjects}</div>
        </Card>
        <Card className="p-5">
          <div className="text-sm text-muted">Topics in current filter</div>
          <div className="mt-2 text-3xl font-semibold">{summary.topics}</div>
        </Card>
      </section>

      <Card className="p-6">
        <h2 className="text-lg font-semibold">Curriculum explorer</h2>
        <p className="mt-1 text-sm text-muted">Follow the academic hierarchy, then jump straight into topic practice.</p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <select
            className="h-11 rounded-md border border-app bg-transparent px-3 text-sm"
            value={selectedLevel}
            onChange={(event) => {
              setSelectedLevel(event.target.value ? Number(event.target.value) : "");
              setSelectedSubject("");
              setSelectedChapter("");
            }}
          >
            <option value="">All levels</option>
            {levels.data?.map((level) => (
              <option key={level.id} value={level.id}>
                {level.name}
              </option>
            ))}
          </select>

          <select
            className="h-11 rounded-md border border-app bg-transparent px-3 text-sm"
            value={selectedSubject}
            onChange={(event) => {
              setSelectedSubject(event.target.value ? Number(event.target.value) : "");
              setSelectedChapter("");
            }}
          >
            <option value="">All subjects</option>
            {subjects.data?.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>

          <select
            className="h-11 rounded-md border border-app bg-transparent px-3 text-sm"
            value={selectedChapter}
            onChange={(event) => setSelectedChapter(event.target.value ? Number(event.target.value) : "")}
          >
            <option value="">All chapters</option>
            {chapters.data?.map((chapter) => (
              <option key={chapter.id} value={chapter.id}>
                {chapter.title}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {topics.data?.map((topic) => (
            <Card key={topic.id} className="p-5">
              <div className="text-xs uppercase tracking-wide text-cyan-700">{topic.chapter_title}</div>
              <h3 className="mt-2 text-base font-semibold">{topic.title}</h3>
              <p className="mt-2 line-clamp-3 text-sm leading-6 text-muted">{topic.content || "No theory text saved for this topic yet."}</p>
              <div className="mt-4 flex gap-2">
                <Link href={`/quiz?topic=${topic.id}`} className="text-sm font-medium text-cyan-700">
                  Open quiz
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-semibold">Content viewer</h2>
        <p className="mt-1 text-sm text-muted">This uses the separate content workspace for notes, resources, flashcards, and attachments.</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {contentTopics.data?.map((topic) => (
            <Link key={topic.id} href={`/content/${topic.id}`} className="rounded-md border border-app p-4 transition hover:border-cyan-700">
              <div className="text-sm font-medium">{topic.title}</div>
              <div className="mt-1 text-xs text-muted">Content topic #{topic.id}</div>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
