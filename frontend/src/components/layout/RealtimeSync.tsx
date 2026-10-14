"use client";

import { useRealtimeSync } from "@/hooks/useRealtimeSync";

/** Mounts SSE listener; renders nothing. */
export function RealtimeSync() {
  useRealtimeSync();
  return null;
}
