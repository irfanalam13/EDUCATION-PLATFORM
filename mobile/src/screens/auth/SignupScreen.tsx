import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Field } from "@/components/Field";
import { Screen } from "@/components/Screen";
import { Text } from "@/components/Text";
import { useAuth } from "@/providers/AuthProvider";
import { palette, spacing } from "@/theme";
import { getErrorMessage } from "@/utils/data";

export function SignupScreen({ onGoLogin }: { onGoLogin: () => void }) {
  const { resendEmailVerification, signUp, verifyEmail } = useAuth();
  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password2: "",
    teacher_message: ""
  });
  const [accountType, setAccountType] = useState<"STUDENT" | "TEACHER">("STUDENT");
  const [pendingEmail, setPendingEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const response = await signUp({ ...form, account_type: accountType });
      if (response.requires_verification) {
        setPendingEmail(form.email);
        setDevOtp(response.dev_otp || "");
        return;
      }
      onGoLogin();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitOtp() {
    setSubmitting(true);
    setError(null);
    try {
      await verifyEmail(pendingEmail, otp);
      onGoLogin();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function resendOtp() {
    setError(null);
    try {
      const response = await resendEmailVerification(pendingEmail);
      if (response.dev_otp) setDevOtp(response.dev_otp);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (pendingEmail) {
    return (
      <Screen>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.wrapper}>
          <Text variant="title">Verify email</Text>
          <Text variant="muted">Enter the 6-digit code sent to {pendingEmail}.</Text>

          <Card style={styles.card}>
            {devOtp ? <Text style={styles.devOtp}>Dev OTP: {devOtp}</Text> : null}
            <Field label="Verification code" value={otp} onChangeText={setOtp} keyboardType="number-pad" maxLength={6} />
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Button label={submitting ? "Verifying..." : "Verify email"} onPress={submitOtp} disabled={otp.length !== 6 || submitting} />
            <Button label="Resend code" onPress={resendOtp} variant="secondary" />
            <Button label="Back to sign in" onPress={onGoLogin} variant="ghost" />
          </Card>
        </KeyboardAvoidingView>
      </Screen>
    );
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.wrapper}>
        <Text variant="title">Create account</Text>
        <Text variant="muted">Start as a student or request instructor approval.</Text>

        <Card style={styles.card}>
          <Field label="Username" value={form.username} onChangeText={(value) => update("username", value)} autoCapitalize="none" />
          <Field label="Email" value={form.email} onChangeText={(value) => update("email", value)} autoCapitalize="none" keyboardType="email-address" />
          <Field label="First name" value={form.first_name} onChangeText={(value) => update("first_name", value)} />
          <Field label="Last name" value={form.last_name} onChangeText={(value) => update("last_name", value)} />
          <Field label="Password" value={form.password} onChangeText={(value) => update("password", value)} secureTextEntry />
          <Field label="Confirm password" value={form.password2} onChangeText={(value) => update("password2", value)} secureTextEntry />
          <Button label={accountType === "STUDENT" ? "Student account" : "Instructor request"} onPress={() => setAccountType(accountType === "STUDENT" ? "TEACHER" : "STUDENT")} variant="secondary" />
          {accountType === "TEACHER" ? (
            <Field label="Instructor message" value={form.teacher_message} onChangeText={(value) => update("teacher_message", value)} multiline />
          ) : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Button label={submitting ? "Creating..." : "Create account"} onPress={submit} disabled={submitting} />
          <Button label="Back to sign in" onPress={onGoLogin} variant="ghost" />
        </Card>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: spacing.md
  },
  card: {
    gap: spacing.md
  },
  error: {
    color: palette.danger,
    fontSize: 14
  },
  devOtp: {
    color: palette.warning,
    fontSize: 14
  }
});
