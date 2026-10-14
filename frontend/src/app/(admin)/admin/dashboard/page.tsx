"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { DashboardCharts } from "@/components/analytics/DashboardCharts";
import { PageHeader, StatCard } from "@/components/layout/PageHeader";
import { useAuth } from "@/hooks/useAuth";
import { normalizeRole } from "@/lib/roles";
import Link from "next/link";
import { BarChart3, Clock, CheckCircle, AlertTriangle, Loader2, ClipboardList } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AdminDashboard() {
  const { user } = useAuth();
  const role = normalizeRole(user?.role);
  const isSystemAdmin = role === "admin";

  const { data: overview, isLoading } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
  });

  const { data: deptData } = useQuery({
    queryKey: ["analytics-dept"],
    queryFn: () => analyticsApi.byDepartment().then((r) => r.data),
    enabled: isSystemAdmin,
  });

  const { data: trends } = useQuery({
    queryKey: ["analytics-trends"],
    queryFn: () => analyticsApi.trends().then((r) => r.data),
  });

  if (isLoading || !overview) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading…
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Overview"
        description={
          isSystemAdmin
            ? "City-wide complaint volume and performance"
            : "Your department’s open workload and resolution progress"
        }
      />

      {isSystemAdmin && (
        <div className="mb-6">
          <Link href="/admin/complaints">
            <Button variant="outline" className="gap-2">
              <ClipboardList className="h-4 w-4" />
              View all complaints ({overview.total_complaints})
            </Button>
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total" value={overview.total_complaints} icon={BarChart3} />
        <StatCard label="Pending" value={overview.pending} icon={AlertTriangle} iconClassName="bg-amber-50 [&>svg]:text-amber-600" />
        <StatCard label="In progress" value={overview.in_progress} icon={Clock} iconClassName="bg-orange-50 [&>svg]:text-orange-600" />
        <StatCard label="Resolved" value={`${overview.resolution_rate}%`} icon={CheckCircle} iconClassName="bg-emerald-50 [&>svg]:text-emerald-600" />
      </div>

      <DashboardCharts
        overview={overview}
        departmentData={isSystemAdmin ? deptData : undefined}
        trendData={trends}
      />
    </div>
  );
}
