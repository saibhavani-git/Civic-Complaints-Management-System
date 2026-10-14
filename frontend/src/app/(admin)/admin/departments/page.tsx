"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { CreateDepartmentForm, AddButton } from "@/components/admin/AdminForms";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { Loader2 } from "lucide-react";

export default function AdminDepartmentsPage() {
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const { data: departments = [], isLoading } = useQuery({
    queryKey: ["admin-departments"],
    queryFn: () => adminApi.listDepartments().then((r) => r.data),
  });

  if (user?.role !== "admin") {
    return (
      <div className="py-16 text-center">
        <p className="text-muted-foreground">Only system administrators can manage departments.</p>
        <Link href="/admin/dashboard" className="text-sm text-primary hover:underline mt-4 inline-block">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Departments"
        description="Government departments that receive citizen reports"
        action={<AddButton label="Add Department" onClick={() => setShowForm(true)} />}
      />

      {showForm ? (
        <CreateDepartmentForm onClose={() => setShowForm(false)} />
      ) : isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground py-12">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading...
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {departments.map((d: { id: string; name: string; code: string; description?: string }) => (
            <div key={d.id} className="rounded-xl border bg-card p-5 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold">{d.name}</h3>
                <span className="shrink-0 rounded-md bg-primary/10 px-2 py-0.5 text-xs font-mono font-medium text-primary">{d.code}</span>
              </div>
              {d.description && <p className="mt-2 text-sm text-muted-foreground">{d.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
