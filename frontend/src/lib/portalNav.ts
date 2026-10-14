import { LayoutDashboard, PlusCircle, User, ClipboardList, ShieldCheck, HardHat, Building2 } from "lucide-react";
import type { NavLink } from "@/components/layout/PortalSidebar";
import type { UserRole } from "@/types";

/** Citizen: submit + track only (+ account). Notifications live in the header bell. */
export const citizenNav: NavLink[] = [
  { href: "/dashboard", label: "My complaints", icon: LayoutDashboard },
  { href: "/complaints/new", label: "Report issue", icon: PlusCircle },
  { href: "/profile", label: "Account", icon: User },
];

/** Officer: work queue only. */
export const officerNav: NavLink[] = [
  { href: "/officer/complaints", label: "My cases", icon: ClipboardList },
  { href: "/officer/account", label: "Account", icon: User },
];

type AdminNavItem = NavLink & { roles: UserRole[] };

const adminItems: AdminNavItem[] = [
  { href: "/admin/dashboard", label: "Overview", icon: LayoutDashboard, roles: ["admin", "dept_admin"] },
  {
    href: "/admin/complaints",
    label: "Complaints",
    icon: ClipboardList,
    roles: ["admin", "dept_admin"],
  },
  { href: "/admin/staff/administrators", label: "Staff", icon: ShieldCheck, roles: ["admin"] },
  { href: "/admin/team", label: "Field team", icon: HardHat, roles: ["dept_admin"] },
  { href: "/admin/departments", label: "Departments", icon: Building2, roles: ["admin"] },
  { href: "/admin/account", label: "Account", icon: User, roles: ["admin", "dept_admin"] },
];

export function adminNavLinks(role: UserRole): NavLink[] {
  return adminItems.filter((l) => l.roles.includes(role)).map(({ roles: _r, ...link }) => link);
}

export function adminPortalTitle(role: UserRole): string {
  return role === "admin" ? "System admin" : "Department admin";
}
