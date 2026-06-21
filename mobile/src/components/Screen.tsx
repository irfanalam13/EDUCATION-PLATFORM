import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { palette, spacing } from "@/theme";

export function Screen({
  children,
  scroll = true
}: {
  children: React.ReactNode;
  scroll?: boolean;
}) {
  const content = <View style={styles.content}>{children}</View>;

  return (
    <SafeAreaView style={styles.safeArea}>
      {scroll ? (
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.scrollContent}>
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: palette.background
  },
  scrollContent: {
    flexGrow: 1
  },
  content: {
    flex: 1,
    padding: spacing.md,
    gap: spacing.md
  }
});
