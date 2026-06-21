import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { apiRequest } from "@/services/api";
import { palette, spacing } from "@/theme";
import type { AcademicTopic, Chapter, Level, Subject } from "@/types/api";
import { getErrorMessage, unwrapList } from "@/utils/data";

export function LearnScreen({ onOpenQuiz }: { onOpenQuiz: () => void }) {
  const [levelId, setLevelId] = useState<number | null>(null);
  const [subjectId, setSubjectId] = useState<number | null>(null);
  const [chapterId, setChapterId] = useState<number | null>(null);

  const levels = useQuery({
    queryKey: ["levels"],
    queryFn: async () => unwrapList(await apiRequest<Level[] | { results: Level[] }>("/api/academics/levels/"))
  });
  const subjects = useQuery({
    queryKey: ["subjects", levelId],
    queryFn: async () => unwrapList(await apiRequest<Subject[] | { results: Subject[] }>(`/api/academics/subjects/${levelId ? `?level=${levelId}` : ""}`))
  });
  const chapters = useQuery({
    queryKey: ["chapters", subjectId],
    queryFn: async () => unwrapList(await apiRequest<Chapter[] | { results: Chapter[] }>(`/api/academics/chapters/${subjectId ? `?subject=${subjectId}` : ""}`))
  });
  const topics = useQuery({
    queryKey: ["topics", chapterId],
    queryFn: async () => unwrapList(await apiRequest<AcademicTopic[] | { results: AcademicTopic[] }>(`/api/academics/topics/${chapterId ? `?chapter=${chapterId}` : ""}`))
  });

  const busy = levels.isLoading || subjects.isLoading || chapters.isLoading || topics.isLoading;
  const error = levels.error || subjects.error || chapters.error || topics.error;

  const selectedLevel = useMemo(() => levels.data?.find((item) => item.id === levelId), [levelId, levels.data]);

  if (busy && !levels.data) return <Screen><LoadingView label="Loading curriculum..." /></Screen>;
  if (error) return <Screen><ErrorView message={getErrorMessage(error)} /></Screen>;

  return (
    <Screen>
      <Text variant="title">Learn</Text>
      <Text variant="muted">Browse curriculum by level, subject, chapter, and topic.</Text>

      <Card style={styles.section}>
        <Text variant="subtitle">Levels</Text>
        <ChipList
          items={levels.data || []}
          selectedId={levelId}
          getLabel={(item) => item.name}
          onSelect={(id) => {
            setLevelId(id);
            setSubjectId(null);
            setChapterId(null);
          }}
        />
        {selectedLevel ? <Text variant="muted">Selected: {selectedLevel.name}</Text> : null}
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">Subjects</Text>
        <ChipList
          items={subjects.data || []}
          selectedId={subjectId}
          getLabel={(item) => item.name}
          onSelect={(id) => {
            setSubjectId(id);
            setChapterId(null);
          }}
        />
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">Chapters</Text>
        <ChipList items={chapters.data || []} selectedId={chapterId} getLabel={(item) => item.title} onSelect={setChapterId} />
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">Topics</Text>
        {(topics.data || []).slice(0, 12).map((topic) => (
          <View key={topic.id} style={styles.topic}>
            <View style={{ flex: 1 }}>
              <Text variant="label">{topic.title}</Text>
              <Text variant="muted" numberOfLines={2}>{topic.content || "Theory content has not been added yet."}</Text>
            </View>
            <Button label="Quiz" onPress={onOpenQuiz} variant="secondary" style={styles.quizButton} />
          </View>
        ))}
        {!topics.data?.length ? <Text variant="muted">No topics found for this filter.</Text> : null}
      </Card>
    </Screen>
  );
}

function ChipList<T extends { id: number }>({
  items,
  selectedId,
  getLabel,
  onSelect
}: {
  items: T[];
  selectedId: number | null;
  getLabel: (item: T) => string;
  onSelect: (id: number) => void;
}) {
  return (
    <View style={styles.chips}>
      {items.map((item) => {
        const active = item.id === selectedId;
        return (
          <Pressable key={item.id} style={[styles.chip, active ? styles.chipActive : null]} onPress={() => onSelect(item.id)}>
            <Text style={active ? styles.chipTextActive : styles.chipText}>{getLabel(item)}</Text>
          </Pressable>
        );
      })}
      {!items.length ? <Text variant="muted">Nothing to show yet.</Text> : null}
    </View>
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
  topic: {
    alignItems: "center",
    borderTopColor: palette.border,
    borderTopWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    paddingTop: spacing.sm
  },
  quizButton: {
    minHeight: 40
  }
});
