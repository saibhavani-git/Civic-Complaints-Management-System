"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { complaintsApi } from "@/lib/api";
import { complaintsListKey } from "@/lib/complaintQueries";
import { ComplaintCard } from "@/components/complaints/ComplaintCard";
import { ComplaintFilters } from "@/components/complaints/ComplaintShared";
import { PageHeader, EmptyState } from "@/components/layout/PageHeader";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRole } from "@/lib/roles";
import { userDepartmentLabel } from "@/lib/staffDisplay";
import { ClipboardList, Loader2 } from "lucide-react";
import type { Complaint } from "@/types";
import { complaintsLoadErrorMessage } from "@/lib/complaintListError";
import { apiStatusParam, type ComplaintFilterRole } from "@/lib/complaintFilters";

export default function AdminComplaintsPage() {
  const { user } = useAuth();
  const role = normalizeRole(user?.role);
  const isSystemAdmin = role === "admin";
  const isDeptAdmin = role === "dept_admin";
  const filterRole: ComplaintFilterRole = isSystemAdmin ? "admin" : "dept_admin";
  const deptLabel = user ? userDepartmentLabel(user) : null;
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [awaitingAssignment, setAwaitingAssignment] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: complaintsListKey(user?.id, filterRole, { status, priority, awaiting_assignment: awaitingAssignment }),
    queryFn: () =>
      complaintsApi
        .list({
          status: awaitingAssignment ? undefined : apiStatusParam(filterRole, status),
          priority: priority || undefined,
          awaiting_assignment: isDeptAdmin && awaitingAssignment ? true : undefined,
          limit: 100,
        })
        .then((r) => r.data),
    enabled: !!user?.id,
  });

  const complaints: Complaint[] = data?.items || [];

  return (
    <div>
      <PageHeader
        title={isSystemAdmin ? "All complaints" : "Department queue"}
        description={
          isSystemAdmin
            ? `${data?.total || 0} complaints city-wide`
            : isDeptAdmin
              ? `${data?.total || 0} complaints for ${deptLabel ?? "your department"} — assign officers from each case`
              : `${data?.total || 0} complaints in your department`
        }
      />

      <div className="mb-6">
        <ComplaintFilters
          filterRole={filterRole}
          status={status}
          priority={priority}
          onStatusChange={setStatus}
          onPriorityChange={setPriority}
          awaitingAssignment={awaitingAssignment}
          onAwaitingAssignmentChange={
            isDeptAdmin
              ? (v) => {
                  setAwaitingAssignment(v);
                  if (v) setStatus("");
                }
              : undefined
          }
        />
      </div>

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 mb-6">
          {complaintsLoadErrorMessage(error)}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground py-12">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading...
        </div>
      ) : isError ? null : complaints.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No complaints"
          description={
            isSystemAdmin
              ? "No complaints in the system yet."
              : isDeptAdmin
                ? "No complaints routed to your department yet (initial routing may still be in progress)."
                : "No complaints match your filters."
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {complaints.map((c) => (
            <ComplaintCard key={c.id} complaint={c} href={`/admin/complaints/${c.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
