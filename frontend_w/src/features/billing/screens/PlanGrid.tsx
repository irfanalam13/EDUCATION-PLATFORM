"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

import { useSubscribe } from "../api/queries";
import type { Plan } from "../types";

const GATEWAYS = ["MANUAL", "STRIPE", "KHALTI", "ESEWA"] as const;

function intervalLabel(interval: Plan["interval"]) {
  return interval === "YEAR" ? "/year" : interval === "MONTH" ? "/month" : "";
}

export function PlanGrid({ plans, currentSlug }: { plans: Plan[]; currentSlug?: string }) {
  const subscribe = useSubscribe();
  const [gateway, setGateway] = useState<(typeof GATEWAYS)[number]>("MANUAL");
  const [coupon, setCoupon] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubscribe(plan: Plan) {
    setMessage(null);
    try {
      const res = await subscribe.mutateAsync({
        plan: plan.slug,
        gateway,
        coupon_code: coupon.trim() || undefined,
        success_url: typeof window !== "undefined" ? `${window.location.origin}/billing?paid=1` : undefined,
        cancel_url: typeof window !== "undefined" ? `${window.location.origin}/pricing` : undefined,
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url; // hosted gateway checkout
        return;
      }
      if (res.requires_payment) {
        setMessage(`Invoice ${res.invoice?.number} created — total ${res.invoice?.total}. Complete payment to activate.`);
      } else if (res.status === "TRIALING") {
        setMessage("Trial started — enjoy Premium! 🎉");
      } else {
        setMessage("Subscription active. 🎉");
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Subscription failed.");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="mb-1 block text-muted">Payment method</span>
          <select
            value={gateway}
            onChange={(e) => setGateway(e.target.value as (typeof GATEWAYS)[number])}
            className="h-10 rounded-md border border-app bg-card px-3"
          >
            {GATEWAYS.map((g) => (
              <option key={g} value={g}>
                {g === "MANUAL" ? "Manual / offline" : g.charAt(0) + g.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-muted">Coupon (optional)</span>
          <input
            value={coupon}
            onChange={(e) => setCoupon(e.target.value.toUpperCase())}
            placeholder="e.g. HALF"
            className="h-10 rounded-md border border-app bg-card px-3"
          />
        </label>
      </div>

      {message && (
        <div className="rounded-md border border-cyan-200 bg-cyan-50 p-3 text-sm text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200">
          {message}
        </div>
      )}

      <div className="grid gap-5 md:grid-cols-3">
        {plans.map((plan) => {
          const isCurrent = plan.slug === currentSlug;
          return (
            <Card
              key={plan.id}
              className={`flex flex-col p-6 ${plan.highlight ? "ring-2 ring-cyan-600" : ""}`}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                {plan.highlight && (
                  <span className="rounded-full bg-cyan-100 px-2 py-0.5 text-xs text-cyan-800">Popular</span>
                )}
              </div>
              <p className="mt-1 text-sm text-muted">{plan.description}</p>
              <div className="mt-4">
                <span className="text-3xl font-semibold">
                  {plan.is_free ? "Free" : `${plan.currency} ${plan.price}`}
                </span>
                {!plan.is_free && <span className="text-sm text-muted">{intervalLabel(plan.interval)}</span>}
              </div>
              {plan.trial_days > 0 && (
                <div className="mt-1 text-xs text-cyan-700">{plan.trial_days}-day free trial</div>
              )}
              <ul className="mt-4 flex-1 space-y-2 text-sm">
                {plan.features.map((f) => (
                  <li key={f.key} className="flex items-start gap-2">
                    <span className="text-cyan-600">✓</span>
                    <span>
                      {f.label}
                      {f.limit > 0 ? ` (${f.limit}/mo)` : ""}
                    </span>
                  </li>
                ))}
              </ul>
              <Button
                className="mt-6"
                disabled={isCurrent || subscribe.isPending}
                variant={plan.highlight ? "primary" : "secondary"}
                onClick={() => handleSubscribe(plan)}
              >
                {isCurrent ? "Current plan" : plan.is_free ? "Switch to Free" : `Choose ${plan.name}`}
              </Button>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
