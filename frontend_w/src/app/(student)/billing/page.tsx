import { AppFrame } from "@/components/layout/AppFrame";
import { SubscriptionView } from "@/features/billing";

export default function BillingPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Subscription</h1>
        <p className="mt-2 text-sm text-muted">Manage your plan, entitlements, and renewals.</p>
      </div>
      <SubscriptionView />
    </AppFrame>
  );
}
