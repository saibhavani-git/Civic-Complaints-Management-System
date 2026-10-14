"use client";

import { RoleShell } from "@/components/layout/RoleShell";
import { RoleRedirect } from "@/components/layout/RoleRedirect";
import { officerNav } from "@/lib/portalNav";

export default function OfficerLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleRedirect allowedRoles={["officer"]}>
      <RoleShell title="Officer" links={officerNav} allowedRoles={["officer"]}>
        {children}
      </RoleShell>
    </RoleRedirect>
  );
}
