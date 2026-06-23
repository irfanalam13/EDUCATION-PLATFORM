"use client";

import { Card } from "@/components/ui/Card";

import { useInvoices } from "../api/queries";

function fmtDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "—";
}

const STATUS_STYLE: Record<string, string> = {
  PAID: "text-emerald-700",
  OPEN: "text-amber-700",
  REFUNDED: "text-rose-700",
  VOID: "text-slate-500",
};

export function BillingHistoryView() {
  const invoices = useInvoices();

  if (invoices.isLoading) return <div className="text-sm text-muted">Loading invoices…</div>;
  if (invoices.isError)
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        Unable to load billing history.
      </div>
    );

  const rows = invoices.data ?? [];
  if (rows.length === 0)
    return <Card className="p-6 text-sm text-muted">No invoices yet.</Card>;

  return (
    <Card className="overflow-x-auto p-0">
      <table className="w-full min-w-[640px] text-sm">
        <thead className="border-b border-app text-left text-muted">
          <tr>
            <th className="px-4 py-3 font-medium">Invoice</th>
            <th className="px-4 py-3 font-medium">Date</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Total</th>
            <th className="px-4 py-3 font-medium">Paid</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((inv) => (
            <tr key={inv.id} className="border-b border-app/60">
              <td className="px-4 py-3 font-mono text-xs">{inv.number}</td>
              <td className="px-4 py-3">{fmtDate(inv.created_at)}</td>
              <td className={`px-4 py-3 font-medium ${STATUS_STYLE[inv.status] ?? ""}`}>{inv.status}</td>
              <td className="px-4 py-3">
                {inv.currency} {inv.total}
              </td>
              <td className="px-4 py-3">
                {inv.currency} {inv.amount_paid}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
