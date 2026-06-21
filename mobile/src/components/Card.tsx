import { StyleSheet, View, ViewProps } from "react-native";

import { palette, spacing } from "@/theme";

export function Card({ style, ...props }: ViewProps) {
  return <View {...props} style={[styles.card, style]} />;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.card,
    borderColor: palette.border,
    borderRadius: 8,
    borderWidth: 1,
    padding: spacing.md,
    shadowColor: "#0f172a",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2
  }
});
