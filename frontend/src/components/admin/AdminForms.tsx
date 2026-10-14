"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, X } from "lucide-react";

export function CreateDepartmentForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", code: "", description: "" });
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () =>
      adminApi.createDepartment({
        ...form,
        keywords: [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-departments"] });
      onClose();
    },
    onError: () => setError("Failed to create department"),
  });

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Add Department</h3>
        <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
        className="grid sm:grid-cols-2 gap-4"
      >
        <div className="space-y-2">
          <Label>Department Name</Label>
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div className="space-y-2">
          <Label>Code</Label>
          <Input
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
            required
            maxLength={10}
            placeholder="PWD"
          />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label>Description</Label>
          <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating..." : "Create Department"}
          </Button>
        </div>
      </form>
    </div>
  );
}

export function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button onClick={onClick} className="gap-2" size="sm">
      <Plus className="h-4 w-4" /> {label}
    </Button>
  );
}

export function roleLabel(role: string): string {
  const map: Record<string, string> = {
    admin: "System admin",
    dept_admin: "Department admin",
    officer: "Officer",
    citizen: "Citizen",
  };
  return map[role] || role;
}
