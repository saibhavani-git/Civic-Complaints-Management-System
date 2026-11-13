/** Four public statuses. Internal workflow values map into these. */

export const PUBLIC_STATUSES = [
  { value: "submitted", label: "Submitted" },
  { value: "in_progress", label: "In progress" },
  { value: "resolved", label: "Resolved" },
  { value: "rejected", label: "Rejected" },
] as const;

export type PublicStatus = (typeof PUBLIC_STATUSES)[number]["value"];

const SUBMITTED = new Set(["submitted", "ai_processing"]);
const RESOLVED = new Set(["resolved", "closed", "feedback_received"]);

export function publicStatus(status: string): PublicStatus {
  if (status === "rejected") return "rejected";
  if (SUBMITTED.has(status) || status === "submitted") return "submitted";
  if (RESOLVED.has(status)) return "resolved";
  return "in_progress";
}

/** Citizen tracker: submitted → review → department → worker → finished. */
export const TRACKING_STEPS = [
  "Submitted",
  "Under review",
  "Assigned to department",
  "Worker assigned",
  "Finished",
] as const;

const FINISHED = new Set(["resolved", "closed", "feedback_received"]);

/** 0–4 = active step index; 5 = all steps complete. */
export function trackingStepIndex(status: string): number {
  if (FINISHED.has(status)) return 5;
  if (["assigned", "work_started", "in_progress"].includes(status)) return 3;
  if (["routed_to_department", "ai_processed", "verified", "pending"].includes(status)) return 2;
  if (status === "ai_processing") return 1;
  if (status === "submitted") return 0;
  return 0;
}

const STEP_LABELS: Record<string, string> = {
  submitted: "Submitted",
  ai_processing: "Under review",
  routed_to_department: "Assigned to department",
  ai_processed: "Assigned to department",
  verified: "Assigned to department",
  pending: "Assigned to department",
  assigned: "Worker assigned",
  work_started: "Work in progress",
  in_progress: "Work in progress",
  work_completed: "Work completed",
  resolved: "Finished",
  closed: "Finished",
  feedback_received: "Finished",
  rejected: "Rejected",
};

/** Fine-grained label used on the progress tracker timeline. */
export function stepLabel(status: string): string {
  return STEP_LABELS[status] ?? status.replace(/_/g, " ");
}

export function statusLabel(status: string, _opts?: { unsupportedDepartment?: boolean }): string {
  const group = publicStatus(status);
  return PUBLIC_STATUSES.find((item) => item.value === group)?.label ?? "In progress";
}

export function priorityLabel(priority: string): "Low" | "Medium" | "High" {
  if (priority === "low") return "Low";
  return priority === "high" || priority === "critical" ? "High" : "Medium";
}
