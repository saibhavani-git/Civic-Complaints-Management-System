"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { validatePhoneInput } from "@/lib/phone";
import { X } from "lucide-react";
import type { UserRole } from "@/types";

const COPY: Record<string, { title: string; submit: string; hint: string }> = {
  admin: {
    title: "New system administrator",
    submit: "Create administrator",
    hint: "Full access to departments, staff, and platform settings.",
  },
  dept_admin: {
    title: "New department head",
    submit: "Create department head",
    hint: "Manages one department’s complaints and field team.",
  },
  officer: {
    title: "New field officer",
    submit: "Create officer",
    hint: "Resolves complaints assigned by their department head.",
  },
};

export function CreateStaffForm({
  role,
  onClose,
}: {
  role: Extract<UserRole, "admin" | "dept_admin" | "officer">;
  onClose: () => void;
}) {
  const copy = COPY[role];
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    phone: "",
    department_id: "",
    service_area: "",
  });
  const [error, setError] = useState("");

  const needsDepartment = role === "officer" || role === "dept_admin";
  const needsFieldArea = role === "officer";

  const { data: departments = [] } = useQuery({
    queryKey: ["admin-departments"],
    queryFn: () => adminApi.listDepartments().then((r) => r.data),
    enabled: needsDepartment,
  });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createUser({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        role,
        phone: form.phone.trim(),
        department_id: needsDepartment ? form.department_id : undefined,
        service_area: needsFieldArea ? form.service_area.trim() : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      onClose();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not save. Try again.");
    },
  });

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">{copy.title}</h3>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="text-xs text-muted-foreground mb-4">{copy.hint}</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (needsDepartment && !form.department_id) {
            setError("Select a department");
            return;
          }
          const phoneErr = validatePhoneInput(form.phone);
          if (phoneErr) {
            setError(phoneErr);
            return;
          }
          if (needsFieldArea && form.service_area.trim().length < 2) {
            setError("Field area is required for officers");
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
        {needsDepartment && (
          <div className="space-y-2 sm:col-span-2">
            <Label>Department</Label>
            <select
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: e.target.value })}
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"
              required
            >
              <option value="">Select department…</option>
              {departments.map((d: { id: string; name: string; code: string }) => (
                <option key={d.id} value={d.id}>
                  {d.code} — {d.name}
                </option>
              ))}
            </select>
          </div>
        )}
        {needsFieldArea && (
          <div className="space-y-2 sm:col-span-2">
            <Label>Field area</Label>
            <Input
              placeholder="e.g. North zone, Wards 12–18"
              value={form.service_area}
              onChange={(e) => setForm({ ...form, service_area: e.target.value })}
              required
              minLength={2}
            />
          </div>
        )}
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Saving…" : copy.submit}
          </Button>
        </div>
      </form>
    </div>
  );
}
