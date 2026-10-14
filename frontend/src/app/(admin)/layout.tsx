"use client";

import { useAuth } from "@/hooks/useAuth";
import { RoleRedirect } from "@/components/layout/RoleRedirect";
import { PortalFrame, PortalSidebar } from "@/components/layout/PortalSidebar";
import { adminNavLinks, adminPortalTitle } from "@/lib/portalNav";
import { normalizeRole } from "@/lib/roles";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();

  return (
    <RoleRedirect allowedRoles={["admin", "dept_admin"]}>
      {loading || !user ? (
        <div className="flex items-center justify-center py-24">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : (
        <PortalFrame
          sidebar={
            <PortalSidebar
              title={adminPortalTitle(normalizeRole(user.role))}
              links={adminNavLinks(normalizeRole(user.role))}
              user={user}
              onLogout={logout}
            />
          }
        >
          {children}
        </PortalFrame>
      )}
    </RoleRedirect>
  );
}
