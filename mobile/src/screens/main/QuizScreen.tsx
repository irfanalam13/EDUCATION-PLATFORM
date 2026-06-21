import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Field } from "@/components/Field";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { apiRequest } from "@/services/api";
import { palette, spacing } from "@/theme";
import type { McqQuestion } from "@/types/api";
import { getErrorMessage, unwrapList } from "@/utils/data";

export function QuizScreen() {
  const [topicId, setTopicId] = useState("1");
  const [activeTopicId, setActiveTopicId] = useState(1);
  const [index, setIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState<Record<number, boolean>>({});

  const questions = useQuery({
    queryKey: ["quiz", activeTopicId],
    queryFn: async () => unwrapList(await apiRequest<McqQuestion[] | { results: McqQuestion[] }>(`/api/assessment/mcq/questions/?topic=${activeTopicId}`))
  });

  const answer = useMutation({
    mutationFn: (payload: { questionId: number; choiceId: number }) =>
      apiRequest<{ is_correct: boolean }>(`/api/assessment/mcq/questions/${payload.questionId}/answer/`, {
        method: "POST",
        body: { choice_id: payload.choiceId }
      }),
    onSuccess: (result, variables) => {
      setAnswered((current) => ({ ...current, [variables.questionId]: true }));
      if (result.is_correct) setScore((current) => current + 1);
      setFeedback(result.is_correct ? "Correct answer." : "Not quite. Try reviewing the topic before the next one.");
    },
    onError: (err) => setFeedback(getErrorMessage(err))
  });

  const current = questions.data?.[index];

  return (
    <Screen>
      <Text variant="title">Quiz</Text>
      <Text variant="muted">Practice topic-wise MCQs from the Django backend.</Text>

      <Card style={styles.section}>
        <Field label="Topic ID" value={topicId} onChangeText={setTopicId} keyboardType="number-pad" />
        <Button
          label="Load topic quiz"
          onPress={() => {
            setActiveTopicId(Number(topicId || 1));
            setIndex(0);
            setScore(0);
            setAnswered({});
            setFeedback(null);
          }}
        />
      </Card>

      <Card style={styles.section}>
        <View style={styles.row}>
          <Text variant="subtitle">Question {questions.data?.length ? index + 1 : 0}</Text>
          <Text variant="muted">Score {score}/{questions.data?.length || 0}</Text>
        </View>

        {questions.isLoading ? <Text variant="muted">Loading questions...</Text> : null}
        {questions.isError ? <Text style={styles.error}>{getErrorMessage(questions.error)}</Text> : null}
        {!questions.isLoading && !questions.data?.length ? <Text variant="muted">No MCQs found for topic #{activeTopicId}.</Text> : null}

        {current ? (
          <>
            <Text>{current.question_text}</Text>
            <View style={styles.options}>
              {current.choices.map((choice) => {
                const selected = selectedChoiceId === choice.id;
                return (
                  <Pressable key={choice.id} style={[styles.option, selected ? styles.optionSelected : null]} onPress={() => setSelectedChoiceId(choice.id)}>
                    <Text>{choice.choice_text}</Text>
                  </Pressable>
                );
              })}
            </View>
            {feedback ? <Text variant="muted">{feedback}</Text> : null}
            {!answered[current.id] ? (
              <Button
                label={answer.isPending ? "Checking..." : "Submit answer"}
                onPress={() => selectedChoiceId && answer.mutate({ questionId: current.id, choiceId: selectedChoiceId })}
                disabled={!selectedChoiceId || answer.isPending}
              />
            ) : (
              <Button
                label={index + 1 >= (questions.data?.length || 0) ? "Review complete" : "Next question"}
                onPress={() => {
                  setIndex((currentIndex) => Math.min(currentIndex + 1, (questions.data?.length || 1) - 1));
                  setSelectedChoiceId(null);
                  setFeedback(null);
                }}
              />
            )}
          </>
        ) : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: {
    gap: spacing.md
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  options: {
    gap: spacing.sm
  },
  option: {
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md
  },
  optionSelected: {
    backgroundColor: palette.primarySoft,
    borderColor: palette.primary
  },
  error: {
    color: palette.danger
  }
});
