import { AppFrame } from "@/components/layout/AppFrame";
import { PricingView } from "@/features/billing";

export default function PricingPage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Plans &amp; pricing</h1>
        <p className="mt-2 text-sm text-muted">
          Upgrade for unlimited quizzes, AI study tools, and advanced analytics.
        </p>
      </div>
      <PricingView />
    </AppFrame>
  );
}
