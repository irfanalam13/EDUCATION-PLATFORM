"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { GoogleSignInButton } from "./GoogleSignInButton";


export function LoginForm({ nextTo }: { nextTo?: string }) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  return (
    <Card className="mx-auto max-w-md p-8">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <p className="mt-2 text-sm text-muted">Use your platform account to open your dashboard, notes, and quiz workspace.</p>

      <form
        className="mt-6 space-y-4"
        onSubmit={async (event) => {
          event.preventDefault();
          setSubmitting(true);
          setError(null);
          try {
            const response = await fetch("/api/auth/login", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ username, password }),
            });
            if (!response.ok) {
              const data = await response.json().catch(() => ({}));
              throw new Error(data.detail || "Unable to sign in with those credentials.");
            }
            router.push(nextTo || "/dashboard");
            router.refresh();
          } catch (error: unknown) {
            setError(error instanceof Error ? error.message : "Unable to sign in with those credentials.");
          } finally {
            setSubmitting(false);
          }
        }}
      >
        <Field label="Username">
          <Input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Enter your username" />
        </Field>

        <Field label="Password">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
          />
        </Field>

        {error ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

        <Button className="w-full" disabled={submitting} type="submit">
          {submitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted">
        New here?{" "}
        <Link href="/signup" className="font-medium text-cyan-700">
          Create an account
        </Link>
      </p>

      <div className="mt-6 border-t border-app pt-6">
        <GoogleSignInButton nextTo={nextTo || "/dashboard"} />
      </div>
    </Card>
  );
}
