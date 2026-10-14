"use client";

import { Badge } from "@/components/ui/badge";
import type { StaffRow } from "@/components/admin/people/types";
import { fieldAreaTextClassName } from "@/lib/staffDisplay";
import { cn } from "@/lib/utils";

export function PersonTable({
  rows,
  showDepartment = false,
  showStatus = true,
  showWorkload = false,
  showFieldArea = false,
  emptyMessage = "No one listed yet.",
}: {
  rows: StaffRow[];
  showDepartment?: boolean;
  showStatus?: boolean;
  showWorkload?: boolean;
  showFieldArea?: boolean;
  emptyMessage?: string;
}) {
  if (rows.length === 0) {
    return (
      <div className="px-5 py-10 text-center text-sm text-muted-foreground">{emptyMessage}</div>
    );
  }

  return (
    <table className="w-full text-sm table-fixed sm:table-auto">
      <thead>
        <tr className="border-b bg-muted/40">
          <th className="px-5 py-3 text-left font-medium text-muted-foreground">Name</th>
          <th className="px-5 py-3 text-left font-medium text-muted-foreground">Email</th>
          <th className="px-5 py-3 text-left font-medium text-muted-foreground">Phone</th>
          {showDepartment && (
            <th className="px-5 py-3 text-left font-medium text-muted-foreground">Department</th>
          )}
          {showFieldArea && (
            <th className="px-5 py-3 text-left font-medium text-muted-foreground min-w-[14rem] sm:min-w-[18rem]">
              Field area
            </th>
          )}
          {showWorkload && (
            <th className="px-5 py-3 text-left font-medium text-muted-foreground">Active cases</th>
          )}
          {showStatus && (
            <th className="px-5 py-3 text-left font-medium text-muted-foreground">Status</th>
          )}
        </tr>
      </thead>
      <tbody>
        {rows.map((u) => (
          <tr key={u.id} className="border-b last:border-0 hover:bg-muted/20">
            <td className="px-5 py-3.5">
              <div className="font-medium">{u.full_name}</div>
              {!showFieldArea && u.service_area && (
                <div className={cn("text-xs text-muted-foreground mt-0.5", fieldAreaTextClassName)}>
                  {u.service_area}
                </div>
              )}
            </td>
            <td className="px-5 py-3.5 text-muted-foreground">{u.email}</td>
            <td className="px-5 py-3.5 text-muted-foreground">{u.phone || "—"}</td>
            {showFieldArea && (
              <td className={cn("px-5 py-3.5 text-muted-foreground align-top", fieldAreaTextClassName)}>
                {u.service_area || "—"}
              </td>
            )}
            {showDepartment && (
              <td className="px-5 py-3.5 text-muted-foreground">
                {u.department_code ? (
                  <>
                    <span className="font-mono text-xs text-foreground">{u.department_code}</span>
                    {u.department_name ? ` · ${u.department_name}` : ""}
                  </>
                ) : (
                  "—"
                )}
              </td>
            )}
            {showWorkload && (
              <td className="px-5 py-3.5 text-muted-foreground">{u.active_assigned_count ?? 0}</td>
            )}
            {showStatus && (
              <td className="px-5 py-3.5">
                <Badge variant={u.is_active ? "success" : "danger"}>
                  {u.is_active ? "Active" : "Inactive"}
                </Badge>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
