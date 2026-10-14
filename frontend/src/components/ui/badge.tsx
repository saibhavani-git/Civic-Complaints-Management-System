"use client";

import { cn } from "@/lib/utils";
import { statusLabel } from "@/lib/complaintStatus";

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
}: {
  status: string;
  unsupportedDepartment?: boolean;
}) {
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
    resolved: "success",
    feedback_received: "success",
    closed: "muted",
    rejected: "danger",
  };
  return (
    <Badge variant={map[status] || "muted"}>
      {statusLabel(status, { unsupportedDepartment })}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, BadgeVariant> = {
    low: "muted",
    medium: "info",
    high: "warning",
    critical: "danger",
  };
  return <Badge variant={map[priority] || "muted"}>{priority}</Badge>;
}
