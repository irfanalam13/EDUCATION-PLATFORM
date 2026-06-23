import { StyleSheet, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { cancelSubscription, fetchSubscription } from "@/services/billing";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

function fmtDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "—";
}

export function SubscriptionScreen({
  onUpgrade,
  onHistory,
}: {
  onUpgrade: () => void;
  onHistory: () => void;
}) {
  const qc = useQueryClient();
  const sub = useQuery({ queryKey: ["billing", "subscription"], queryFn: fetchSubscription });
  const cancel = useMutation({
    mutationFn: (atPeriodEnd: boolean) => cancelSubscription(atPeriodEnd),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["billing", "subscription"] }),
  });

  if (sub.isLoading) {
    return (
      <Screen>
        <LoadingView label="Loading subscription..." />
      </Screen>
    );
  }
  if (sub.isError || !sub.data) {
    return (
      <Screen>
        <ErrorView message={getErrorMessage(sub.error)} onRetry={() => sub.refetch()} />
      </Screen>
    );
  }

  const { subscription, entitlements } = sub.data;

  return (
    <Screen>
      <Text variant="title">Subscription</Text>

      <Card style={styles.card}>
        <Text variant="muted">Current plan</Text>
        <Text variant="subtitle">
          {subscription ? subscription.plan.name : `Free (${entitlements.tier})`}
        </Text>
        {subscription ? (
          <View style={styles.rows}>
            <Row label="Status" value={subscription.status} />
            <Row label="Renews / ends" value={fmtDate(subscription.current_period_end)} />
            <Row label="Trial ends" value={fmtDate(subscription.trial_end)} />
            <Row label="Auto-renew" value={subscription.cancel_at_period_end ? "Off" : "On"} />
          </View>
        ) : null}
      </Card>

      <Card style={styles.card}>
        <Text variant="label">What you can use</Text>
        {entitlements.features.map((f) => (
          <Row
            key={f.key}
            label={f.label}
            value={f.limit <= 0 ? "Unlimited" : `${f.used}/${f.limit}`}
          />
        ))}
      </Card>

      <Button label={subscription && !subscription.plan.is_free ? "Change plan" : "Upgrade"} onPress={onUpgrade} />
      <Button label="Payment history" variant="secondary" onPress={onHistory} />
      {subscription && subscription.is_active && !subscription.plan.is_free ? (
        <>
          <Button
            label="Cancel at period end"
            variant="ghost"
            disabled={cancel.isPending}
            onPress={() => cancel.mutate(true)}
          />
          <Button
            label="Cancel now"
            variant="ghost"
            disabled={cancel.isPending}
            onPress={() => cancel.mutate(false)}
          />
        </>
      ) : null}
    </Screen>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text variant="muted">{label}</Text>
      <Text>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.sm },
  rows: { gap: spacing.xs, marginTop: spacing.sm },
  row: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 2 },
});
