import { useEffect, useMemo, useState } from "react";
import { Dimensions, Linking, Pressable, StyleSheet, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart, LineChart } from "react-native-chart-kit";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import {
  fetchInstitutionOverview,
  fetchMyInstitutions,
  fetchReports,
  fetchTeacherOverview,
  generateReport,
} from "@/services/analytics";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

type SubTab = "institution" | "teacher" | "reports";

const CHART_WIDTH = Dimensions.get("window").width - spacing.md * 2;
const chartConfig = {
  backgroundGradientFrom: palette.card,
  backgroundGradientTo: palette.card,
  decimalPlaces: 0,
  color: (o = 1) => `rgba(14, 116, 144, ${o})`,
  labelColor: () => palette.muted,
  propsForDots: { r: "3" },
};

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <Card style={styles.metric}>
      <Text variant="muted" style={styles.metricLabel}>
        {label}
      </Text>
      <Text variant="title" style={styles.metricValue}>
        {value}
      </Text>
    </Card>
  );
}

export function AnalyticsScreen() {
  const [tab, setTab] = useState<SubTab>("institution");
  const [institutionId, setInstitutionId] = useState<number | null>(null);

  const institutions = useQuery({ queryKey: ["institutions", "me"], queryFn: fetchMyInstitutions });

  useEffect(() => {
    if (institutionId == null && institutions.data?.length) {
      setInstitutionId(institutions.data[0].id);
    }
  }, [institutions.data, institutionId]);

  if (institutions.isLoading) {
    return (
      <Screen>
        <LoadingView label="Loading institutions..." />
      </Screen>
    );
  }
  if (!institutions.data?.length) {
    return (
      <Screen>
        <Text variant="title">Analytics</Text>
        <Text variant="muted">Your account is not linked to any institution.</Text>
      </Screen>
    );
  }

  return (
    <Screen>
      <Text variant="title" style={{ marginBottom: spacing.sm }}>
        Analytics
      </Text>

      {institutions.data.length > 1 ? (
        <View style={styles.chips}>
          {institutions.data.map((i) => (
            <Pressable
              key={i.id}
              onPress={() => setInstitutionId(i.id)}
              style={[styles.chip, institutionId === i.id ? styles.chipActive : null]}
            >
              <Text style={institutionId === i.id ? styles.chipTextActive : styles.chipText}>{i.name}</Text>
            </Pressable>
          ))}
        </View>
      ) : null}

      <View style={styles.segment}>
        {(["institution", "teacher", "reports"] as SubTab[]).map((t) => (
          <Pressable key={t} onPress={() => setTab(t)} style={[styles.segmentBtn, tab === t ? styles.segmentActive : null]}>
            <Text style={tab === t ? styles.segmentTextActive : styles.segmentText}>
              {t === "institution" ? "Institution" : t === "teacher" ? "Teacher" : "Reports"}
            </Text>
          </Pressable>
        ))}
      </View>

      {institutionId != null && tab === "institution" ? <InstitutionTab institutionId={institutionId} /> : null}
      {institutionId != null && tab === "teacher" ? <TeacherTab institutionId={institutionId} /> : null}
      {institutionId != null && tab === "reports" ? <ReportsTab institutionId={institutionId} /> : null}
    </Screen>
  );
}

function InstitutionTab({ institutionId }: { institutionId: number }) {
  const q = useQuery({
    queryKey: ["analytics", "institution", institutionId],
    queryFn: () => fetchInstitutionOverview(institutionId),
  });

  const trend = useMemo(() => (q.data?.trend ?? []).slice(-8), [q.data]);

  if (q.isLoading) return <LoadingView label="Loading institution analytics..." />;
  if (q.isError || !q.data) return <ErrorView message={getErrorMessage(q.error)} onRetry={() => q.refetch()} />;

  const m = q.data.metrics;
  return (
    <View style={{ gap: spacing.md }}>
      <View style={styles.grid}>
        <Metric label="Active students" value={m.active_students} />
        <Metric label="Daily active" value={m.daily_active_users} />
        <Metric label="Monthly active" value={m.monthly_active_users} />
        <Metric label="Learning hrs" value={m.learning_hours} />
        <Metric label="Quiz %" value={`${m.quiz_performance}%`} />
        <Metric label="Avg mastery" value={`${m.avg_mastery}%`} />
        <Metric label="Attendance" value={`${m.attendance_rate}%`} />
        <Metric label="Completion" value={`${m.assignments.completion_rate}%`} />
      </View>

      {trend.length >= 2 ? (
        <Card style={styles.chartCard}>
          <Text variant="subtitle">Active users</Text>
          <LineChart
            data={{ labels: trend.map((t) => t.date.slice(5)), datasets: [{ data: trend.map((t) => t.active_users) }] }}
            width={CHART_WIDTH - spacing.md * 2}
            height={200}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </Card>
      ) : null}
    </View>
  );
}

