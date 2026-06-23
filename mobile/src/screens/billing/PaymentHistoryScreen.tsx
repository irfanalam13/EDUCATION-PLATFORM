import { StyleSheet, View } from "react-native";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { ErrorView, LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { fetchInvoices } from "@/services/billing";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

const STATUS_COLOR: Record<string, string> = {
  PAID: palette.success,
  OPEN: palette.warning,
  REFUNDED: palette.danger,
};

export function PaymentHistoryScreen({ onBack }: { onBack: () => void }) {
  const invoices = useQuery({ queryKey: ["billing", "invoices"], queryFn: fetchInvoices });

  if (invoices.isLoading) {
    return (
      <Screen>
        <LoadingView label="Loading invoices..." />
      </Screen>
    );
  }
  if (invoices.isError) {
    return (
      <Screen>
        <ErrorView message={getErrorMessage(invoices.error)} onRetry={() => invoices.refetch()} />
      </Screen>
    );
  }

  const rows = invoices.data ?? [];

  return (
    <Screen>
      <Text variant="title">Payment history</Text>
      {rows.length === 0 ? (
        <Card>
          <Text variant="muted">No invoices yet.</Text>
        </Card>
      ) : (
        rows.map((inv) => (
          <Card key={inv.id} style={styles.row}>
            <View style={styles.rowTop}>
              <Text variant="label">{inv.number}</Text>
              <Text style={{ color: STATUS_COLOR[inv.status] ?? palette.ink, fontWeight: "700" }}>
                {inv.status}
              </Text>
            </View>
            <View style={styles.rowTop}>
              <Text variant="muted">{new Date(inv.created_at).toLocaleDateString()}</Text>
              <Text>
                {inv.currency} {inv.total}
              </Text>
            </View>
          </Card>
        ))
      )}
      <Button label="Back" variant="secondary" onPress={onBack} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.xs },
  rowTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
});
