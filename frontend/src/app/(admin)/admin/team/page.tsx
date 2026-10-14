"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { staffApi } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { AddButton } from "@/components/admin/AdminForms";
import { PersonTable } from "@/components/admin/people/PersonTable";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { validatePhoneInput } from "@/lib/phone";
import Link from "next/link";
import { Loader2, X } from "lucide-react";
import type { StaffRow } from "@/components/admin/people/types";

function AddTeamMemberForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", phone: "", service_area: "" });
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () => staffApi.addWorker(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dept-team"] });
      onClose();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not add team member");
    },
  });

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">New field officer</h3>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="text-xs text-muted-foreground mb-4">
        They will log in with the same page as other staff and see assigned cases under My cases.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const phoneErr = validatePhoneInput(form.phone);
          if (phoneErr) {
            setError(phoneErr);
            return;
          }
          if (!form.service_area.trim()) {
            setError("Field area is required");
            return;
          }
          create.mutate();
        }}
        className="grid sm:grid-cols-2 gap-4"
      >
        <div className="space-y-2">
          <Label>Full name</Label>
          <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </div>
        <div className="space-y-2">
          <Label>Email</Label>
          <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </div>
        <div className="space-y-2">
          <Label>Phone</Label>
          <Input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
        </div>
        <div className="space-y-2">
          <Label>Password</Label>
          <Input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={8}
          />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label>Field area</Label>
          <Input
            placeholder="e.g. North zone, Wards 12–18"
            value={form.service_area}
            onChange={(e) => setForm({ ...form, service_area: e.target.value })}
            required
            minLength={2}
          />
          <p className="text-[11px] text-muted-foreground">Required — shown when assigning complaints to this officer.</p>
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Saving…" : "Add to team"}
          </Button>
        </div>
      </form>
    </div>
  );
}

export default function DeptTeamPage() {
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const { data: team = [], isLoading } = useQuery({
    queryKey: ["dept-team"],
    queryFn: () => staffApi.listTeam().then((r) => r.data),
    enabled: user?.role === "dept_admin",
  });

  const rows: StaffRow[] = team.map(
    (w: {
      id: string;
      full_name: string;
      email: string;
      phone?: string;
      service_area?: string;
      active_assigned_count?: number;
    }) => ({
      id: w.id,
      full_name: w.full_name,
      email: w.email,
      phone: w.phone,
      service_area: w.service_area,
      role: "officer",
      is_active: true,
      active_assigned_count: w.active_assigned_count ?? 0,
    })
  );

  if (user?.role !== "dept_admin") {
    return (
      <div className="py-16 text-center">
        <p className="text-muted-foreground">Department heads manage their field team here.</p>
        <Link href="/admin/dashboard" className="text-sm text-primary hover:underline mt-4 inline-block">
          Back to overview
        </Link>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Field team"
        description={`${rows.length} officer${rows.length === 1 ? "" : "s"} in your department`}
        action={<AddButton label="Add officer" onClick={() => setShowForm(true)} />}
      />
      {showForm ? (
        <AddTeamMemberForm onClose={() => setShowForm(false)} />
      ) : isLoading ? (
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-x-auto">
          <PersonTable
            rows={rows}
            showStatus={false}
            showFieldArea
            showWorkload
            emptyMessage="No officers yet. Add someone to assign complaints."
          />
        </div>
      )}
    </div>
  );
}
