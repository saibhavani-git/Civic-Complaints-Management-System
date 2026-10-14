"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardPath, normalizeRole } from "@/lib/roles";
import type { UserRole } from "@/types";

/**
 * Sends users to their home portal when they open a route meant for another role.
 */
export function RoleRedirect({
  allowedRoles,
  children,
}: {
  allowedRoles: UserRole[];
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading || !user) return;
    const role = normalizeRole(user.role);
    if (!allowedRoles.includes(role)) {
      router.replace(getDashboardPath(role));
    }
  }, [user, loading, allowedRoles, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="page-container py-24 text-center">
        <p className="text-muted-foreground">Please log in to continue.</p>
        <a href="/login" className="text-sm text-primary hover:underline mt-4 inline-block">
          Go to log in
        </a>
      </div>
    );
  }

  const role = normalizeRole(user.role);
  if (!allowedRoles.includes(role)) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground text-sm">
        Redirecting to your portal…
      </div>
    );
  }

  return <>{children}</>;
}
