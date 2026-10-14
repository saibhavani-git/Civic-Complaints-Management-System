"use client";

import { cn } from "@/lib/utils";
import { normalizeRole, roleLabel } from "@/lib/roles";
import type { UserRole } from "@/types";

const ROLE_STYLES: Record<UserRole, string> = {
  citizen: "bg-sky-100 text-sky-800 ring-sky-200",
  officer: "bg-violet-100 text-violet-800 ring-violet-200",
  dept_admin: "bg-amber-100 text-amber-900 ring-amber-200",
  admin: "bg-slate-800 text-white ring-slate-600",
};

export function RoleBadge({
  role,
  className,
  size = "default",
}: {
  role: unknown;
  className?: string;
  size?: "sm" | "default";
}) {
  const normalized = normalizeRole(role);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-semibold ring-1",
        size === "sm" ? "px-2 py-0.5 text-[10px] uppercase tracking-wide" : "px-2.5 py-0.5 text-xs",
        ROLE_STYLES[normalized],
        className
      )}
    >
      {roleLabel(role)}
    </span>
  );
}
