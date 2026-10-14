"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { RoleShell } from "@/components/layout/RoleShell";
import { PortalFrame, PortalSidebar } from "@/components/layout/PortalSidebar";
import { adminNavLinks, adminPortalTitle, citizenNav, officerNav } from "@/lib/portalNav";
import { getDashboardPath, getNotificationsPath, normalizeRole } from "@/lib/roles";

export function PortalWrapper({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !user) return;
    const role = normalizeRole(user.role);
    if (role !== "citizen" && window.location.pathname === "/notifications") {
      router.replace(getNotificationsPath(role));
    }
  }, [user, loading, router]);

  if (loading) {
    return <div className="flex items-center justify-center py-24 text-muted-foreground">Loading...</div>;
  }
  if (!user) return <>{children}</>;

  const role = normalizeRole(user.role);

  if (role === "citizen") {
    return (
      <RoleShell title="Citizen" links={citizenNav} allowedRoles={["citizen"]}>
        {children}
      </RoleShell>
    );
  }
  if (role === "officer") {
    return (
      <RoleShell title="Officer" links={officerNav} allowedRoles={["officer"]}>
        {children}
      </RoleShell>
    );
  }
  if (role === "admin" || role === "dept_admin") {
    return (
      <PortalFrame
        sidebar={
          <PortalSidebar
            title={adminPortalTitle(role)}
            links={adminNavLinks(role)}
            user={user}
            onLogout={logout}
          />
        }
      >
        {children}
      </PortalFrame>
    );
  }

  router.replace(getDashboardPath(role));
  return null;
}
