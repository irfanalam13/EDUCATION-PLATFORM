import { useState } from "react";

import { PaymentHistoryScreen } from "@/screens/billing/PaymentHistoryScreen";
import { PaymentSuccessScreen } from "@/screens/billing/PaymentSuccessScreen";
import { PricingScreen } from "@/screens/billing/PricingScreen";
import { SubscriptionScreen } from "@/screens/billing/SubscriptionScreen";

// Local stack for the billing tab (the app uses simple state-based navigation).
type BillingRoute = "subscription" | "pricing" | "success" | "history";

export function BillingScreen() {
  const [route, setRoute] = useState<BillingRoute>("subscription");

  switch (route) {
    case "pricing":
      return (
        <PricingScreen onPaid={() => setRoute("success")} onBack={() => setRoute("subscription")} />
      );
    case "success":
      return <PaymentSuccessScreen onViewSubscription={() => setRoute("subscription")} />;
    case "history":
      return <PaymentHistoryScreen onBack={() => setRoute("subscription")} />;
    case "subscription":
    default:
      return (
        <SubscriptionScreen
          onUpgrade={() => setRoute("pricing")}
          onHistory={() => setRoute("history")}
        />
      );
  }
}
