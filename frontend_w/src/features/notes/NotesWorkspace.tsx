"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, TextArea } from "@/components/ui/Field";
import { apiClient, unwrapList } from "@/lib/api";
import type { ContentNote, SessionUser } from "@/lib/types";


type SessionResponse = { authenticated: boolean; me?: SessionUser };
type ContentTopic = { id: number; title: string };

export function NotesWorkspace({ initialTopicId }: { initialTopicId?: number }) {
  const queryClient = useQueryClient();
  const [selectedTopicId, setSelectedTopicId] = useState<number | "">(initialTopicId || "");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<ContentNote["visibility"]>("private");

  const session = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const response = await fetch("/api/auth/session", { cache: "no-store" });
      return (await response.json()) as SessionResponse;
    },
  });
  const topics = useQuery({
    queryKey: ["note-topics"],
    queryFn: async () => unwrapList((await apiClient.get<ContentTopic[] | { results: ContentTopic[] }>("/api/academics/topics/")).data),
  });
  const notes = useQuery({
    queryKey: ["my-notes", selectedTopicId, session.data?.me?.id],
    enabled: Boolean(selectedTopicId && session.data?.me?.id),
    queryFn: async () =>
      unwrapList(
        (
          await apiClient.get<ContentNote[] | { results: ContentNote[] }>("/api/content/notes/", {
            params: { topic: selectedTopicId, created_by: session.data?.me?.id },
          })
        ).data,
      ),
  });

  const saveNote = useMutation({
    mutationFn: async () =>
      apiClient.post("/api/content/notes/", {
        topic: selectedTopicId,
        title,
        content_richtext: content,
        visibility,
      }),
    onSuccess: async () => {
      setTitle("");
      setContent("");
      await queryClient.invalidateQueries({ queryKey: ["my-notes"] });
    },
  });

  const selectedTopic = useMemo(
    () => topics.data?.find((topic) => topic.id === selectedTopicId),
    [selectedTopicId, topics.data],
  );

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card className="p-6">
        <h2 className="text-lg font-semibold">Compose a note</h2>
        <p className="mt-1 text-sm text-muted">Keep markdown-style notes per content topic and sync them back to the server.</p>

        <div className="mt-5 space-y-4">
          <Field label="Content topic">
            <select
              className="h-11 w-full rounded-md border border-app bg-transparent px-3 text-sm"
              value={selectedTopicId}
              onChange={(event) => setSelectedTopicId(event.target.value ? Number(event.target.value) : "")}
            >
              <option value="">Select a topic</option>
              {topics.data?.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Title">
            <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Revision summary" />
          </Field>

          <Field label="Content" hint="Markdown text is saved as plain content for now.">
            <TextArea value={content} onChange={(event) => setContent(event.target.value)} placeholder="- Key formula&#10;- Example&#10;- Mistakes to avoid" />
          </Field>

          <Field label="Visibility">
            <select
              className="h-11 w-full rounded-md border border-app bg-transparent px-3 text-sm"
              value={visibility}
              onChange={(event) => setVisibility(event.target.value as ContentNote["visibility"])}
            >
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </Field>

          <Button
            disabled={!selectedTopicId || !title || !content || saveNote.isPending}
            onClick={() => saveNote.mutate()}
          >
            {saveNote.isPending ? "Saving..." : "Save note"}
          </Button>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Your notes</h2>
            <p className="text-sm text-muted">{selectedTopic ? `Showing notes for ${selectedTopic.title}` : "Pick a topic to browse saved notes."}</p>
          </div>
        </div>

        <div className="mt-5 space-y-4">
          {notes.data?.length ? (
            notes.data.map((note) => (
              <div key={note.id} className="rounded-md border border-app p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{note.title}</div>
                  <div className="text-xs uppercase tracking-wide text-muted">{note.visibility}</div>
                </div>
                <div className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">{note.content_richtext}</div>
              </div>
            ))
          ) : (
            <div className="rounded-md border border-dashed border-app p-4 text-sm text-muted">No saved notes yet for this topic.</div>
          )}
        </div>
      </Card>
    </div>
  );
}
