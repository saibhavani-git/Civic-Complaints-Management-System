"use client";



import { Suspense, useMemo, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import Link from "next/link";

import { useRouter, useSearchParams } from "next/navigation";

import { complaintsApi } from "@/lib/api";

import { complaintsListKey } from "@/lib/complaintQueries";

import { useAuth } from "@/hooks/useAuth";

import { ComplaintCard } from "@/components/complaints/ComplaintCard";
import { ComplaintFilters } from "@/components/complaints/ComplaintShared";
import { citizenGroupMatches } from "@/lib/complaintFilters";

import { PageHeader, StatCard, EmptyState } from "@/components/layout/PageHeader";

import { Button } from "@/components/ui/button";

import { PlusCircle, FileText, Clock, CheckCircle, Loader2, X } from "lucide-react";

import type { Complaint } from "@/types";
import { complaintsLoadErrorMessage } from "@/lib/complaintListError";



function DashboardContent() {

  const { user } = useAuth();

  const router = useRouter();

  const searchParams = useSearchParams();

  const showSubmittedBanner = searchParams.get("submitted") === "1";
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading, isError, error } = useQuery({

    queryKey: complaintsListKey(user?.id, "citizen"),

    queryFn: () => complaintsApi.list({ limit: 100 }).then((r) => r.data),

    enabled: !!user?.id,

  });



  const allComplaints: Complaint[] = useMemo(() => {
    const items = data?.items ?? [];
    return [...items].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [data?.items]);

  const complaints = useMemo(
    () => allComplaints.filter((c) => citizenGroupMatches(c.status, statusFilter)),
    [allComplaints, statusFilter]
  );



  const stats = {

    total: data?.total || 0,

    pending: allComplaints.filter((c) =>
      ["submitted", "ai_processing", "routed_to_department", "ai_processed", "pending"].includes(c.status)
    ).length,

    inProgress: allComplaints.filter((c) =>
      ["assigned", "work_started", "in_progress"].includes(c.status)
    ).length,

    resolved: allComplaints.filter((c) => ["resolved", "closed"].includes(c.status)).length,

  };



  return (

    <div>

      <PageHeader

        title="My Complaints"

        description="All your reports — newest first. Status updates as your case moves through the municipality."

        action={

          <Link href="/complaints/new">

            <Button className="gap-2">

              <PlusCircle className="h-4 w-4" /> New Complaint

            </Button>

          </Link>

        }

      />



      {showSubmittedBanner && (

        <div className="mb-6 flex items-start justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">

          <p>

            <strong>Submitted.</strong> Your complaint is on the list below. You will get bell notifications as

            tracking steps change.

          </p>

          <button

            type="button"

            aria-label="Dismiss"

            className="shrink-0 text-emerald-700 hover:text-emerald-900"

            onClick={() => router.replace("/dashboard")}

          >

            <X className="h-4 w-4" />

          </button>

        </div>

      )}



      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">

        <StatCard label="Total" value={stats.total} icon={FileText} />

        <StatCard label="Pending" value={stats.pending} icon={Clock} iconClassName="bg-amber-50 [&>svg]:text-amber-600" />

        <StatCard label="In Progress" value={stats.inProgress} icon={Clock} iconClassName="bg-orange-50 [&>svg]:text-orange-600" />

        <StatCard label="Resolved" value={stats.resolved} icon={CheckCircle} iconClassName="bg-emerald-50 [&>svg]:text-emerald-600" />

      </div>

      {allComplaints.length > 0 && (
        <div className="mb-6">
          <ComplaintFilters
            filterRole="citizen"
            status={statusFilter}
            priority=""
            onStatusChange={setStatusFilter}
            onPriorityChange={() => {}}
          />
        </div>
      )}

      {isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 mb-6">
          {complaintsLoadErrorMessage(error)}
        </div>
      ) : null}

      {isLoading ? (

        <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">

          <Loader2 className="h-5 w-5 animate-spin" /> Loading your complaints...

        </div>

      ) : isError ? null : allComplaints.length === 0 ? (

        <EmptyState

          icon={FileText}

          title="No complaints yet"

          description="Report your first civic issue — broken roads, streetlights, garbage, water supply, and more."

          action={

            <Link href="/complaints/new">

              <Button className="gap-2">

                <PlusCircle className="h-4 w-4" /> Submit Complaint

              </Button>

            </Link>

          }

        />

      ) : complaints.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No matches"
          description="Try a different status filter or view all complaints."
          action={
            <Button type="button" variant="outline" onClick={() => setStatusFilter("")}>
              Clear filter
            </Button>
          }
        />
      ) : (

        <div>

          <h2 className="text-sm font-medium text-muted-foreground mb-4">

            {complaints.length} complaint{complaints.length !== 1 ? "s" : ""}

            <span className="ml-2 text-muted-foreground">· newest first</span>

          </h2>

          <div className="grid gap-4 md:grid-cols-2">

            {complaints.map((c) => (

              <ComplaintCard key={c.id} complaint={c} href={`/complaints/${c.id}`} />

            ))}

          </div>

        </div>

      )}

    </div>

  );

}



export default function CitizenDashboard() {

  return (

    <Suspense

      fallback={

        <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">

          <Loader2 className="h-5 w-5 animate-spin" /> Loading...

        </div>

      }

    >

      <DashboardContent />

    </Suspense>

  );

}


