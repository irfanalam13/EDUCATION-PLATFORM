import { AppFrame } from "@/components/layout/AppFrame";
import { UpgradeView } from "@/features/billing";

export default function UpgradePage() {
  return (
    <AppFrame>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Upgrade your plan</h1>
        <p className="mt-2 text-sm text-muted">Pick the plan that fits how you study.</p>
      </div>
      <UpgradeView />
    </AppFrame>
  );
}
