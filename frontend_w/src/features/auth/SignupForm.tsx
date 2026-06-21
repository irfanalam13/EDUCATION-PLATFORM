"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { GoogleSignInButton } from "./GoogleSignInButton";


export function SignupForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pendingEmail, setPendingEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password2: "",
    account_type: "STUDENT",
    teacher_message: "",
  });

  if (pendingEmail) {
    return (
      <Card className="mx-auto max-w-md p-8">
        <h1 className="text-2xl font-semibold">Verify your email</h1>
        <p className="mt-2 text-sm text-muted">Enter the 6-digit code sent to {pendingEmail}.</p>

        <form
          className="mt-6 space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            setSubmitting(true);
            setError(null);
            try {
              const response = await fetch("/api/auth/verify-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: pendingEmail, code: otp }),
              });
              if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(JSON.stringify(data));
              }
              router.push("/login");
            } catch (error: unknown) {
              setError(error instanceof Error ? error.message : "Unable to verify email.");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          {devOtp ? <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">Dev OTP: {devOtp}</div> : null}
          <Field label="Verification code">
            <Input inputMode="numeric" maxLength={6} value={otp} onChange={(event) => setOtp(event.target.value)} placeholder="123456" />
          </Field>
          {error ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}
          <Button className="w-full" disabled={otp.length !== 6 || submitting} type="submit">
            {submitting ? "Verifying..." : "Verify email"}
          </Button>
          <Button
            className="w-full"
            type="button"
            variant="secondary"
            onClick={async () => {
              const response = await fetch("/api/auth/resend-verification", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: pendingEmail }),
              });
              const data = await response.json().catch(() => ({}));
              if (data.dev_otp) setDevOtp(data.dev_otp);
            }}
          >
            Resend code
          </Button>
        </form>
      </Card>
    );
  }

  return (
    <Card className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Create your account</h1>
      <p className="mt-2 text-sm text-muted">We&apos;ll use this account across dashboard, practice, notes, and learning tools.</p>

      <form
        className="mt-6 grid gap-4 md:grid-cols-2"
        onSubmit={async (event) => {
          event.preventDefault();
          setSubmitting(true);
          setError(null);
          try {
            const response = await fetch("/api/auth/register", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(form),
            });
            if (!response.ok) {
              const data = await response.json().catch(() => ({}));
              throw new Error(typeof data === "object" ? JSON.stringify(data) : "Unable to create account.");
            }
            const data = await response.json();
            if (data.requires_verification) {
              setPendingEmail(form.email);
              setDevOtp(data.dev_otp || "");
              return;
            }
            router.push("/login");
          } catch (error: unknown) {
            setError(error instanceof Error ? error.message : "Unable to create account.");
          } finally {
            setSubmitting(false);
          }
        }}
      >
        <Field label="Username">
          <Input value={form.username} onChange={(e) => setForm((s) => ({ ...s, username: e.target.value }))} />
        </Field>
        <Field label="Email">
          <Input type="email" value={form.email} onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))} />
        </Field>
        <Field label="First name">
          <Input value={form.first_name} onChange={(e) => setForm((s) => ({ ...s, first_name: e.target.value }))} />
        </Field>
        <Field label="Last name">
          <Input value={form.last_name} onChange={(e) => setForm((s) => ({ ...s, last_name: e.target.value }))} />
        </Field>
        <Field label="Password">
          <Input type="password" value={form.password} onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))} />
        </Field>
        <Field label="Confirm password">
          <Input type="password" value={form.password2} onChange={(e) => setForm((s) => ({ ...s, password2: e.target.value }))} />
        </Field>
        <Field label="Account type" hint="Teacher requests still go through approval on the backend.">
          <select
            className="h-11 w-full rounded-md border border-app bg-transparent px-3 text-sm"
            value={form.account_type}
            onChange={(e) => setForm((s) => ({ ...s, account_type: e.target.value }))}
          >
            <option value="STUDENT">Student</option>
            <option value="TEACHER">Instructor</option>
          </select>
        </Field>
        <Field label="Teacher message" hint="Optional note for instructor approval.">
          <Input
            value={form.teacher_message}
            onChange={(e) => setForm((s) => ({ ...s, teacher_message: e.target.value }))}
            placeholder="Tell the admin what you'll teach"
          />
        </Field>

        {error ? <div className="md:col-span-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

        <div className="md:col-span-2 flex items-center justify-between gap-3">
          <p className="text-sm text-muted">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-cyan-700">
              Sign in
            </Link>
          </p>
          <Button disabled={submitting} type="submit">
            {submitting ? "Creating..." : "Create account"}
          </Button>
        </div>
      </form>

      <div className="mt-6 border-t border-app pt-6">
        <GoogleSignInButton />
      </div>
    </Card>
  );
}
