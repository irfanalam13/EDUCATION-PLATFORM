import { StyleSheet, View } from "react-native";

import { palette, spacing } from "@/theme";
import { Button } from "./Button";
import { Text } from "./Text";

export function LoadingView({ label = "Loading..." }: { label?: string }) {
  return (
    <View style={styles.box}>
      <Text variant="muted">{label}</Text>
    </View>
  );
}

export function ErrorView({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={styles.box}>
      <Text variant="subtitle">Could not load</Text>
      <Text variant="muted">{message}</Text>
      {onRetry ? <Button label="Try again" onPress={onRetry} variant="secondary" /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    backgroundColor: palette.card,
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.sm,
    padding: spacing.md
  }
});
