/** Citizen-facing tracking: submitted → review → dept → worker → finished */

export const TRACKING_STEPS = [
  "Submitted",
  "Under review",
  "Assigned to department",
  "Worker assigned",
  "Finished",
] as const;

const FINISHED = new Set(["resolved", "closed", "feedback_received"]);

/** 0–4 = active step index; 5 = all steps complete */
export function trackingStepIndex(status: string): number {
  if (FINISHED.has(status)) return 5;
  if (["assigned", "work_started", "in_progress"].includes(status)) return 3;
  if (["routed_to_department", "ai_processed", "verified", "pending"].includes(status)) return 2;
  if (status === "ai_processing") return 1;
  if (status === "submitted") return 0;
  return 0;
}

export const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  ai_processing: "Under review",
  routed_to_department: "Assigned to department",
  ai_processed: "Assigned to department",
  verified: "Assigned to department",
  pending: "Assigned to department",
  assigned: "Worker assigned",
  work_started: "Work in progress",
  in_progress: "Work in progress",
  resolved: "Finished",
  closed: "Finished",
  feedback_received: "Finished",
  rejected: "Rejected",
};

export function statusLabel(status: string, _opts?: { unsupportedDepartment?: boolean }): string {
  return STATUS_LABELS[status] ?? status.replace(/_/g, " ");
}
