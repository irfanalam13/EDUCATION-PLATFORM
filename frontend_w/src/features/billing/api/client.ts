// Billing API calls. Routed through the same-origin BFF proxy (apiClient
// baseURL = /api/backend), which injects the JWT from the httpOnly cookie.
import { apiClient, unwrapList } from "@/lib/api";

import type {
  Invoice,
  Plan,
  SubscribeRequest,
  SubscribeResponse,
  SubscriptionResponse,
} from "../types";

export async function fetchPlans(): Promise<Plan[]> {
  const { data } = await apiClient.get<Plan[]>("/api/billing/plans/");
  return data;
}

export async function fetchSubscription(): Promise<SubscriptionResponse> {
  const { data } = await apiClient.get<SubscriptionResponse>("/api/billing/subscription/");
  return data;
}

export async function fetchInvoices(): Promise<Invoice[]> {
  const { data } = await apiClient.get<Invoice[] | { results: Invoice[] }>("/api/billing/invoices/");
  return unwrapList(data);
}

export async function subscribe(body: SubscribeRequest): Promise<SubscribeResponse> {
  const { data } = await apiClient.post<SubscribeResponse>("/api/billing/subscribe/", body);
  return data;
}

export async function cancelSubscription(atPeriodEnd: boolean): Promise<unknown> {
  const { data } = await apiClient.post("/api/billing/cancel/", { at_period_end: atPeriodEnd });
  return data;
}

export type CouponPreview = {
  valid: boolean;
  preview?: { subtotal: string; discount: string; total: string; currency: string };
};

export async function validateCoupon(code: string, planSlug: string): Promise<CouponPreview> {
  const { data } = await apiClient.get<CouponPreview>("/api/billing/coupon/validate/", {
    params: { code, plan: planSlug },
  });
  return data;
}
