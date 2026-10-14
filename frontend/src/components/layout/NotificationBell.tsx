"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { notificationsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { getNotificationsPath } from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Bell, Check } from "lucide-react";
import type { Notification } from "@/types";
import {
  dedupeNotificationsForDisplay,
  markNotificationReadInCache,
} from "@/lib/notificationQueries";

interface NotificationBellProps {
  fullWidth?: boolean;
}

export function NotificationBell({ fullWidth }: NotificationBellProps) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list().then((r) => r.data),
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["notifications"] });
      const prev = queryClient.getQueryData<Notification[]>(["notifications"]);
      queryClient.setQueryData(["notifications"], markNotificationReadInCache(prev, id));
      return { prev };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["notifications"], ctx.prev);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const displayList = dedupeNotificationsForDisplay(notifications);
  const unread = notifications.filter((n: Notification) => !n.is_read).length;

  if (fullWidth) {
    return (
      <Link href={getNotificationsPath(user?.role)}>
        <Button variant="outline" className="w-full justify-start gap-2" size="sm">
          <Bell className="h-4 w-4" />
          Notifications
          {unread > 0 && (
            <span className="ml-auto rounded-full bg-primary px-1.5 py-0.5 text-[10px] text-white">
              {unread}
            </span>
          )}
        </Button>
      </Link>
    );
  }

  return (
    <div className="relative">
      <Button variant="ghost" size="icon" onClick={() => setOpen(!open)} className="relative">
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </Button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-50 w-80 rounded-xl border bg-white shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <span className="text-sm font-semibold">Notifications</span>
              <Link href={getNotificationsPath(user?.role)} className="text-xs text-primary hover:underline" onClick={() => setOpen(false)}>
                View all
              </Link>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-muted-foreground">No notifications</p>
              ) : (
                displayList.slice(0, 8).map((n: Notification) => (
                  <div
                    key={n.id}
                    className={`flex gap-3 border-b px-4 py-3 last:border-0 ${!n.is_read ? "bg-blue-50/50" : ""}`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{n.title}</p>
                      <p className="text-xs text-muted-foreground line-clamp-2">{n.message}</p>
                      <p className="text-[10px] text-muted-foreground mt-1">{formatDate(n.created_at)}</p>
                    </div>
                    {!n.is_read && (
                      <button
                        type="button"
                        disabled={markRead.isPending}
                        onClick={() => markRead.mutate(n.id)}
                        className="shrink-0 text-primary hover:text-primary/80 disabled:opacity-50"
                        title="Mark as read"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
