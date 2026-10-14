import type { User } from "@/types";
import { normalizeRole } from "@/lib/roles";

export function userDepartmentLabel(user: Pick<User, "role" | "department_name" | "department_code">): string | null {
  const role = normalizeRole(user.role);
  if (role !== "officer" && role !== "dept_admin") return null;
  if (user.department_name) {
    return user.department_name;
  }
  return null;
}

/** Officer beat / zone; falls back to department coverage text. */
export function officerServiceAreaLabel(
  user: Pick<User, "role" | "service_area" | "department_area">
): string | null {
  if (normalizeRole(user.role) !== "officer") return null;
  const area = user.service_area?.trim() || user.department_area?.trim();
  return area || null;
}

/** Use on any UI that shows officer field area (avoid truncate / single-line clip). */
export const fieldAreaTextClassName =
  "break-words whitespace-normal leading-relaxed [overflow-wrap:anywhere]";
