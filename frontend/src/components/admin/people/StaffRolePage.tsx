"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { AddButton } from "@/components/admin/AdminForms";
import { CreateStaffForm } from "@/components/admin/people/CreateStaffForm";
import { PersonTable } from "@/components/admin/people/PersonTable";
import type { StaffRow } from "@/components/admin/people/types";
import { Loader2 } from "lucide-react";
import type { UserRole } from "@/types";

type StaffRole = Extract<UserRole, "admin" | "dept_admin" | "officer" | "citizen">;

const PAGE: Record<
  StaffRole,
  { title: string; description: string; addLabel?: string; readOnly?: boolean; groupByDept?: boolean }
> = {
  admin: {
    title: "System administrators",
    description: "Platform-wide access",
    addLabel: "Add administrator",
  },
  dept_admin: {
    title: "Department heads",
    description: "One lead per department queue",
    addLabel: "Add department head",
    groupByDept: true,
  },
  officer: {
    title: "Field officers",
    description: "Staff who resolve assigned complaints",
    addLabel: "Add officer",
    groupByDept: true,
  },
  citizen: {
    title: "Registered residents",
    description: "Created via public sign-up — view only",
    readOnly: true,
  },
};

function groupByDepartment(rows: StaffRow[]) {
  const map = new Map<string, StaffRow[]>();
  for (const u of rows) {
    const key = u.department_id || "__none__";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(u);
  }
  return [...map.entries()]
    .map(([key, items]) => ({
      key,
      label:
        key === "__none__"
          ? "Unassigned"
          : `${items[0].department_code ?? ""} · ${items[0].department_name ?? "Department"}`.trim(),
      items,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
}

export function StaffRolePage({ role }: { role: StaffRole }) {
  const meta = PAGE[role];
  const [showForm, setShowForm] = useState(false);

  const { data: all = [], isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminApi.listUsers().then((r) => r.data as StaffRow[]),
  });

  const rows = useMemo(() => all.filter((u) => u.role === role), [all, role]);

  const canCreate = role === "admin" || role === "dept_admin" || role === "officer";

  return (
    <div>
      <PageHeader
        title={meta.title}
        description={`${rows.length} ${rows.length === 1 ? "person" : "people"} · ${meta.description}`}
        action={
          !meta.readOnly && canCreate ? (
            <AddButton label={meta.addLabel!} onClick={() => setShowForm(true)} />
          ) : undefined
        }
      />

      {showForm && canCreate && role !== "citizen" ? (
        <CreateStaffForm role={role as "admin" | "dept_admin" | "officer"} onClose={() => setShowForm(false)} />
      ) : isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground py-12">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading…
        </div>
      ) : meta.groupByDept ? (
        <div className="space-y-4">
          {groupByDepartment(rows).map((g) => (
            <div key={g.key} className="rounded-xl border bg-card shadow-sm overflow-hidden">
              <div className="border-b bg-muted/30 px-5 py-2.5 text-sm font-medium">{g.label}</div>
              <PersonTable
                rows={g.items}
                showDepartment={false}
                showFieldArea={role === "officer"}
              />
            </div>
          ))}
          {rows.length === 0 && (
            <div className="rounded-xl border bg-card shadow-sm">
              <PersonTable rows={[]} emptyMessage="No one in this category yet." />
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <PersonTable
            rows={rows}
            showDepartment={role === "officer" || role === "dept_admin"}
            showFieldArea={role === "officer"}
            emptyMessage={role === "citizen" ? "No registered residents yet." : "No one in this category yet."}
          />
        </div>
      )}
    </div>
  );
}
