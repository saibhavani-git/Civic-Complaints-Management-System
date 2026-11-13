"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle, Clock, Loader2, MapPin } from "lucide-react";
import { adminApi } from "@/lib/api";
import { PageHeader, StatCard } from "@/components/layout/PageHeader";
import { RoleBadge } from "@/components/account/RoleBadge";
import { Badge, PriorityBadge, StatusBadge } from "@/components/ui/badge";
import type { PersonCase, PersonCaseReport, PersonCaseSummary } from "@/components/admin/people/types";
import { formatDate } from "@/lib/utils";
import { normalizeRole } from "@/lib/roles";

const BACK: Record<string, { href: string; label: string }> = {
  admin: { href: "/admin/staff/administrators", label: "Administrators" },
  dept_admin: { href: "/admin/staff/department-heads", label: "Department heads" },
  officer: { href: "/admin/staff/field-staff", label: "Field staff" },
  citizen: { href: "/admin/staff/residents", label: "Residents" },
};

const COPY = {
  assigned: {
    lead: "Cases assigned to this officer.",
    solved: "Solved",
    current: "Current",
    critical: "Critical",
    solvedTitle: "Solved cases",
    solvedHint: "Finished or closed while assigned to this officer.",
    solvedEmpty: "No solved cases yet.",
    currentTitle: "Current cases",
    currentHint: "Open work: assigned, in progress, or waiting for a department head to close it.",
    currentEmpty: "No open cases.",
    criticalTitle: "Critical cases",
    criticalHint: "Open cases marked critical.",
    criticalEmpty: "No open critical cases.",
  },
  reported: {
    lead: "Complaints this resident filed.",
    solved: "Finished",
    current: "Open",
    critical: "Critical",
    solvedTitle: "Finished reports",
    solvedHint: "Reports that have been resolved or closed.",
    solvedEmpty: "No finished reports yet.",
    currentTitle: "Open reports",
    currentHint: "Reports that are still being handled.",
    currentEmpty: "No open reports.",
    criticalTitle: "Critical reports",
    criticalHint: "Open reports marked critical.",
    criticalEmpty: "No open critical reports.",
  },
  department: {
    lead: "Cases in this department.",
    solved: "Resolved",
    current: "Open",
    critical: "Critical",
    solvedTitle: "Resolved cases",
    solvedHint: "Department cases that are finished or closed.",
    solvedEmpty: "No resolved cases yet.",
    currentTitle: "Open cases",
    currentHint: "Still in the department queue or with a field officer.",
    currentEmpty: "No open cases.",
    criticalTitle: "Critical cases",
    criticalHint: "Open department cases marked critical.",
    criticalEmpty: "No open critical cases.",
  },
} as const;

