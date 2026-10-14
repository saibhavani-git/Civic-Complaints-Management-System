"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { notificationsApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDate, getDashboardPath } from "@/lib/utils";
import { Bell, Check, Loader2 } from "lucide-react";
import type { Notification } from "@/types";
import {
  dedupeNotificationsForDisplay,
  markAllNotificationsReadInCache,
  markNotificationReadInCache,
} from "@/lib/notificationQueries";
import { Button } from "@/components/ui/button";

function complaintHref(role: string, complaintId: string) {
  if (role === "officer") return `/officer/complaints/${complaintId}`;
  if (role === "admin") return `/admin/complaints/${complaintId}`;
  return `/complaints/${complaintId}`;
}

export default function NotificationsContent() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: notifications = [], isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list().then((r) => r.data),
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["notifications"] });
      const prev = queryClient.getQueryData<Notification[]>(["notifications"]);
      queryClient.setQueryData(
        ["notifications"],
        markNotificationReadInCache(prev, id)
      );
      return { prev };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["notifications"], ctx.prev);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllRead = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["notifications"] });
      const prev = queryClient.getQueryData<Notification[]>(["notifications"]);
      queryClient.setQueryData(["notifications"], markAllNotificationsReadInCache(prev));
      return { prev };
    },
    onError: (_err, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["notifications"], ctx.prev);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const displayList = dedupeNotificationsForDisplay(notifications);
  const unread = notifications.filter((n: Notification) => !n.is_read).length;

  return (
    <div className="w-full">
      <PageHeader
        backHref={user ? getDashboardPath(user.role) : undefined}
        backLabel="Back to dashboard"
        title="Notifications"
        description={unread > 0 ? `${unread} unread` : "You're all caught up"}
        action={
          unread > 0 ? (
            <Button
              size="sm"
              variant="outline"
              disabled={markAllRead.isPending}
              onClick={() => markAllRead.mutate()}
            >
              Mark all as read
            </Button>
          ) : undefined
        }
      />

      {isLoading ? (
        <div className="flex items-center justify-center gap-2 text-muted-foreground py-16">
          <Loader2 className="h-5 w-5 animate-spin" />
          Loading...
        </div>
      ) : notifications.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-card py-16 text-center">
          <Bell className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <p className="font-medium">No notifications yet</p>
          <p className="text-sm text-muted-foreground mt-1">Updates will appear here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayList.map((n: Notification) => (
            <div
              key={n.id}
              className={`rounded-xl border bg-card p-4 sm:p-5 flex items-start gap-4 ${
                !n.is_read ? "border-primary/30 bg-blue-50/30" : ""
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="font-medium text-sm">{n.title}</p>
                  {!n.is_read && (
                    <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                      New
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">{n.message}</p>
                <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
                  <p className="text-xs text-muted-foreground">{formatDate(n.created_at)}</p>
                  {n.complaint_id && user && (
                    <Link
                      href={complaintHref(user.role, n.complaint_id)}
                      className="text-xs font-medium text-primary hover:underline"
                    >
                      View complaint →
                    </Link>
                  )}
                </div>
              </div>
              {!n.is_read && (
                <button
                  type="button"
                  disabled={markRead.isPending || markAllRead.isPending}
                  onClick={() => markRead.mutate(n.id)}
                  className="shrink-0 h-9 w-9 flex items-center justify-center rounded-lg border bg-white hover:bg-muted text-primary transition-colors disabled:opacity-50"
                  title="Mark as read"
                >
                  <Check className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
