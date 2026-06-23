"use client";

import { usePlans, useSubscription } from "../api/queries";
import { PlanGrid } from "./PlanGrid";

// Upgrade flow: show only paid plans (Free is the implicit downgrade path).
export function UpgradeView() {
  const plans = usePlans();
  const sub = useSubscription();

  if (plans.isLoading) return <div className="text-sm text-muted">Loading plans…</div>;
  if (plans.isError || !plans.data)
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        Unable to load plans right now.
      </div>
    );

  const paid = plans.data.filter((p) => !p.is_free);
  return <PlanGrid plans={paid} currentSlug={sub.data?.subscription?.plan.slug} />;
}