function CaseRow({
  item,
  showReporter,
  showOfficer,
}: {
  item: PersonCase;
  showReporter: boolean;
  showOfficer: boolean;
}) {
  return (
    <Link href={`/admin/complaints/${item.id}`} className="block px-5 py-3.5 hover:bg-muted/30">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">
            Ref. <span className="font-medium text-foreground">{item.complaint_id}</span>
            {item.department_code ? ` · ${item.department_code}` : ""}
          </p>
          <p className="mt-0.5 font-medium">{item.title}</p>
          <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="truncate">{item.address || "Location set"}</span>
          </p>
          {showReporter && item.citizen_name && (
            <p className="mt-1 text-xs text-muted-foreground">Reporter: {item.citizen_name}</p>
          )}
          {showOfficer && item.officer_name && (
            <p className="mt-1 text-xs text-muted-foreground">Officer: {item.officer_name}</p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={item.status} />
          <PriorityBadge priority={item.priority} />
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {item.updated_at ? `Updated ${formatDate(item.updated_at)}` : item.created_at ? formatDate(item.created_at) : ""}
      </p>
    </Link>
  );
}

function CaseSection({
  title,
  hint,
  items,
  total,
  empty,
  showReporter,
  showOfficer,
}: {
  title: string;
  hint: string;
  items: PersonCase[];
  total: number;
  empty: string;
  showReporter: boolean;
  showOfficer: boolean;
}) {
  return (
    <section className="rounded-xl border bg-card shadow-sm overflow-hidden">
      <div className="border-b px-5 py-3">
        <h2 className="text-sm font-semibold">
          {title}
          <span className="ml-2 font-normal text-muted-foreground">{total}</span>
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>
      </div>
      {items.length === 0 ? (
        <p className="px-5 py-8 text-sm text-muted-foreground">{empty}</p>
      ) : (
        <ul className="divide-y">
          {items.map((item) => (
            <li key={item.id}>
              <CaseRow item={item} showReporter={showReporter} showOfficer={showOfficer} />
            </li>
          ))}
        </ul>
      )}
      {total > items.length && (
        <p className="border-t px-5 py-2 text-xs text-muted-foreground">
          Showing {items.length} of {total}.{" "}
          <Link href="/admin/complaints" className="text-primary hover:underline">
            All complaints
          </Link>
        </p>
      )}
    </section>
  );
}

function StageLine({ summary }: { summary: PersonCaseSummary }) {
  const chips = [
    summary.waiting_assignment > 0 ? `${summary.waiting_assignment} not yet assigned` : null,
    `${summary.assigned} assigned`,
    `${summary.in_progress} in progress`,
    `${summary.awaiting_close} awaiting close`,
    `${summary.rejected} rejected`,
    summary.critical_solved > 0 ? `${summary.critical_solved} critical already solved` : null,
  ].filter(Boolean);

  return (
    <div className="mb-8 flex flex-wrap gap-2">
      {chips.map((label) => (
        <span key={label} className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
          {label}
        </span>
      ))}
      <span className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
        {summary.resolution_rate}% resolved
      </span>
    </div>
  );
}

export function PersonCaseView({ userId }: { userId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-user-cases", userId],
    queryFn: () => adminApi.userCases(userId).then((r) => r.data as PersonCaseReport),
    enabled: Boolean(userId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-12 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div>
        <PageHeader title="Person" backHref="/admin/staff/field-staff" backLabel="Staff" />
        <p className="text-sm text-destructive">Could not load this person. They may have been removed.</p>
      </div>
    );
  }

  const { person, summary } = data;
  const role = normalizeRole(person.role);
  const back = BACK[role] ?? BACK.officer;
  const scope = person.scope === "none" ? null : COPY[person.scope];
  const showReporter = person.scope === "assigned" || person.scope === "department";
  const showOfficer = person.scope === "reported" || person.scope === "department";

  return (
    <div>
      <PageHeader
        title={person.full_name}
        description={scope?.lead ?? "System administrators are not assigned field cases."}
        backHref={back.href}
        backLabel={back.label}
      />

      <div className="mb-6 rounded-xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <RoleBadge role={person.role} />
          <Badge variant={person.is_active ? "success" : "danger"}>
            {person.is_active ? "Active" : "Inactive"}
          </Badge>
          {person.department_code && (
            <span className="text-sm text-muted-foreground">
              <span className="font-mono text-xs text-foreground">{person.department_code}</span>
              {person.department_name ? ` · ${person.department_name}` : ""}
            </span>
          )}
        </div>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-muted-foreground">Email</dt>
            <dd>{person.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Phone</dt>
            <dd>{person.phone || "—"}</dd>
          </div>
          {person.service_area && (
            <div className="sm:col-span-2">
              <dt className="text-xs text-muted-foreground">Field area</dt>
              <dd>{person.service_area}</dd>
            </div>
          )}
        </dl>
      </div>

      {!scope ? (
        <p className="text-sm text-muted-foreground">
          This account runs the platform. Open{" "}
          <Link href="/admin/complaints" className="text-primary hover:underline">
            complaints
          </Link>{" "}
          for the city-wide list.
        </p>
      ) : (
        <>
          <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-3">
            <StatCard label={scope.solved} value={summary.solved} icon={CheckCircle} iconClassName="bg-emerald-50 [&>svg]:text-emerald-600" />
            <StatCard label={scope.current} value={summary.current} icon={Clock} iconClassName="bg-orange-50 [&>svg]:text-orange-600" />
            <StatCard label={scope.critical} value={summary.critical} icon={AlertTriangle} iconClassName="bg-red-50 [&>svg]:text-red-600" />
            <StatCard label="High" value={summary.high} icon={AlertTriangle} iconClassName="bg-amber-50 [&>svg]:text-amber-600" />
            <StatCard label="Medium" value={summary.medium} icon={Clock} iconClassName="bg-blue-50 [&>svg]:text-blue-600" />
            <StatCard label="Low" value={summary.low} icon={CheckCircle} iconClassName="bg-slate-100 [&>svg]:text-slate-600" />
          </div>
          <p className="mb-3 text-xs text-muted-foreground">
            High, medium, and low counts are open cases only. Critical is the open critical count.
          </p>
          <StageLine summary={summary} />

          <div className="space-y-4">
            <CaseSection
              title={scope.criticalTitle}
              hint={scope.criticalHint}
              items={data.critical}
              total={summary.critical}
              empty={scope.criticalEmpty}
              showReporter={showReporter}
              showOfficer={showOfficer}
            />
            <CaseSection
              title={scope.currentTitle}
              hint={scope.currentHint}
              items={data.current}
              total={summary.current}
              empty={scope.currentEmpty}
              showReporter={showReporter}
              showOfficer={showOfficer}
            />
            <CaseSection
              title={scope.solvedTitle}
              hint={scope.solvedHint}
              items={data.solved}
              total={summary.solved}
              empty={scope.solvedEmpty}
              showReporter={showReporter}
              showOfficer={showOfficer}
            />
          </div>
        </>
      )}
    </div>
  );
}
