import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { palette, spacing } from "@/theme";

export function PaymentSuccessScreen({
  onViewSubscription,
}: {
  onViewSubscription: () => void;
}) {
  return (
    <Screen scroll={false}>
      <View style={styles.center}>
        <Ionicons name="checkmark-circle" size={72} color={palette.success} />
        <Text variant="title" style={styles.heading}>
          You&apos;re all set!
        </Text>
        <Text variant="muted" style={styles.body}>
          Your subscription is active. Enjoy unlimited quizzes, AI study tools, and advanced
          analytics.
        </Text>
        <Button label="View my subscription" onPress={onViewSubscription} style={styles.button} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.md,
    padding: spacing.lg,
  },
  heading: { textAlign: "center" },
  body: { textAlign: "center" },
  button: { marginTop: spacing.md, alignSelf: "stretch" },
});
