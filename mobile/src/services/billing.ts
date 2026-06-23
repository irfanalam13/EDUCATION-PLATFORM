import { apiRequest } from "./api";
import { unwrapList } from "@/utils/data";

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
  is_free: boolean;
  highlight: boolean;
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
  current_period_end: string | null;
  trial_end: string | null;
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

export type SubscriptionResponse = {
  subscription: Subscription | null;
  entitlements: { tier: string; features: EntitlementFeature[] };
};

export type Invoice = {
  id: number;
  number: string;
  status: string;
  currency: string;
  total: string;
  amount_paid: string;
  created_at: string;
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
};

export const fetchPlans = () => apiRequest<Plan[]>("/api/billing/plans/", { auth: false });

export const fetchSubscription = () => apiRequest<SubscriptionResponse>("/api/billing/subscription/");

export const fetchInvoices = async (): Promise<Invoice[]> =>
  unwrapList(await apiRequest<Invoice[] | { results: Invoice[] }>("/api/billing/invoices/"));

export const subscribe = (body: SubscribeRequest) =>
  apiRequest<SubscribeResponse>("/api/billing/subscribe/", { method: "POST", body });

export const cancelSubscription = (atPeriodEnd: boolean) =>
  apiRequest<unknown>("/api/billing/cancel/", { method: "POST", body: { at_period_end: atPeriodEnd } });
