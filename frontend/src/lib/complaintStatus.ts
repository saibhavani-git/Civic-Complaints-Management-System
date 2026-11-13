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

/** Happy-path tracker. Rejected is the fourth status, shown on its own. */
export const TRACKING_STEPS = ["Submitted", "In progress", "Resolved"] as const;

/** 0–2 = active step; 3 = resolved (all steps complete). */
export function trackingStepIndex(status: string): number {
  const group = publicStatus(status);
  if (group === "resolved") return TRACKING_STEPS.length;
  if (group === "in_progress") return 1;
  return 0;
}

export function statusLabel(status: string, _opts?: { unsupportedDepartment?: boolean }): string {
  const group = publicStatus(status);
  return PUBLIC_STATUSES.find((item) => item.value === group)?.label ?? "In progress";
}

export function priorityLabel(priority: string): "Low" | "Medium" | "High" {
  if (priority === "low") return "Low";
  return priority === "high" || priority === "critical" ? "High" : "Medium";
}
