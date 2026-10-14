import type { UserRole } from "@/types";

/** Roles that have a dedicated complaints list + filters */
export type ComplaintFilterRole = Extract<UserRole, "citizen" | "officer" | "dept_admin" | "admin">;

export type StatusFilterOption = { value: string; label: string };

const CITIZEN_GROUPS: Record<string, readonly string[]> = {
  _review: ["submitted", "ai_processing"],
  _with_dept: ["routed_to_department", "ai_processed", "verified", "pending"],
  _in_progress: ["assigned", "work_started", "in_progress"],
  _finished: ["resolved", "closed", "feedback_received"],
  _rejected: ["rejected"],
};

export function statusFilterOptions(role: ComplaintFilterRole): StatusFilterOption[] {
  switch (role) {
    case "citizen":
      return [
        { value: "", label: "All complaints" },
        { value: "_review", label: "Under review" },
        { value: "_with_dept", label: "With department" },
        { value: "_in_progress", label: "Work in progress" },
        { value: "_finished", label: "Finished" },
      ];
    case "officer":
      return [
        { value: "", label: "All assigned" },
        { value: "assigned", label: "Newly assigned" },
        { value: "work_started", label: "Work started" },
        { value: "in_progress", label: "In progress" },
        { value: "resolved", label: "Resolved" },
        { value: "closed", label: "Closed" },
      ];
    case "dept_admin":
      return [
        { value: "", label: "All in department" },
        { value: "routed_to_department", label: "Routed — unassigned" },
        { value: "assigned", label: "Assigned to officer" },
        { value: "work_started", label: "Work started" },
        { value: "in_progress", label: "In progress" },
        { value: "resolved", label: "Resolved" },
        { value: "closed", label: "Closed" },
        { value: "rejected", label: "Rejected" },
      ];
    case "admin":
      return [
        { value: "", label: "All statuses" },
        { value: "submitted", label: "Submitted" },
        { value: "ai_processing", label: "Under review" },
        { value: "routed_to_department", label: "Routed to department" },
        { value: "assigned", label: "Assigned to officer" },
        { value: "work_started", label: "Work started" },
        { value: "in_progress", label: "In progress" },
        { value: "resolved", label: "Resolved" },
        { value: "closed", label: "Closed" },
        { value: "rejected", label: "Rejected" },
      ];
    default:
      return [{ value: "", label: "All" }];
  }
}

/** Citizen dashboard groups — filter client-side (API returns all of the user's complaints). */
export function citizenGroupMatches(complaintStatus: string, groupValue: string): boolean {
  if (!groupValue) return true;
  const statuses = CITIZEN_GROUPS[groupValue];
  return statuses ? statuses.includes(complaintStatus) : complaintStatus === groupValue;
}

/** Status values sent to GET /complaints (not citizen group keys). */
export function apiStatusParam(role: ComplaintFilterRole, status: string): string | undefined {
  if (!status || role === "citizen" || status.startsWith("_")) return undefined;
  return status;
}

export function showPriorityFilter(role: ComplaintFilterRole): boolean {
  return role !== "citizen";
}

export function showAwaitingAssignmentFilter(role: ComplaintFilterRole): boolean {
  return role === "dept_admin";
}
