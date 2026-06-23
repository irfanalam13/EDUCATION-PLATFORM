import { AppFrame } from "@/components/layout/AppFrame";
import { BillingHistoryView } from "@/features/billing";

export default function BillingHistoryPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Billing history</h1>
        <p className="mt-2 text-sm text-muted">Your invoices and payments.</p>
      </div>
      <BillingHistoryView />
    </AppFrame>
  );
}
