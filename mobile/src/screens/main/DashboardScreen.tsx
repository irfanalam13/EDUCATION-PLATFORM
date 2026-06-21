import { useQuery } from "@tanstack/react-query";
import { StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { useAuth } from "@/providers/AuthProvider";
import { apiRequest } from "@/services/api";
import { palette, spacing } from "@/theme";
import type { DashboardPayload } from "@/types/api";
import { formatPercent, getErrorMessage } from "@/utils/data";

export function DashboardScreen() {
  const { user, signOut } = useAuth();
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiRequest<DashboardPayload>("/api/progress/dashboard/")
  });

  if (dashboard.isLoading) return <Screen><LoadingView label="Loading dashboard..." /></Screen>;
  if (dashboard.isError || !dashboard.data) {
    return (
      <Screen>
        <ErrorView message={getErrorMessage(dashboard.error)} onRetry={() => dashboard.refetch()} />
      </Screen>
    );
  }

  const data = dashboard.data;
  const accuracy = data.totals.total_answered ? (data.totals.correct / data.totals.total_answered) * 100 : 0;

  return (
    <Screen>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text variant="title">Namaste, {user?.first_name || user?.username}</Text>
          <Text variant="muted">Here is your learning pulse for today.</Text>
        </View>
        <Button label="Sign out" onPress={signOut} variant="secondary" style={styles.signOut} />
      </View>

      <View style={styles.grid}>
        <Metric label="Mastery" value={formatPercent(data.totals.avg_mastery)} />
        <Metric label="Accuracy" value={formatPercent(accuracy)} />
        <Metric label="Streak" value={`${data.streak.current_streak}d`} />
        <Metric label="XP today" value={`${data.today.xp_earned}`} />
      </View>

      <Card style={styles.section}>
        <Text variant="subtitle">Today</Text>
        <Text variant="muted">{data.today.minutes} minutes learned, {data.today.attempted} practice attempts.</Text>
        <View style={styles.progressTrack}>
          <View style={[styles.progressBar, { width: `${Math.min(100, (data.today.minutes / Math.max(1, data.goals.daily_minutes_goal)) * 100)}%` }]} />
        </View>
        <Text variant="muted">Daily goal: {data.goals.daily_minutes_goal} minutes</Text>
      </Card>

      <Card style={styles.section}>
        <Text variant="subtitle">Due reviews</Text>
        {data.due_topics.length ? (
          data.due_topics.slice(0, 4).map((topic) => (
            <View key={topic.topic} style={styles.row}>
              <Text>Topic #{topic.topic}</Text>
              <Text variant="muted">{formatPercent(topic.mastery)}</Text>
            </View>
          ))
        ) : (
          <Text variant="muted">No due reviews yet. Practice will create your review queue.</Text>
        )}
      </Card>
    </Screen>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card style={styles.metric}>
      <Text variant="muted">{label}</Text>
      <Text variant="subtitle">{value}</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md
  },
  signOut: {
    minHeight: 40
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  metric: {
    flexBasis: "47%",
    gap: spacing.xs
  },
  section: {
    gap: spacing.sm
  },
  row: {
    alignItems: "center",
    borderTopColor: palette.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: spacing.sm
  },
  progressTrack: {
    backgroundColor: "#e2e8f0",
    borderRadius: 999,
    height: 10,
    overflow: "hidden"
  },
  progressBar: {
    backgroundColor: palette.primary,
    height: "100%"
  }
});
