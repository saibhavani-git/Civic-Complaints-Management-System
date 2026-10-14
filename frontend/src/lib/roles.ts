import type { UserRole } from "@/types";

const VALID_ROLES: UserRole[] = ["citizen", "officer", "dept_admin", "admin"];

/** Normalize API / legacy role strings for routing. */
export function normalizeRole(role: unknown): UserRole {
  const raw = String(role ?? "citizen").toLowerCase().trim();
  if (raw === "dept-admin" || raw === "department_admin") return "dept_admin";
  if (raw === "super_admin" || raw === "superadmin") return "admin";
  if (VALID_ROLES.includes(raw as UserRole)) return raw as UserRole;
  return "citizen";
}

export function getDashboardPath(role: unknown): string {
  switch (normalizeRole(role)) {
    case "admin":
    case "dept_admin":
      return "/admin/dashboard";
    case "officer":
      return "/officer/complaints";
    default:
      return "/dashboard";
  }
}

export function getNotificationsPath(role: unknown): string {
  switch (normalizeRole(role)) {
    case "admin":
    case "dept_admin":
      return "/admin/notifications";
    case "officer":
      return "/officer/notifications";
    default:
      return "/notifications";
  }
}

export function roleLabel(role: unknown): string {
  switch (normalizeRole(role)) {
    case "admin":
      return "System admin";
    case "dept_admin":
      return "Department admin";
    case "officer":
      return "Officer";
    default:
      return "Citizen";
  }
}

export type AccountKind = "citizen" | "staff";

export function isStaffRole(role: unknown): boolean {
  const r = normalizeRole(role);
  return r === "admin" || r === "dept_admin" || r === "officer";
}
