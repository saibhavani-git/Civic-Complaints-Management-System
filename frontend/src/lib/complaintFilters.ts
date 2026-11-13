import type { UserRole } from "@/types";
import { publicStatus, PUBLIC_STATUSES } from "@/lib/complaintStatus";

/** Roles that have a dedicated complaints list + filters */
export type ComplaintFilterRole = Extract<UserRole, "citizen" | "officer" | "dept_admin" | "admin">;

export type StatusFilterOption = { value: string; label: string };

export function statusFilterOptions(_role: ComplaintFilterRole): StatusFilterOption[] {
  return [
    { value: "", label: "All statuses" },
    ...PUBLIC_STATUSES.map((item) => ({ value: item.value, label: item.label })),
  ];
}

/** Citizen dashboard groups — filter client-side (API returns all of the user's complaints). */
export function citizenGroupMatches(complaintStatus: string, groupValue: string): boolean {
  if (!groupValue) return true;
  return publicStatus(complaintStatus) === groupValue;
}

/** Public status sent to GET /complaints. The API expands it to the matching internal statuses. */
export function apiStatusParam(_role: ComplaintFilterRole, status: string): string | undefined {
  if (!status) return undefined;
  return status;
}

export function showPriorityFilter(role: ComplaintFilterRole): boolean {
  return role !== "citizen";
}

export function showAwaitingAssignmentFilter(role: ComplaintFilterRole): boolean {
  return role === "dept_admin";
}
