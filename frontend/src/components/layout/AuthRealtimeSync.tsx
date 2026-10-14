"use client";

import { RealtimeSync } from "@/components/layout/RealtimeSync";
import { useAuth } from "@/hooks/useAuth";

/** SSE only when authenticated (inside AuthProvider). */
export function AuthRealtimeSync() {
  const { user, loading } = useAuth();
  if (loading || !user) return null;
  return <RealtimeSync />;
}
