"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient, unwrapList } from "@/lib/api";
import type { AppNotification, PaginatedResponse } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const TYPE_ICON: Record<AppNotification["type"], string> = {
  SYSTEM: "🔔",
  XP: "⚡",
  BADGE: "🏅",
  QUIZ: "📝",
  ANNOUNCEMENT: "📢",
};

export function NotificationCenter() {
  const qc = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const list = useQuery({
    queryKey: ["notifications", { unreadOnly }],
    queryFn: async () => {
      const res = await apiClient.get<PaginatedResponse<AppNotification> | AppNotification[]>(
        "/api/notifications/notifications/",
        { params: unreadOnly ? { unread: 1 } : {} },
      );
      return unwrapList<AppNotification>(res.data);
    },
  });

  const markRead = useMutation({
    mutationFn: async (payload: { ids?: string[]; all?: boolean }) =>
      (await apiClient.post("/api/notifications/notifications/read/", payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });

  const items = list.data ?? [];
  const hasUnread = items.some((n) => !n.is_read);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="inline-flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => setUnreadOnly(e.target.checked)}
            className="h-4 w-4 rounded border-app"
          />
          Unread only
        </label>
        <Button
          variant="secondary"
          disabled={!hasUnread || markRead.isPending}
          onClick={() => markRead.mutate({ all: true })}
        >
          {markRead.isPending ? "Updating…" : "Mark all read"}
        </Button>
      </div>

      {list.isLoading ? (
        <div className="text-sm text-muted">Loading notifications…</div>
      ) : list.isError ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          Unable to load notifications right now.
        </div>
      ) : items.length === 0 ? (
        <Card className="p-10 text-center text-sm text-muted">
          {unreadOnly ? "No unread notifications." : "You're all caught up — no notifications yet."}
        </Card>
      ) : (
        <ul className="space-y-2">
          {items.map((n) => (
            <li key={n.id}>
              <Card
                className={cn(
                  "flex items-start gap-3 p-4",
                  !n.is_read && "border-l-4 border-l-cyan-700",
                )}
              >
                <div aria-hidden className="mt-0.5 text-lg">
                  {TYPE_ICON[n.type] ?? "🔔"}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <div className="truncate text-sm font-medium">{n.title}</div>
                    <time className="shrink-0 text-xs text-muted">{formatDate(n.created_at)}</time>
                  </div>
                  {n.body && <p className="mt-1 text-sm text-muted">{n.body}</p>}
                </div>
                {!n.is_read && (
                  <button
                    onClick={() => markRead.mutate({ ids: [n.id] })}
                    disabled={markRead.isPending}
                    className="shrink-0 text-xs text-cyan-700 hover:underline"
                  >
                    Mark read
                  </button>
                )}
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