function TeacherTab({ institutionId }: { institutionId: number }) {
  const q = useQuery({
    queryKey: ["analytics", "teacher", institutionId],
    queryFn: () => fetchTeacherOverview(institutionId),
  });

  if (q.isLoading) return <LoadingView label="Loading teaching analytics..." />;
  if (q.isError || !q.data) return <ErrorView message={getErrorMessage(q.error)} onRetry={() => q.refetch()} />;

  const m = q.data.metrics;
  const weak = m.weak_topics.slice(0, 5);
  return (
    <View style={{ gap: spacing.md }}>
      <View style={styles.grid}>
        <Metric label="Students taught" value={m.students_taught} />
        <Metric label="Avg score" value={m.average_student_score} />
        <Metric label="Quiz %" value={`${m.quiz_performance}%`} />
        <Metric label="Engagement" value={`${m.engagement_rate}%`} />
      </View>

      {weak.length >= 1 ? (
        <Card style={styles.chartCard}>
          <Text variant="subtitle">Weak topics (mastery %)</Text>
          <BarChart
            data={{
              labels: weak.map((w) => w.topic.slice(0, 8)),
              datasets: [{ data: weak.map((w) => Math.round(w.avg_mastery ?? 0)) }],
            }}
            width={CHART_WIDTH - spacing.md * 2}
            height={220}
            fromZero
            yAxisLabel=""
            yAxisSuffix="%"
            chartConfig={{ ...chartConfig, color: (o = 1) => `rgba(245, 158, 11, ${o})` }}
            style={styles.chart}
          />
        </Card>
      ) : (
        <Text variant="muted">No weak-topic data yet.</Text>
      )}
    </View>
  );
}

function ReportsTab({ institutionId }: { institutionId: number }) {
  const queryClient = useQueryClient();
  const q = useQuery({
    queryKey: ["analytics", "reports", institutionId],
    queryFn: () => fetchReports(institutionId),
  });

  const gen = useMutation({
    mutationFn: (vars: { period: string; fmt: string }) => generateReport(institutionId, vars.period, vars.fmt),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["analytics", "reports", institutionId] }),
  });

  return (
    <View style={{ gap: spacing.md }}>
      <Card style={styles.chartCard}>
        <Text variant="subtitle">Generate report</Text>
        <View style={styles.genRow}>
          <Button label="Monthly PDF" onPress={() => gen.mutate({ period: "MONTHLY", fmt: "PDF" })} disabled={gen.isPending} />
          <Button
            label="Monthly Excel"
            variant="secondary"
            onPress={() => gen.mutate({ period: "MONTHLY", fmt: "XLSX" })}
            disabled={gen.isPending}
          />
        </View>
        {gen.isError ? <Text style={{ color: palette.danger }}>Generation failed (admin only).</Text> : null}
      </Card>

      {q.isLoading ? (
        <LoadingView label="Loading reports..." />
      ) : q.data?.length ? (
        q.data.map((r) => (
          <Card key={r.id} style={styles.reportRow}>
            <View style={{ flex: 1 }}>
              <Text variant="body">
                {r.period} · {r.file_format}
              </Text>
              <Text variant="muted">
                {r.period_start} → {r.period_end} · {r.status}
              </Text>
            </View>
            {r.download_url ? (
              <Button label="Open" variant="ghost" onPress={() => Linking.openURL(r.download_url as string)} />
            ) : null}
          </Card>
        ))
      ) : (
        <Text variant="muted">No reports yet — generate one above.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginBottom: spacing.sm },
  chip: { borderColor: palette.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  chipActive: { backgroundColor: palette.primarySoft, borderColor: palette.primary },
  chipText: { color: palette.muted, fontSize: 12 },
  chipTextActive: { color: palette.primaryDark, fontSize: 12, fontWeight: "700" },
  segment: { flexDirection: "row", backgroundColor: palette.card, borderColor: palette.border, borderWidth: 1, borderRadius: 10, padding: 3, marginBottom: spacing.md },
  segmentBtn: { flex: 1, alignItems: "center", paddingVertical: 8, borderRadius: 8 },
  segmentActive: { backgroundColor: palette.primary },
  segmentText: { color: palette.muted, fontWeight: "700", fontSize: 13 },
  segmentTextActive: { color: "#fff", fontWeight: "700", fontSize: 13 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  metric: { width: "47%", padding: spacing.md, flexGrow: 1 },
  metricLabel: { fontSize: 12 },
  metricValue: { fontSize: 22, marginTop: 2 },
  chartCard: { padding: spacing.md, gap: spacing.sm },
  chart: { borderRadius: 8, marginVertical: spacing.xs },
  genRow: { flexDirection: "row", gap: spacing.sm, flexWrap: "wrap" },
  reportRow: { flexDirection: "row", alignItems: "center", padding: spacing.md, gap: spacing.sm },
});
