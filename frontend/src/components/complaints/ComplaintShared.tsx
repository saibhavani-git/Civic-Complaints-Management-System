"use client";

import { StatusBadge, PriorityBadge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { Complaint } from "@/types";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRole } from "@/lib/roles";
import { sanitizeTimelineNote } from "@/lib/timelineNotes";
import {
  type ComplaintFilterRole,
  showAwaitingAssignmentFilter,
  showPriorityFilter,
  statusFilterOptions,
} from "@/lib/complaintFilters";

function timelineEntriesForDisplay(history: Complaint["status_history"]) {
  const chronological = [...(history ?? [])].reverse();
  const out: typeof chronological = [];
  for (const entry of chronological) {
    const prev = out[out.length - 1];
    if (prev && prev.status === entry.status) continue;
    out.push(entry);
  }
  return out;
}

export function ComplaintTimeline({
  history,
  showNotes = true,
}: {
  history: Complaint["status_history"];
  showNotes?: boolean;
}) {
  const entries = timelineEntriesForDisplay(history);
  if (!entries.length) return null;

  return (
    <div className="space-y-0">
      {entries.map((entry, i) => (
        <div
          key={`${entry.status}-${entry.changed_at}-${i}`}
          className="flex gap-3 pb-4 last:pb-0"
        >
          <div className="flex flex-col items-center">
            <div className="h-2.5 w-2.5 rounded-full bg-primary ring-4 ring-primary/20" />
            {i < entries.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
          </div>
          <div className="flex-1 pb-2">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={entry.status} />
              <span className="text-xs text-muted-foreground">{formatDate(entry.changed_at)}</span>
            </div>
            {showNotes && (() => {
              const note = sanitizeTimelineNote(entry.note);
              return note ? (
                <p className="text-sm text-muted-foreground mt-1">{note}</p>
              ) : null;
            })()}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ComplaintFilters({
  filterRole,
  status,
  priority,
  onStatusChange,
  onPriorityChange,
  awaitingAssignment,
  onAwaitingAssignmentChange,
}: {
  filterRole: ComplaintFilterRole;
  status: string;
  priority: string;
  onStatusChange: (v: string) => void;
  onPriorityChange: (v: string) => void;
  awaitingAssignment?: boolean;
  onAwaitingAssignmentChange?: (v: boolean) => void;
}) {
  const statusOptions = statusFilterOptions(filterRole);
  const showAwaiting = showAwaitingAssignmentFilter(filterRole) && onAwaitingAssignmentChange;
  const showPriority = showPriorityFilter(filterRole);

  return (
    <div className="flex flex-wrap items-center gap-3">
      {showAwaiting && (
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer select-none rounded-lg border border-input bg-background px-3 py-2">
          <input
            type="checkbox"
            checked={!!awaitingAssignment}
            onChange={(e) => onAwaitingAssignmentChange(e.target.checked)}
            className="rounded border-input"
          />
          Needs officer assignment
        </label>
      )}
      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
        disabled={!!awaitingAssignment}
        aria-label="Filter by status"
        className="h-9 rounded-lg border border-input bg-background px-3 text-sm disabled:opacity-50 min-w-[10rem]"
      >
        {statusOptions.map((opt) => (
          <option key={opt.value || "__all"} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {showPriority && (
        <select
          value={priority}
          onChange={(e) => onPriorityChange(e.target.value)}
          aria-label="Filter by priority"
          className="h-9 rounded-lg border border-input bg-background px-3 text-sm min-w-[9rem]"
        >
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      )}
    </div>
  );
}

export function ComplaintMeta({ complaint }: { complaint: Complaint }) {
  const { user } = useAuth();
  const role = user ? normalizeRole(user.role) : null;
  const isCitizen = role === "citizen";
  const ai = complaint.ai_metadata as { unsupported_department?: boolean; routing?: { unsupported?: boolean } } | undefined;
  const unsupportedDepartment = Boolean(ai?.unsupported_department || ai?.routing?.unsupported);
  return (
    <div className="flex flex-wrap gap-2">
      <StatusBadge status={complaint.status} unsupportedDepartment={unsupportedDepartment} />
      {!isCitizen && <PriorityBadge priority={complaint.priority} />}
    </div>
  );
}
