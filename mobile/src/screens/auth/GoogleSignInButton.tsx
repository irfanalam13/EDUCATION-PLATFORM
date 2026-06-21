import { useEffect, useState } from "react";
import * as Google from "expo-auth-session/providers/google";
import * as WebBrowser from "expo-web-browser";

import { Button } from "@/components/Button";
import { useAuth } from "@/providers/AuthProvider";
import { getErrorMessage } from "@/utils/data";

WebBrowser.maybeCompleteAuthSession();

// Isolated so that Google.useAuthRequest() — which throws on Android when no
// androidClientId is set — only ever runs when the parent has confirmed at least
// one Google client ID is configured. Rendering this component conditionally is
// what keeps the hook off the render path on unconfigured installs.
export function GoogleSignInButton({
  disabled,
  onError,
}: {
  disabled?: boolean;
  onError: (message: string | null) => void;
}) {
  const { signInWithGoogleToken } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [request, response, promptAsync] = Google.useAuthRequest({
    androidClientId: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
    iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
    webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
    clientId:
      process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID ||
      process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
    scopes: ["openid", "profile", "email"],
  });

  useEffect(() => {
    async function finishGoogleSignIn() {
      if (response?.type !== "success") return;

      setSubmitting(true);
      onError(null);
      try {
        const idToken =
          response.authentication?.idToken ||
          (response.params as { id_token?: string } | undefined)?.id_token;
        if (!idToken) throw new Error("Google did not return an ID token.");

        await signInWithGoogleToken(idToken);
      } catch (err) {
        onError(getErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    }

    finishGoogleSignIn();
  }, [response, signInWithGoogleToken, onError]);

  async function submit() {
    setSubmitting(true);
    onError(null);
    try {
      await promptAsync();
    } catch (err) {
      onError(getErrorMessage(err));
      setSubmitting(false);
    }
  }

  return (
    <Button
      label={submitting ? "Opening Google..." : "Continue with Google"}
      onPress={submit}
      disabled={disabled || !request || submitting}
      variant="secondary"
    />
  );
}
