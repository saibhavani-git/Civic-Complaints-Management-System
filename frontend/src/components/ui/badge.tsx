"use client";

import { cn } from "@/lib/utils";
import { priorityLabel, publicStatus, statusLabel, stepLabel } from "@/lib/complaintStatus";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "muted";

const variants: Record<BadgeVariant, string> = {
  default: "bg-primary/10 text-primary",
  success: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  warning: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  danger: "bg-red-50 text-red-700 ring-1 ring-red-200",
  info: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  muted: "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({
  status,
  unsupportedDepartment,
  detailed = false,
}: {
  status: string;
  unsupportedDepartment?: boolean;
  detailed?: boolean;
}) {
  if (detailed) {
    const map: Record<string, BadgeVariant> = {
      submitted: "muted",
      pending: "warning",
      ai_processing: "info",
      ai_processed: "info",
      routed_to_department: "info",
      verified: "info",
      assigned: "info",
      work_started: "warning",
      in_progress: "warning",
      work_completed: "success",
      resolved: "success",
      feedback_received: "success",
      closed: "muted",
      rejected: "danger",
    };
    return <Badge variant={map[status] || "muted"}>{stepLabel(status)}</Badge>;
  }
  const group = publicStatus(status);
  const map: Record<string, BadgeVariant> = {
    submitted: "muted",
    in_progress: "info",
    resolved: "success",
    rejected: "danger",
  };
  return (
    <Badge variant={map[group] || "muted"}>
      {statusLabel(status, { unsupportedDepartment })}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const label = priorityLabel(priority);
  const map: Record<string, BadgeVariant> = {
    Low: "muted",
    Medium: "info",
    High: "warning",
  };
  return <Badge variant={map[label] || "muted"}>{label}</Badge>;
}
