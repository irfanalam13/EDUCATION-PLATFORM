// Billing domain types — mirror apps/billing serializers.

export type PlanFeature = { key: string; label: string; limit: number };

export type Plan = {
  id: number;
  tier: "FREE" | "PREMIUM" | "INSTITUTION";
  name: string;
  slug: string;
  description: string;
  price: string;
  currency: string;
  interval: "MONTH" | "YEAR" | "LIFETIME";
  trial_days: number;
  max_seats: number;
  highlight: boolean;
  display_order: number;
  is_free: boolean;
  features: PlanFeature[];
};

export type SubscriptionStatus =
  | "TRIALING"
  | "ACTIVE"
  | "PAST_DUE"
  | "CANCELED"
  | "EXPIRED"
  | "INCOMPLETE";

export type Subscription = {
  id: number;
  plan: Plan;
  status: SubscriptionStatus;
  gateway: string;
  started_at: string | null;
  trial_end: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_active: boolean;
  in_trial: boolean;
};

export type EntitlementFeature = {
  key: string;
  label: string;
  limit: number;
  used: number;
  remaining: number | null;
};

export type EntitlementSnapshot = { tier: string; features: EntitlementFeature[] };

export type SubscriptionResponse = {
  subscription: Subscription | null;
  entitlements: EntitlementSnapshot;
};

export type Payment = {
  id: number;
  gateway: string;
  amount: string;
  currency: string;
  amount_refunded: string;
  status: string;
  created_at: string;
};

export type Invoice = {
  id: number;
  number: string;
  status: string;
  currency: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total: string;
  amount_paid: string;
  amount_due: string;
  created_at: string;
  paid_at: string | null;
  payments: Payment[];
};

export type SubscribeResponse = {
  status: SubscriptionStatus;
  requires_payment: boolean;
  checkout_url: string;
  checkout_payload: Record<string, unknown> | null;
  invoice?: Invoice;
};

export type SubscribeRequest = {
  plan: string;
  gateway?: "STRIPE" | "KHALTI" | "ESEWA" | "MANUAL";
  coupon_code?: string;
  success_url?: string;
  cancel_url?: string;
  start_trial?: boolean;
  institution_id?: number;
  seats?: number;
  billing_email?: string;
};
