"use client";

import { formatDate } from "@/lib/utils";
import { StatusBadge, PriorityBadge } from "@/components/ui/badge";
import type { Complaint } from "@/types";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRole } from "@/lib/roles";
import Link from "next/link";
import { ChevronRight, MapPin } from "lucide-react";

interface ComplaintCardProps {
  complaint: Complaint;
  href?: string;
}

export function ComplaintCard({ complaint, href }: ComplaintCardProps) {
  const { user } = useAuth();
  const isCitizen = user ? normalizeRole(user.role) === "citizen" : false;
  const ai = complaint.ai_metadata as { unsupported_department?: boolean; routing?: { unsupported?: boolean } } | undefined;
  const unsupportedDepartment = Boolean(ai?.unsupported_department || ai?.routing?.unsupported);

  const content = (
    <article className="group theme-card p-5 transition-all hover:border-primary/30 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-muted-foreground">
            Ref. <span className="font-medium text-foreground">{complaint.complaint_id}</span>
          </p>
          <h3 className="mt-1 font-semibold text-foreground truncate group-hover:text-primary transition-colors">
            {complaint.title}
          </h3>
          {!isCitizen && (complaint.citizen_name || complaint.citizen_phone) && (
            <p className="mt-1 text-xs text-muted-foreground truncate">
              Reporter: {complaint.citizen_name || "Resident"}
              {complaint.citizen_phone ? ` · ${complaint.citizen_phone}` : ""}
            </p>
          )}
          {isCitizen && complaint.assigned_officer_name && (
            <p className="mt-1 text-xs text-muted-foreground truncate">
              Officer: {complaint.assigned_officer_name}
            </p>
          )}
        </div>
        <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <StatusBadge status={complaint.status} unsupportedDepartment={unsupportedDepartment} />
        {!isCitizen && <PriorityBadge priority={complaint.priority} />}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="flex items-center gap-1 truncate">
          <MapPin className="h-3 w-3 shrink-0" />
          {complaint.location?.address?.split(",")[0] || "Location set"}
        </span>
        <span>{formatDate(complaint.created_at)}</span>
      </div>

      {complaint.department_name && (
        <p className="mt-2 text-xs font-medium text-primary">{complaint.department_name}</p>
      )}
    </article>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}
