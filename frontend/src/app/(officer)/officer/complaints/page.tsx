"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { complaintsApi } from "@/lib/api";
import { complaintsListKey } from "@/lib/complaintQueries";
import { useAuth } from "@/hooks/useAuth";
import { ComplaintCard } from "@/components/complaints/ComplaintCard";
import { ComplaintFilters } from "@/components/complaints/ComplaintShared";
import { PageHeader, EmptyState } from "@/components/layout/PageHeader";
import { ClipboardList, Loader2, MapPin } from "lucide-react";
import { fieldAreaTextClassName } from "@/lib/staffDisplay";
import { cn } from "@/lib/utils";
import type { Complaint } from "@/types";
import { complaintsLoadErrorMessage } from "@/lib/complaintListError";
import { officerServiceAreaLabel, userDepartmentLabel } from "@/lib/staffDisplay";
import { apiStatusParam } from "@/lib/complaintFilters";

export default function OfficerComplaintsPage() {
  const { user } = useAuth();
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: complaintsListKey(user?.id, "officer", { status, priority }),
    queryFn: () =>
      complaintsApi
        .list({
          status: apiStatusParam("officer", status),
          priority: priority || undefined,
          limit: 100,
        })
        .then(
        (r) => r.data
      ),
    enabled: !!user?.id,
  });

  const complaints: Complaint[] = data?.items || [];
  const dept = user ? userDepartmentLabel(user) : null;
  const area = user ? officerServiceAreaLabel(user) : null;
  return (
    <div>
      <PageHeader
        title="My Cases"
        description={
          dept
            ? `${dept} — assigned complaints, highest priority first`
            : "Assigned complaints, highest priority first (critical → high → medium → low)"
        }
      />

      {area && (
        <div className={cn("flex gap-2 text-sm text-muted-foreground mb-6 -mt-4", fieldAreaTextClassName)}>
          <MapPin className="h-4 w-4 shrink-0 text-primary mt-0.5" aria-hidden />
          <p>
            <span className="font-medium text-foreground">Field area: </span>
            {area}
          </p>
        </div>
      )}

      <div className="mb-6">
        <ComplaintFilters
          filterRole="officer"
          status={status}
          priority={priority}
          onStatusChange={setStatus}
          onPriorityChange={setPriority}
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
          title="No assigned cases"
          description="Your department admin assigns complaints to you — they will appear here."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {complaints.map((c) => (
            <ComplaintCard key={c.id} complaint={c} href={`/officer/complaints/${c.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
