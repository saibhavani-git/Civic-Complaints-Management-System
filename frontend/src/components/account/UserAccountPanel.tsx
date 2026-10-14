"use client";

import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { authApi } from "@/lib/api";
import { roleLabel } from "@/lib/roles";
import { validatePhoneInput } from "@/lib/phone";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Phone, Shield, User, Loader2, Building2, MapPin, CheckCircle2 } from "lucide-react";
import { normalizeRole } from "@/lib/roles";
import { fieldAreaTextClassName, officerServiceAreaLabel, userDepartmentLabel } from "@/lib/staffDisplay";
import { cn } from "@/lib/utils";

export function UserAccountPanel({ variant = "fullscreen" }: { variant?: "default" | "fullscreen" }) {
  const { user, loading, refreshUser } = useAuth();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setPhone(user.phone ?? "");
    }
  }, [user]);

  const save = useMutation({
    mutationFn: () => authApi.updateProfile({ full_name: fullName, phone }),
    onSuccess: async () => {
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not save profile");
    },
  });

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground gap-2">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading account…
      </div>
    );
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const phoneErr = validatePhoneInput(phone);
    if (phoneErr) {
      setError(phoneErr);
      return;
    }
    if (fullName.trim().length < 2) {
      setError("Full name is required");
      return;
    }
    save.mutate();
  };

  const role = normalizeRole(user.role);
  const deptLabel = userDepartmentLabel(user);
  const fieldArea = officerServiceAreaLabel(user);

  const details = [
    { icon: User, label: "Full name", value: user.full_name },
    { icon: Shield, label: "Account type", value: roleLabel(user.role) },
    ...(deptLabel ? [{ icon: Building2, label: "Department", value: deptLabel }] : []),
    ...(fieldArea ? [{ icon: MapPin, label: "Field area", value: fieldArea }] : []),
    { icon: Mail, label: "Email", value: user.email },
    { icon: Phone, label: "Phone on file", value: user.phone || "Not set" },
    ...(role === "admin" ? [{ icon: Shield, label: "Portal", value: roleLabel(user.role) }] : []),
  ];

  const editHint =
    role === "citizen"
      ? "We use these details when we follow up on your complaints."
      : "Shown to colleagues and citizens on assigned work.";

  const dirty =
    fullName.trim() !== (user.full_name ?? "").trim() ||
    phone.trim() !== (user.phone ?? "").trim();

  const resetForm = () => {
    setFullName(user.full_name);
    setPhone(user.phone ?? "");
    setError("");
  };

  const inputClass =
    "h-11 bg-background shadow-none [&:-webkit-autofill]:[-webkit-text-fill-color:hsl(var(--foreground))] [&:-webkit-autofill]:shadow-[inset_0_0_0_1000px_hsl(var(--background))]";

  const editForm = (
    <form
      onSubmit={handleSave}
      className="rounded-xl border bg-card shadow-sm flex flex-col min-h-0 lg:min-h-full"
    >
      <div className="border-b px-5 py-4">
        <h2 className="text-sm font-semibold">Edit profile</h2>
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{editHint}</p>
      </div>

      <div className="p-5 space-y-5 flex-1">
        <div className="space-y-1.5">
          <Label htmlFor="full_name" className="text-xs font-medium text-muted-foreground">
            Full name
          </Label>
          <Input
            id="full_name"
            autoComplete="name"
            className={inputClass}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            minLength={2}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="phone" className="text-xs font-medium text-muted-foreground">
            Phone number
          </Label>
          <Input
            id="phone"
            type="tel"
            autoComplete="tel"
            inputMode="tel"
            placeholder="+91 9876543210"
            className={inputClass}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
          <p className="text-[11px] text-muted-foreground pt-0.5">Include country code, e.g. +91</p>
        </div>

        {error && (
          <p className="text-sm text-red-600 rounded-lg border border-red-200 bg-red-50 px-3 py-2">{error}</p>
        )}
        {saved && (
          <p className="text-sm text-emerald-800 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            Profile saved
          </p>
        )}
      </div>

      <div className="border-t px-5 py-4 flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-2 bg-muted/30">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-muted-foreground sm:mr-auto"
          disabled={!dirty || save.isPending}
          onClick={resetForm}
        >
          Reset
        </Button>
        <Button type="submit" size="sm" disabled={save.isPending || !dirty}>
          {save.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" /> Saving…
            </>
          ) : (
            "Save changes"
          )}
        </Button>
      </div>
    </form>
  );

  const detailsCard = (
    <div className="rounded-xl border bg-card shadow-sm text-sm h-full">
      <div className="border-b px-5 py-4">
        <h2 className="text-sm font-semibold">Account details</h2>
      </div>
      <div className="divide-y">
        {details.map(({ icon: Icon, label, value }) => {
          const isFieldArea = label === "Field area";
          return (
            <div
              key={label}
              className={cn(
                "flex gap-3 px-5 py-3.5",
                isFieldArea ? "items-start" : "items-center"
              )}
            >
              <Icon className={cn("h-4 w-4 text-muted-foreground shrink-0", isFieldArea && "mt-0.5")} />
              <span className={cn("text-muted-foreground w-28 shrink-0", isFieldArea && "pt-0.5")}>{label}</span>
              <span
                className={cn(
                  "font-medium min-w-0 flex-1",
                  isFieldArea ? fieldAreaTextClassName : "truncate"
                )}
              >
                {value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );

  if (variant === "fullscreen") {
    return (
      <div className="flex flex-col min-h-[calc(100dvh-3.5rem)] w-full -mx-4 sm:-mx-6 md:-my-6 px-4 sm:px-6 lg:px-10 py-6 pb-28 md:pb-10">
        <div className="max-w-5xl mx-auto w-full grid lg:grid-cols-2 gap-6 lg:gap-8 items-start">
          {detailsCard}
          {editForm}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      {detailsCard}
      {editForm}
    </div>
  );
}
