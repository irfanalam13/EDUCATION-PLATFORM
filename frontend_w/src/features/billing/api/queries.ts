"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelSubscription,
  fetchInvoices,
  fetchPlans,
  fetchSubscription,
  subscribe,
} from "./client";
import type { SubscribeRequest } from "../types";

export const billingKeys = {
  plans: ["billing", "plans"] as const,
  subscription: ["billing", "subscription"] as const,
  invoices: ["billing", "invoices"] as const,
};

export function usePlans() {
  return useQuery({ queryKey: billingKeys.plans, queryFn: fetchPlans });
}

export function useSubscription() {
  return useQuery({ queryKey: billingKeys.subscription, queryFn: fetchSubscription });
}

export function useInvoices() {
  return useQuery({ queryKey: billingKeys.invoices, queryFn: fetchInvoices });
}

export function useSubscribe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SubscribeRequest) => subscribe(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: billingKeys.subscription });
      qc.invalidateQueries({ queryKey: billingKeys.invoices });
    },
  });
}

export function useCancelSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (atPeriodEnd: boolean) => cancelSubscription(atPeriodEnd),
    onSuccess: () => qc.invalidateQueries({ queryKey: billingKeys.subscription }),
  });
}
