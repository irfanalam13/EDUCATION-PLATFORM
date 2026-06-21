import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Field } from "@/components/Field";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { apiRequest } from "@/services/api";
import { palette, spacing } from "@/theme";
import type { ContentNote, ContentTopic } from "@/types/api";
import { getErrorMessage, unwrapList } from "@/utils/data";

export function NotesScreen() {
  const queryClient = useQueryClient();
  const [topicId, setTopicId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const topics = useQuery({
    queryKey: ["content-topics"],
    queryFn: async () => unwrapList(await apiRequest<ContentTopic[] | { results: ContentTopic[] }>("/api/academics/topics/"))
  });

  const notes = useQuery({
    queryKey: ["notes", topicId],
    enabled: Boolean(topicId),
    queryFn: async () => unwrapList(await apiRequest<ContentNote[] | { results: ContentNote[] }>(`/api/content/notes/?topic=${topicId}`))
  });

  const save = useMutation({
    mutationFn: () =>
      apiRequest("/api/content/notes/", {
        method: "POST",
        body: {
          topic: topicId,
          title,
          content_richtext: content,
          visibility: "private"
        }
      }),
    onSuccess: async () => {
      setTitle("");
      setContent("");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["notes", topicId] });
    },
    onError: (err) => setError(getErrorMessage(err))
  });

  const selectedTopic = useMemo(() => topics.data?.find((item) => item.id === topicId), [topicId, topics.data]);

  return (
    <Screen>
      <Text variant="title">Notes</Text>
      <Text variant="muted">Create private lesson notes and browse saved notes by content topic.</Text>

      <Card style={styles.section}>
        <Text variant="subtitle">Topic</Text>
        <View style={styles.chips}>
          {(topics.data || []).slice(0, 16).map((topic) => {
            const active = topic.id === topicId;
            return (
              <Pressable key={topic.id} style={[styles.chip, active ? styles.chipActive : null]} onPress={() => setTopicId(topic.id)}>
                <Text style={active ? styles.chipTextActive : styles.chipText}>{topic.title}</Text>
              </Pressable>
            );
          })}
        </View>
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">New note</Text>
        {selectedTopic ? <Text variant="muted">Saving under {selectedTopic.title}</Text> : <Text variant="muted">Choose a topic first.</Text>}
        <Field label="Title" value={title} onChangeText={setTitle} />
        <Field label="Markdown note" value={content} onChangeText={setContent} multiline />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label={save.isPending ? "Saving..." : "Save note"} onPress={() => save.mutate()} disabled={!topicId || !title || !content || save.isPending} />
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">Saved notes</Text>
        {(notes.data || []).map((note) => (
          <View key={note.id} style={styles.note}>
            <Text variant="label">{note.title}</Text>
            <Text variant="muted">{note.content_richtext}</Text>
          </View>
        ))}
        {topicId && !notes.data?.length ? <Text variant="muted">No notes for this topic yet.</Text> : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: {
    gap: spacing.sm
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  chip: {
    borderColor: palette.border,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  chipActive: {
    backgroundColor: palette.primary,
    borderColor: palette.primary
  },
  chipText: {
    color: palette.ink,
    fontSize: 13,
    fontWeight: "700"
  },
  chipTextActive: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700"
  },
  note: {
    borderTopColor: palette.border,
    borderTopWidth: 1,
    gap: spacing.xs,
    paddingTop: spacing.sm
  },
  error: {
    color: palette.danger
  }
});
