"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardPath, normalizeRole, roleLabel } from "@/lib/roles";
import { RoleBadge } from "@/components/account/RoleBadge";
import type { UserRole } from "@/types";
import { PortalFrame, PortalSidebar, type NavLink } from "@/components/layout/PortalSidebar";

interface RoleShellProps {
  title: string;
  links: NavLink[];
  allowedRoles: UserRole[];
  children: React.ReactNode;
}

export function RoleShell({ title, links, allowedRoles, children }: RoleShellProps) {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const role = user ? normalizeRole(user.role) : null;
  if (!user || !role || !allowedRoles.includes(role)) {
    return (
      <div className="page-container py-24 text-center">
        <h1 className="text-xl font-semibold">Access denied</h1>
        {user && role && (
          <p className="text-sm text-muted-foreground mt-2 flex items-center justify-center gap-2">
            Signed in as <RoleBadge role={role} size="sm" /> ({roleLabel(role)})
          </p>
        )}
        <p className="text-sm text-muted-foreground mt-2 mb-6">
          This page is for {allowedRoles.map(roleLabel).join(" or ")} accounts only.
        </p>
        <Link
          href={user ? getDashboardPath(role!) : "/login"}
          className="text-sm font-medium text-primary hover:underline"
        >
          {user ? "Go to your portal" : "Log in"}
        </Link>
      </div>
    );
  }

  return (
    <PortalFrame
      sidebar={
        <PortalSidebar title={title} links={links} user={user} onLogout={logout} />
      }
    >
      {children}
    </PortalFrame>
  );
}

export type { NavLink };
