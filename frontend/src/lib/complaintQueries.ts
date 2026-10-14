import type { ComplaintFilterRole } from "@/lib/complaintFilters";

/** React Query keys scoped per logged-in user so lists never leak across accounts. */

export function complaintsListKey(
  userId: string | undefined,
  scope: ComplaintFilterRole,
  filters?: { status?: string; priority?: string; awaiting_assignment?: boolean }
) {
  return [
    "complaints",
    scope,
    userId,
    filters?.status ?? "",
    filters?.priority ?? "",
    filters?.awaiting_assignment ? "awaiting" : "",
  ] as const;
}

export function complaintDetailKey(userId: string | undefined, complaintId: string | undefined) {
  return ["complaint", userId, complaintId] as const;
}
