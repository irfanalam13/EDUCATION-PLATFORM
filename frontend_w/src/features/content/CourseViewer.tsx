"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { apiClient, unwrapList } from "@/lib/api";
import type { ContentNote, TopicResource } from "@/lib/types";
import { formatDate } from "@/lib/utils";


type ContentTopic = { id: number; chapter: number; title: string };

export function CourseViewer({ topicId }: { topicId: number }) {
  const topic = useQuery({
    queryKey: ["content-topic", topicId],
    queryFn: async () => (await apiClient.get<ContentTopic>(`/api/academics/topics/${topicId}/`)).data,
  });
  const notes = useQuery({
    queryKey: ["content-notes", topicId],
    queryFn: async () =>
      unwrapList(
        (await apiClient.get<ContentNote[] | { results: ContentNote[] }>("/api/content/notes/", { params: { topic: topicId } })).data,
      ),
  });
  const resources = useQuery({
    queryKey: ["topic-resources", topicId],
    queryFn: async () =>
      unwrapList(
        (
          await apiClient.get<TopicResource[] | { results: TopicResource[] }>("/api/content/topic-resources/", {
            params: { topic: topicId },
          })
        ).data,
      ),
  });

  if (topic.isLoading) {
    return <div className="text-sm text-muted">Loading course viewer...</div>;
  }

  if (topic.isError || !topic.data) {
    return <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">Unable to open this content topic.</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="text-xs uppercase tracking-wide text-cyan-700">Content workspace</div>
        <h1 className="mt-2 text-3xl font-semibold">{topic.data.title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
          This viewer brings together content-topic notes and supporting resources from the backend. Use the dedicated notes
          workspace if you want to create or edit your own study notes.
        </p>
        <div className="mt-5 flex gap-3">
          <Link href={`/content/notes?topic=${topicId}`} className="text-sm font-medium text-cyan-700">
            Open notes workspace
          </Link>
          <Link href={`/quiz?topic=${topicId}`} className="text-sm font-medium text-cyan-700">
            Open quiz
          </Link>
        </div>
      </Card>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-6">
          <h2 className="text-lg font-semibold">Notes</h2>
          <div className="mt-4 space-y-4">
            {notes.data?.length ? (
              notes.data.map((note) => (
                <div key={note.id} className="rounded-md border border-app p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{note.title}</div>
                    <div className="text-xs uppercase tracking-wide text-muted">{note.visibility}</div>
                  </div>
                  <div className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted">{note.content_richtext}</div>
                  <div className="mt-3 text-xs text-muted">Updated {formatDate(note.updated_at)}</div>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">No notes are attached to this content topic yet.</div>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold">Resources</h2>
          <div className="mt-4 space-y-3">
            {resources.data?.length ? (
              resources.data.map((resource) => (
                <div key={resource.id} className="rounded-md border border-app p-4">
                  <div className="text-sm font-medium capitalize">{resource.resource_type}</div>
                  <div className="mt-1 text-sm text-muted">
                    {resource.url ? (
                      <a href={resource.url} target="_blank" rel="noreferrer" className="text-cyan-700">
                        {resource.url}
                      </a>
                    ) : resource.note ? (
                      `Linked note #${resource.note}`
                    ) : resource.attachment ? (
                      `Attachment #${resource.attachment}`
                    ) : (
                      "No URL attached"
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">No resources published for this topic yet.</div>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
