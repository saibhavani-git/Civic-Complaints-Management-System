"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useAuth } from "@/hooks/useAuth";

const API_ROOT =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1").replace(/\/api\/v1\/?$/, "");

type RealtimePayload = {
  type: string;
  complaint_id?: string;
  status?: string;
};

/**
 * One SSE connection per logged-in user — refetches React Query caches when the server pushes events.
 */
export function useRealtimeSync() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!user?.id) return;

    const token = localStorage.getItem("access_token");
    if (!token) return;

    const ctrl = new AbortController();

    fetchEventSource(`${API_ROOT}/api/v1/events/stream`, {
      signal: ctrl.signal,
      headers: { Authorization: `Bearer ${token}` },
      openWhenHidden: true,
      onmessage(ev) {
        if (!ev.data || ev.event === "connected") return;
        let payload: RealtimePayload;
        try {
          payload = JSON.parse(ev.data) as RealtimePayload;
        } catch {
          return;
        }

        if (payload.type === "complaint_updated") {
          queryClient.invalidateQueries({ queryKey: ["complaints"] });
          queryClient.invalidateQueries({ queryKey: ["complaint"] });
          if (payload.complaint_id) {
            queryClient.invalidateQueries({ queryKey: ["complaint", user.id, payload.complaint_id] });
          }
        }
        if (payload.type === "notifications_updated") {
          queryClient.invalidateQueries({ queryKey: ["notifications"] });
        }
      },
      onerror(err) {
        if (!ctrl.signal.aborted) {
          console.warn("Realtime stream interrupted", err);
        }
      },
    }).catch(() => {});

    return () => ctrl.abort();
  }, [user?.id, queryClient]);
}
