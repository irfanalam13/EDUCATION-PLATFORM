import { useState } from "react";
import { Linking, StyleSheet, View } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { fetchPlans, fetchSubscription, subscribe, type Plan, type SubscribeRequest } from "@/services/billing";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

const GATEWAYS: SubscribeRequest["gateway"][] = ["MANUAL", "KHALTI", "ESEWA", "STRIPE"];

export function PricingScreen({ onPaid, onBack }: { onPaid: () => void; onBack?: () => void }) {
  const qc = useQueryClient();
  const plans = useQuery({ queryKey: ["billing", "plans"], queryFn: fetchPlans });
  const sub = useQuery({ queryKey: ["billing", "subscription"], queryFn: fetchSubscription });
  const [gateway, setGateway] = useState<SubscribeRequest["gateway"]>("MANUAL");
  const [notice, setNotice] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (plan: Plan) => subscribe({ plan: plan.slug, gateway }),
    onSuccess: async (res) => {
      qc.invalidateQueries({ queryKey: ["billing", "subscription"] });
      qc.invalidateQueries({ queryKey: ["billing", "invoices"] });
      if (res.checkout_url) {
        Linking.openURL(res.checkout_url).catch(() => setNotice("Could not open the payment page."));
        return;
      }
      if (res.requires_payment) {
        setNotice(`Invoice ${res.invoice?.number} created (${res.invoice?.currency} ${res.invoice?.total}).`);
      } else {
        onPaid();
      }
    },
    onError: (err) => setNotice(getErrorMessage(err)),
  });

  if (plans.isLoading) {
    return (
      <Screen>
        <LoadingView label="Loading plans..." />
      </Screen>
    );
  }
  if (plans.isError || !plans.data) {
    return (
      <Screen>
        <ErrorView message="Unable to load plans." onRetry={() => plans.refetch()} />
      </Screen>
    );
  }

  const currentSlug = sub.data?.subscription?.plan.slug;

  return (
    <Screen>
      <Text variant="title">Plans &amp; pricing</Text>
      <Text variant="muted">Unlock unlimited quizzes, AI tools, and analytics.</Text>

      <View style={styles.gatewayRow}>
        {GATEWAYS.map((g) => (
          <Button
            key={g}
            label={g === "MANUAL" ? "Offline" : (g ?? "")[0] + (g ?? "").slice(1).toLowerCase()}
            variant={gateway === g ? "primary" : "secondary"}
            onPress={() => setGateway(g)}
            style={styles.gatewayBtn}
          />
        ))}
      </View>

      {notice ? (
        <Card style={styles.notice}>
          <Text>{notice}</Text>
        </Card>
      ) : null}

      {plans.data.map((plan) => {
        const isCurrent = plan.slug === currentSlug;
        return (
          <Card key={plan.id} style={[styles.plan, plan.highlight ? styles.highlight : null]}>
            <View style={styles.planHead}>
              <Text variant="subtitle">{plan.name}</Text>
              <Text variant="subtitle">{plan.is_free ? "Free" : `${plan.currency} ${plan.price}`}</Text>
            </View>
            <Text variant="muted">{plan.description}</Text>
            {plan.trial_days > 0 ? (
              <Text style={styles.trial}>{plan.trial_days}-day free trial</Text>
            ) : null}
            <View style={styles.features}>
              {plan.features.map((f) => (
                <Text key={f.key} variant="body">
                  ✓ {f.label}
                  {f.limit > 0 ? ` (${f.limit}/mo)` : ""}
                </Text>
              ))}
            </View>
            <Button
              label={isCurrent ? "Current plan" : plan.is_free ? "Switch to Free" : `Choose ${plan.name}`}
              variant={plan.highlight ? "primary" : "secondary"}
              disabled={isCurrent || mutation.isPending}
              onPress={() => mutation.mutate(plan)}
            />
          </Card>
        );
      })}

      {onBack ? <Button label="Back" variant="ghost" onPress={onBack} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  gatewayRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  gatewayBtn: { flexGrow: 1, minWidth: 70 },
  notice: { backgroundColor: palette.primarySoft, borderColor: palette.primary },
  plan: { gap: spacing.sm },
  highlight: { borderColor: palette.primary, borderWidth: 2 },
  planHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  trial: { color: palette.primary, fontWeight: "700" },
  features: { gap: 4, marginVertical: spacing.sm },
});
