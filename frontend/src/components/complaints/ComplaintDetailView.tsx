"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { complaintsApi } from "@/lib/api";
import { complaintDetailKey } from "@/lib/complaintQueries";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardPath, normalizeRole } from "@/lib/utils";
import { ComplaintMeta, ComplaintTimeline } from "@/components/complaints/ComplaintShared";
import { OfficerActions, FeedbackForm } from "@/components/complaints/ComplaintActions";
import { AssignOfficerPanel } from "@/components/complaints/AssignOfficerPanel";
import { ComplaintProgressTracker } from "@/components/complaints/ComplaintProgressTracker";
import { MapPin, ArrowLeft, Loader2, User, Mail, Phone } from "lucide-react";

function DetailSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">{title}</h2>
      {children}
    </section>
  );
}

export function ComplaintDetailView({ backHref }: { backHref?: string }) {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const role = normalizeRole(user?.role);

  const { data: complaint, isLoading, isError } = useQuery({
    queryKey: complaintDetailKey(user?.id, id),
    queryFn: () => complaintsApi.get(id).then((r) => r.data),
    enabled: !!id && !!user?.id,
    retry: false,
  });

  const back = backHref || (user ? getDashboardPath(user.role) : "/");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading...
      </div>
    );
  }

  if (isError || !complaint) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">
          {isError ? "This complaint is not available for your account." : "Complaint not found."}
        </p>
        <Link href={back} className="text-primary text-sm mt-2 inline-block hover:underline">
          Go back
        </Link>
      </div>
    );
  }

  const ai = complaint.ai_metadata as Record<string, unknown> | undefined;
  const routing = ai?.routing as
    | { unsupported?: boolean; public_message?: string; suggested_external_department?: string }
    | undefined;
  const unsupportedDepartment = Boolean(ai?.unsupported_department || routing?.unsupported);
  const unsupportedMessage =
    (typeof ai?.public_message === "string" && ai.public_message) ||
    routing?.public_message ||
    (unsupportedDepartment
      ? "This complaint is not handled by any department on this portal."
      : undefined);
  const showFeedback = role === "citizen" && complaint.status === "resolved";
  const isStaff = role === "dept_admin" || role === "admin";
  const isOfficer = role === "officer";
  const assignableStatuses = new Set(["routed_to_department", "ai_processed", "verified"]);
  const canAssignOfficer =
    isStaff &&
    !complaint.assigned_officer_id &&
    assignableStatuses.has(complaint.status) &&
    !!complaint.department_id &&
    (role === "admin" || user?.department_id === complaint.department_id);

  return (
    <div className="max-w-3xl">
      <Link href={back} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>

      <div className="mb-6">
        <p className="text-xs text-muted-foreground">
          Reference <span className="font-medium text-foreground">{complaint.complaint_id}</span>
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{complaint.title}</h1>
        <div className="mt-3">
          <ComplaintMeta complaint={complaint} />
        </div>
      </div>

      <div className="space-y-4">
        {role === "citizen" && (
          <DetailSection title="Tracking">
            <ComplaintProgressTracker status={complaint.status} />
            {complaint.status === "submitted" && (
              <p className="text-sm text-muted-foreground mt-3">
                Submitted — your report is being reviewed and will be sent to the right department shortly.
              </p>
            )}
            {complaint.status === "ai_processing" && (
              <p className="text-sm text-muted-foreground mt-3">
                Reviewing details and routing to the appropriate department…
              </p>
            )}
            {unsupportedDepartment && unsupportedMessage && (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
                {unsupportedMessage}
              </div>
            )}
          </DetailSection>
        )}

        <DetailSection title="Description">
          <p className="text-sm leading-relaxed">{complaint.description}</p>
        </DetailSection>

        {(isStaff || isOfficer) && (complaint.citizen_name || complaint.citizen_email || complaint.citizen_phone) && (
          <DetailSection title="Reporter">
            <ul className="text-sm space-y-2">
              {complaint.citizen_name && (
                <li className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="font-medium">{complaint.citizen_name}</span>
                </li>
              )}
              {complaint.citizen_email && (
                <li className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
                  <a href={`mailto:${complaint.citizen_email}`} className="text-primary hover:underline break-all">
                    {complaint.citizen_email}
                  </a>
                </li>
              )}
              {complaint.citizen_phone && (
                <li className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
                  <a href={`tel:${complaint.citizen_phone}`} className="text-primary hover:underline">
                    {complaint.citizen_phone}
                  </a>
                </li>
              )}
            </ul>
          </DetailSection>
        )}

        {role === "citizen" && !unsupportedDepartment && (complaint.department_name || complaint.assigned_officer_name) && (
          <DetailSection title={complaint.assigned_officer_name ? "Assigned officer" : "Department"}>
            {complaint.department_name && (
              <p className="text-sm text-muted-foreground mb-3">
                Department: <span className="font-medium text-foreground">{complaint.department_name}</span>
              </p>
            )}
            {complaint.assigned_officer_name ? (
              <ul className="text-sm space-y-2">
                <li className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="font-medium">{complaint.assigned_officer_name}</span>
                </li>
                {complaint.assigned_officer_email && (
                  <li className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
                    <a href={`mailto:${complaint.assigned_officer_email}`} className="text-primary hover:underline break-all">
                      {complaint.assigned_officer_email}
                    </a>
                  </li>
                )}
                {complaint.assigned_officer_phone && (
                  <li className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
                    <a href={`tel:${complaint.assigned_officer_phone}`} className="text-primary hover:underline">
                      {complaint.assigned_officer_phone}
                    </a>
                  </li>
                )}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                A field officer will be assigned soon. You will see their contact details here.
              </p>
            )}
          </DetailSection>
        )}

        {isOfficer && (
          <DetailSection title="Your case">
            <ul className="text-sm space-y-1">
              <li>
                Department: <strong>{complaint.department_name}</strong>
              </li>
              <li>
                Priority: <strong className="capitalize">{complaint.priority}</strong>
              </li>
            </ul>
          </DetailSection>
        )}

        {isStaff && (canAssignOfficer || complaint.assigned_officer_id) && (
          <AssignOfficerPanel complaint={complaint} departmentId={complaint.department_id} />
        )}

        <DetailSection title="Location">
          <div className="flex items-start gap-2 text-sm">
            <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
            <p>{complaint.location?.address}</p>
          </div>
        </DetailSection>

        {complaint.images?.length > 0 && (
          <DetailSection title="Photos">
            <div className="flex gap-3 flex-wrap">
              {complaint.images.map((img: { url: string }, i: number) => (
                <img
                  key={i}
                  src={img.url}
                  alt={`Evidence ${i + 1}`}
                  className="h-28 w-28 rounded-lg object-cover border"
                />
              ))}
            </div>
          </DetailSection>
        )}

        {isOfficer && complaint.assigned_officer_id === user?.id && (
          <OfficerActions complaint={complaint} role={role} />
        )}

        {showFeedback && <FeedbackForm complaintId={complaint.id} />}

        <DetailSection title="Timeline">
          <ComplaintTimeline history={complaint.status_history} showNotes />
        </DetailSection>
      </div>
    </div>
  );
}
