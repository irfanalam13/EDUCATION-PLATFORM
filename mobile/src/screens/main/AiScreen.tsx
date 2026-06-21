import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import {
  getMastery, getWeakTopics, getRecommendations, getStudyPlan, generatePlan,
} from "@/services/aiLearning";
import { palette, spacing } from "@/theme";

type Section = "home" | "weak" | "plan" | "recs";

const SECTIONS: Array<{ key: Section; label: string }> = [
  { key: "home", label: "Home" },
  { key: "weak", label: "Weak" },
  { key: "plan", label: "Plan" },
  { key: "recs", label: "Tips" },
];

export function AiScreen() {
  const qc = useQueryClient();
  const [section, setSection] = useState<Section>("home");

  const mastery = useQuery({ queryKey: ["ai-mastery"], queryFn: getMastery });
  const weak = useQuery({ queryKey: ["ai-weak"], queryFn: getWeakTopics });
  const recs = useQuery({ queryKey: ["ai-recs"], queryFn: getRecommendations });
  const plan = useQuery({ queryKey: ["ai-plan"], queryFn: getStudyPlan });

  const generate = useMutation({
    mutationFn: generatePlan,
    onSuccess: () => {
      ["ai-mastery", "ai-weak", "ai-recs", "ai-plan"].forEach((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      );
    },
  });

  return (
    <Screen>
      <Text variant="title">AI Study Coach</Text>
      <Text variant="muted">What to study next, personalized for you.</Text>

      <Button
        label={generate.isPending ? "Analyzing..." : "Regenerate plan"}
        onPress={() => generate.mutate()}
        disabled={generate.isPending}
      />

      <View style={styles.segment}>
        {SECTIONS.map((s) => {
          const active = s.key === section;
          return (
            <Pressable
              key={s.key}
              style={[styles.segBtn, active ? styles.segBtnActive : null]}
              onPress={() => setSection(s.key)}
            >
              <Text style={active ? styles.segTextActive : styles.segText}>{s.label}</Text>
            </Pressable>
          );
        })}
      </View>

      {section === "home" ? (
        <Card style={styles.card}>
          <Text variant="subtitle">Overview</Text>
          <Text>Overall mastery: {Math.round(mastery.data?.overall_mastery ?? 0)}%</Text>
          <Text variant="muted">Topics tracked: {mastery.data?.topics.length ?? 0}</Text>
          <Text variant="muted">Weak topics: {weak.data?.length ?? 0}</Text>
          <Text variant="muted">Recommendations: {recs.data?.length ?? 0}</Text>
        </Card>
      ) : null}

      {section === "weak" ? (
        <View style={styles.list}>
          {!weak.data?.length ? (
            <Text variant="muted">No weak topics — run the analysis.</Text>
          ) : (
            weak.data.map((w) => (
              <Card key={w.topic} style={styles.card}>
                <Text variant="subtitle">{w.topic_title}</Text>
                <Text variant="muted">{w.reason}</Text>
                <Text style={styles.weak}>Weakness {Math.round(w.weak_score)} / 100</Text>
              </Card>
            ))
          )}
        </View>
      ) : null}

      {section === "plan" ? (
        <View style={styles.list}>
          {!plan.data ? (
            <Text variant="muted">No plan yet — tap Regenerate plan.</Text>
          ) : (
            plan.data.sessions.map((s) => (
              <Card key={s.id} style={styles.card}>
                <Text variant="subtitle">{s.start_time.slice(0, 5)} · {s.title}</Text>
                <Text variant="muted">{s.activity_type} · {s.duration_min} min</Text>
              </Card>
            ))
          )}
        </View>
      ) : null}

      {section === "recs" ? (
        <View style={styles.list}>
          {!recs.data?.length ? (
            <Text variant="muted">No recommendations yet.</Text>
          ) : (
            recs.data.map((r) => (
              <Card key={r.id} style={styles.card}>
                <Text variant="subtitle">{r.title}</Text>
                <Text variant="muted">{r.kind}{r.message ? ` · ${r.message}` : ""}</Text>
              </Card>
            ))
          )}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  segment: {
    flexDirection: "row",
    gap: spacing.sm,
    marginVertical: spacing.md,
  },
  segBtn: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: palette.card,
    borderWidth: 1,
    borderColor: palette.border,
  },
  segBtnActive: {
    backgroundColor: palette.primarySoft,
    borderColor: palette.primary,
  },
  segText: { color: palette.muted, fontWeight: "700", fontSize: 13 },
  segTextActive: { color: palette.primary, fontWeight: "700", fontSize: 13 },
  list: { gap: spacing.md },
  card: { gap: 4 },
  weak: { color: palette.danger, fontWeight: "700" },
});
