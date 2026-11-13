"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRole } from "@/lib/roles";

const TABS = [
  { href: "/admin/staff/administrators", label: "Administrators" },
  { href: "/admin/staff/department-heads", label: "Department heads" },
  { href: "/admin/staff/field-staff", label: "Field staff" },
  { href: "/admin/staff/residents", label: "Residents" },
];

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const role = user ? normalizeRole(user.role) : null;
  const isPersonDetail = pathname.startsWith("/admin/staff/people/");
  const deptAdminViewingPerson = role === "dept_admin" && isPersonDetail;

  useEffect(() => {
    if (isLoading) return;
    if (role === "admin" || deptAdminViewingPerson) return;
    if (role) router.replace("/admin/dashboard");
  }, [isLoading, role, router, deptAdminViewingPerson]);

  if (isLoading || !role) {
    return null;
  }

  if (deptAdminViewingPerson) {
    return <div>{children}</div>;
  }

  if (role !== "admin") {
    return null;
  }

  return (
    <div>
      <nav className="mb-6 flex flex-wrap gap-1 border-b border-border pb-px">
        {TABS.map((tab) => {
          const active = pathname === tab.href || pathname.startsWith(tab.href + "/");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                active
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
