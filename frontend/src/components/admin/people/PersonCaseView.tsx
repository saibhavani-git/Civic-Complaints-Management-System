"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle, Clock, Loader2, MapPin } from "lucide-react";
import { adminApi } from "@/lib/api";
import { PageHeader, StatCard } from "@/components/layout/PageHeader";
import { RoleBadge } from "@/components/account/RoleBadge";
import { Badge, PriorityBadge, StatusBadge } from "@/components/ui/badge";
import type { PersonCase, PersonCaseReport } from "@/components/admin/people/types";
import { priorityLabel, statusLabel } from "@/lib/complaintStatus";
import { formatDate } from "@/lib/utils";
import { normalizeRole } from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";

function categoryLabel(category?: string | null) {
  if (!category) return null;
  const known: Record<string, string> = {
    garbage: "Garbage",
    road_damage: "Road damage",
    water: "Water",
    electricity: "Electricity",
    traffic: "Traffic",
    parks: "Parks",
    other: "Other",
  };
  return known[category] ?? category.replace(/_/g, " ");
}

const BACK: Record<string, { href: string; label: string }> = {
  admin: { href: "/admin/staff/administrators", label: "Administrators" },
  dept_admin: { href: "/admin/staff/department-heads", label: "Department heads" },
  officer: { href: "/admin/staff/field-staff", label: "Field staff" },
  citizen: { href: "/admin/staff/residents", label: "Residents" },
};

const PRIORITY_LEVELS = [
  { key: "high", title: "High priority", empty: "No high priority cases." },
  { key: "medium", title: "Medium priority", empty: "No medium priority cases." },
  { key: "low", title: "Low priority", empty: "No low priority cases." },
] as const;

function priorityLevel(priority: string) {
  if (priority === "critical" || priority === "high") return "high";
  if (priority === "low") return "low";
  return "medium";
}

const COPY = {
  assigned: {
    lead: "Complaints this officer has solved, and the ones they are solving now.",
    solved: "Complaints solved",
    current: "Currently solving",
    solvedHint: "Finished or closed while assigned to this officer.",
    solvedEmpty: "No complaints solved yet.",
    currentHint: "Assigned work that is still open.",
    currentEmpty: "Not solving any complaints right now.",
  },
  reported: {
    lead: "Complaints this resident filed that are solved, and the ones still being solved.",
    solved: "Complaints solved",
    current: "Still being solved",
    solvedHint: "Reports that have been resolved or closed.",
    solvedEmpty: "No solved complaints yet.",
    currentHint: "Reports that are still open.",
    currentEmpty: "No open complaints.",
  },
  department: {
    lead: "Complaints solved in this department, and the ones still being solved.",
    solved: "Complaints solved",
    current: "Currently solving",
    solvedHint: "Department complaints that are finished or closed.",
    solvedEmpty: "No complaints solved yet.",
    currentHint: "Department complaints that are still open.",
    currentEmpty: "Nothing is being solved right now.",
  },
  none: {
    lead: "Complaints this person has solved, and the ones they are solving now.",
    solved: "Complaints solved",
    current: "Currently solving",
    solvedHint: "Finished complaints linked to this person.",
    solvedEmpty: "No complaints solved yet.",
    currentHint: "Open complaints linked to this person.",
    currentEmpty: "Not solving any complaints right now.",
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
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Labels</span>
            <StatusBadge status={item.status} />
            <PriorityBadge priority={item.priority} />
            {categoryLabel(item.category) && <Badge variant="muted">{categoryLabel(item.category)}</Badge>}
            {(item.department_code || item.department_name) && (
              <Badge variant="info">
                {item.department_code ? `${item.department_code} · ` : ""}
                {item.department_name || "Department"}
              </Badge>
            )}
          </div>
          <p className="mt-1.5 text-xs text-muted-foreground">
            Status: {statusLabel(item.status)}
            {" · "}
            Priority: {priorityLabel(item.priority)}
            {categoryLabel(item.category) ? ` · Category: ${categoryLabel(item.category)}` : ""}
            {item.department_name ? ` · Department: ${item.department_name}` : ""}
          </p>
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

export function PersonCaseView({ userId }: { userId: string }) {
  const { user } = useAuth();
  const viewerIsDeptAdmin = normalizeRole(user?.role) === "dept_admin";
  const viewerBack = viewerIsDeptAdmin
    ? { href: "/admin/team", label: "Field team" }
    : null;
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
        <PageHeader
          title="Person"
          backHref={viewerBack?.href ?? "/admin/staff/field-staff"}
          backLabel={viewerBack?.label ?? "Staff"}
        />
        <p className="text-sm text-destructive">Could not load this person. They may have been removed.</p>
      </div>
    );
  }

  const { person, summary } = data;
  const role = normalizeRole(person.role);
  const back = viewerBack ?? BACK[role] ?? BACK.officer;
  const scope = COPY[person.scope] ?? COPY.none;
  const isSystemAdmin = normalizeRole(person.role) === "admin";
  const isOfficer = person.scope === "assigned";
  const showReporter = person.scope === "assigned" || person.scope === "department";
  const showOfficer = person.scope === "reported" || person.scope === "department";

  return (
    <div>
      <PageHeader
        title={person.full_name}
        description={isSystemAdmin ? "System administrators do not handle cases." : scope.lead}
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

      {isSystemAdmin ? null : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4">
            <StatCard label={scope.solved} value={summary.solved} icon={CheckCircle} iconClassName="bg-emerald-50 [&>svg]:text-emerald-600" />
            <StatCard label={scope.current} value={summary.current} icon={Clock} iconClassName="bg-orange-50 [&>svg]:text-orange-600" />
          </div>

          <div className="space-y-4">
            <CaseSection
              title={scope.solved}
              hint={scope.solvedHint}
              items={data.solved}
              total={summary.solved}
              empty={scope.solvedEmpty}
              showReporter={showReporter}
              showOfficer={showOfficer}
            />
            {isOfficer ? (
              <section className="space-y-3">
                <h2 className="text-sm font-semibold">{scope.current}</h2>
                <p className="text-xs text-muted-foreground -mt-2">{scope.currentHint}</p>
                {PRIORITY_LEVELS.map((level) => {
                  const items = data.current.filter((item) => priorityLevel(item.priority) === level.key);
                  return (
                    <CaseSection
                      key={level.key}
                      title={level.title}
                      hint={`${items.length} open ${level.key} priority ${items.length === 1 ? "case" : "cases"}.`}
                      items={items}
                      total={items.length}
                      empty={level.empty}
                      showReporter={showReporter}
                      showOfficer={showOfficer}
                    />
                  );
                })}
              </section>
            ) : (
              <CaseSection
                title={scope.current}
                hint={scope.currentHint}
                items={data.current}
                total={summary.current}
                empty={scope.currentEmpty}
                showReporter={showReporter}
                showOfficer={showOfficer}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
