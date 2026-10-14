"use client";

import { RoleShell } from "@/components/layout/RoleShell";
import { RoleRedirect } from "@/components/layout/RoleRedirect";
import { citizenNav } from "@/lib/portalNav";

export default function CitizenLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleRedirect allowedRoles={["citizen"]}>
      <RoleShell title="Citizen" links={citizenNav} allowedRoles={["citizen"]}>
        {children}
      </RoleShell>
    </RoleRedirect>
  );
}
