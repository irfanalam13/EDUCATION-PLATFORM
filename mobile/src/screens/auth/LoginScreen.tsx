import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Field } from "@/components/Field";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { useAuth } from "@/providers/AuthProvider";
import { API_BASE_URL } from "@/services/api";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

import { GoogleSignInButton } from "./GoogleSignInButton";

export function LoginScreen({ onGoSignup }: { onGoSignup: () => void }) {
  // Navigation is driven by AuthProvider state: once signIn succeeds, the user
  // is set and RootNavigator swaps to the main stack automatically. (No
  // expo-router in this app — it has no router runtime.)
  const { signIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // The Google OAuth hook (in GoogleSignInButton) throws on Android when no
  // androidClientId is set, so we only mount it when a client ID is configured.
  const googleClientConfigured = Boolean(
    process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ||
      process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID ||
      process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID ||
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID
  );

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await signIn(username, password);
      // RootNavigator switches to the main stack when `user` is set.
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.keyboard}>
        <View style={styles.hero}>
          <Text variant="title">EduPlatform Nepal</Text>
          <Text variant="muted">Learn, practice, take notes, and keep your progress moving from your phone.</Text>
        </View>

        <Card style={styles.card}>
          <Text variant="subtitle">Sign in</Text>
          <Field label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" />
          <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry />
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Button label={submitting ? "Signing in..." : "Sign in"} onPress={submit} disabled={!username || !password || submitting} />
          {googleClientConfigured ? (
            <GoogleSignInButton disabled={submitting} onError={setError} />
          ) : (
            <Text variant="muted">Set Google client IDs in mobile/.env to enable Google sign in.</Text>
          )}
          <Button label="Create account" onPress={onGoSignup} variant="ghost" />
        </Card>

        <Text variant="muted">Backend: {API_BASE_URL}</Text>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  keyboard: {
    flex: 1,
    justifyContent: "center",
    gap: spacing.lg
  },
  hero: {
    gap: spacing.sm
  },
  card: {
    gap: spacing.md
  },
  error: {
    color: palette.danger,
    fontSize: 14
  }
});
