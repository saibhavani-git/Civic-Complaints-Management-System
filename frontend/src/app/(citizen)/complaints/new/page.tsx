"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { complaintsApi } from "@/lib/api";
import { complaintsListKey } from "@/lib/complaintQueries";
import { useAuth } from "@/hooks/useAuth";
import type { Complaint } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import axios from "axios";
import { MapPin, Upload, Loader2 } from "lucide-react";

function submitErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.response?.status === 401) {
      return "Please log in again as a citizen to submit complaints.";
    }
    if (err.response?.status === 403) {
      return "Only citizen accounts can submit complaints.";
    }
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ");
    }
    if (!err.response) {
      const api =
        process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1\/?$/, "") || "http://localhost:8002";
      return `Cannot reach the API at ${api}. Start the backend and restart npm run dev.`;
    }
  }
  return "Failed to submit complaint. Please check your details and try again.";
}

export default function NewComplaintPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    description: "",
    address: "",
    latitude: 28.6139,
    longitude: 77.2090,
  });
  const [images, setImages] = useState<FileList | null>(null);

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setForm({ ...form, latitude: pos.coords.latitude, longitude: pos.coords.longitude });
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("title", form.title);
      fd.append("description", form.description);
      fd.append("latitude", String(form.latitude));
      fd.append("longitude", String(form.longitude));
      fd.append("address", form.address);
      if (images) Array.from(images).forEach((file) => fd.append("images", file));
      const { data } = await complaintsApi.create(fd);
      const created = data as Complaint;
      const listKey = complaintsListKey(user?.id, "citizen");
      queryClient.setQueryData(
        listKey,
        (old: { items: Complaint[]; total: number; page: number; limit: number; pages: number } | undefined) => {
          if (!old) {
            return { items: [created], total: 1, page: 1, limit: 100, pages: 1 };
          }
          const items = [created, ...old.items.filter((c) => c.id !== created.id)];
          return { ...old, items, total: Math.max(old.total, items.length) };
        }
      );
      queryClient.invalidateQueries({ queryKey: listKey });
      router.push("/dashboard?submitted=1");
    } catch (err) {
      setError(submitErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <PageHeader
        backHref="/dashboard"
        backLabel="Back to dashboard"
        title="Report an Issue"
        description="Describe the civic problem with as much detail as possible"
      />

      <form onSubmit={handleSubmit} className="w-full space-y-6 rounded-xl border bg-card p-4 sm:p-6 shadow-sm">
        <div className="space-y-2">
          <Label htmlFor="title">Issue title</Label>
          <Input
            id="title"
            placeholder="e.g. Broken streetlight on Main Road"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
            minLength={5}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <textarea
            id="description"
            className="flex min-h-[140px] w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Describe the issue — when it started, severity, impact on residents..."
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
            minLength={20}
          />
          <p className="text-xs text-muted-foreground">{form.description.length}/5000 characters (min 20)</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Location / Address</Label>
          <Input
            id="address"
            placeholder="Street, area, city"
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
            required
            minLength={5}
          />
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={getLocation} className="gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              Use my GPS coordinates
            </Button>
            <span className="text-xs text-muted-foreground">Location captured for routing</span>
          </div>
        </div>

        <div className="space-y-2">
          <Label>
            Photos <span className="font-normal text-muted-foreground">(optional, max 5)</span>
          </Label>
          <label className="flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-input bg-muted/30 px-6 py-8 hover:bg-muted/50 transition-colors">
            <Upload className="h-8 w-8 text-muted-foreground mb-2" />
            <span className="text-sm font-medium">Click to upload images</span>
            <span className="text-xs text-muted-foreground mt-1">PNG, JPG up to 5MB each</span>
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => setImages(e.target.files)}
            />
          </label>
          {images && images.length > 0 && (
            <p className="text-xs text-muted-foreground">{images.length} file(s) selected</p>
          )}
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end pt-2">
          <Button type="button" variant="outline" onClick={() => router.push("/dashboard")}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading} className="sm:min-w-[160px]">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting…
              </>
            ) : (
              "Submit complaint"
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
