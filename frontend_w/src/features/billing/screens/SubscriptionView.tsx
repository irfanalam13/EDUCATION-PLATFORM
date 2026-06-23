"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

import { useCancelSubscription, useSubscription } from "../api/queries";

function fmtDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString();
}

const STATUS_STYLE: Record<string, string> = {
  ACTIVE: "bg-emerald-100 text-emerald-800",
  TRIALING: "bg-cyan-100 text-cyan-800",
  PAST_DUE: "bg-amber-100 text-amber-800",
  CANCELED: "bg-slate-200 text-slate-700",
  EXPIRED: "bg-rose-100 text-rose-700",
  INCOMPLETE: "bg-amber-100 text-amber-800",
};

export function SubscriptionView() {
  const sub = useSubscription();
  const cancel = useCancelSubscription();
  const [notice, setNotice] = useState<string | null>(null);

  if (sub.isLoading) return <div className="text-sm text-muted">Loading subscription…</div>;
  if (sub.isError || !sub.data)
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        Unable to load your subscription.
      </div>
    );

  const { subscription, entitlements } = sub.data;

  async function handleCancel(atPeriodEnd: boolean) {
    setNotice(null);
    try {
      await cancel.mutateAsync(atPeriodEnd);
      setNotice(atPeriodEnd ? "Your plan will end at the period close." : "Subscription canceled.");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not cancel.");
    }
  }

  return (
    <div className="space-y-6">
      {notice && (
        <div className="rounded-md border border-cyan-200 bg-cyan-50 p-3 text-sm text-cyan-800">{notice}</div>
      )}

      <Card className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm text-muted">Current plan</div>
            <div className="mt-1 text-2xl font-semibold">
              {subscription ? subscription.plan.name : `Free (${entitlements.tier})`}
            </div>
          </div>
          {subscription && (
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLE[subscription.status] ?? ""}`}>
              {subscription.status}
            </span>
          )}
        </div>

        {subscription && (
          <div className="mt-5 grid gap-4 sm:grid-cols-3 text-sm">
            <div className="rounded-md border border-app p-3">
              <div className="text-xs uppercase tracking-wide text-muted">Renews / ends</div>
              <div className="mt-1 font-medium">{fmtDate(subscription.current_period_end)}</div>
            </div>
            <div className="rounded-md border border-app p-3">
              <div className="text-xs uppercase tracking-wide text-muted">Trial ends</div>
              <div className="mt-1 font-medium">{fmtDate(subscription.trial_end)}</div>
            </div>
            <div className="rounded-md border border-app p-3">
              <div className="text-xs uppercase tracking-wide text-muted">Auto-renew</div>
              <div className="mt-1 font-medium">{subscription.cancel_at_period_end ? "Off" : "On"}</div>
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/billing/upgrade">
            <Button>{subscription && !subscription.plan.is_free ? "Change plan" : "Upgrade"}</Button>
          </Link>
          <Link href="/billing/history">
            <Button variant="secondary">Billing history</Button>
          </Link>
          {subscription && subscription.is_active && !subscription.plan.is_free && (
            <>
              <Button variant="ghost" disabled={cancel.isPending} onClick={() => handleCancel(true)}>
                Cancel at period end
              </Button>
              <Button variant="ghost" disabled={cancel.isPending} onClick={() => handleCancel(false)}>
                Cancel now
              </Button>
            </>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-semibold">What you can use</h2>
        <ul className="mt-4 grid gap-2 sm:grid-cols-2 text-sm">
          {entitlements.features.map((f) => (
            <li key={f.key} className="flex items-center justify-between rounded-md border border-app px-3 py-2">
              <span>{f.label}</span>
              <span className="text-muted">
                {f.limit <= 0 ? "Unlimited" : `${f.used}/${f.limit} used`}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
